# Plan: `clickup tasks status <id> <status>`

## Goal

Add a command that changes a task's status. Before writing anything, it checks the requested status against the statuses of the task's own list. If the status is not valid, the command fails and prints the list's valid statuses.

### Agreed behavior

| Case | Behavior | Exit |
|---|---|---|
| Valid status, different from current | PUT the change, print `HGAI-1217: open -> in progress` | 0 |
| Valid status, same as current | Print `HGAI-1217 is already "in progress"`, no write | 0 |
| Unknown status | Error naming the list, then the valid statuses in list order | 1 |
| Matching | Exact match ignoring case (`In Progress` == `in progress`); surrounding whitespace trimmed; the list's own spelling is sent to ClickUp | - |
| IDs | Custom (`HGAI-1217`) and native (`86a3xyzw`) IDs, same as `clickup tasks <id>` | - |

Example of the error:

```
$ clickup tasks status HGAI-1217 done
Error: invalid status "done" for list "Sprint 12"
Valid statuses:
  to do
  in progress
  review
  complete
```

## Current state (verified in the code)

- `tasksCmd` (`internal/commands/tasks.go:24`) takes an optional `[task_id]` with `cobra.MaximumNArgs(1)`. Cobra resolves child command names before positional args, so a `status` subcommand coexists with `clickup tasks <id>`. Its local `--status/-s` filter flag is not inherited by the subcommand, so there is no flag clash.
- `Client.doRequest` (`internal/api/client.go:42`) always sends a `nil` body and only `Get` exists. A status change needs `PUT /task/{id}` with a JSON body.
- Debug output in `doRequest` is printed to stdout, so it mixes into command output (including `-o json`).
- The custom ID query (`custom_task_ids=true` + `team_id`) is duplicated in `GetTask` (`internal/api/tasks.go:67`) and `GetTaskComments` (`internal/api/comments.go:17`).
- `models.Task.List` (`pkg/models/task.go:26`) gives the home list ID. `models.Status` already exists and fits the list status shape.
- There are no tests in `internal/api` or `internal/commands`.

## Flow

```
clickup tasks status HGAI-1217 "In Progress"
  1. GET /task/HGAI-1217?custom_task_ids=true&team_id=W   -> task (current status, list.id)
  2. GET /list/{list.id}                                   -> list name + effective statuses
  3. list.FindStatus("In Progress")
       list has no statuses -> error, exit 1
       not found          -> error with valid statuses, exit 1
       == current status  -> notice, exit 0
  4. PUT /task/HGAI-1217?custom_task_ids=true&team_id=W  {"status":"in progress"}
  5. print "HGAI-1217: open -> in progress"
```

`GET /list/{id}` returns the list's effective statuses, including ones inherited from the folder or space. Tasks that live in multiple lists are validated against their home list, which is the list ClickUp takes statuses from.

## Design

### 1. API client: request bodies (`internal/api/client.go`)

- `doRequest(method, path string, query url.Values, payload any)`: if `payload` is non-nil, marshal it to JSON, send it as the body and set `Content-Type: application/json` (only then).
- Add `Put(path string, query url.Values, payload any) ([]byte, error)`. `Get` passes `nil`.
- Debug lines go to stderr instead of stdout (targeted fix while we are in this function).

### 2. Shared custom ID query (`internal/api/tasks.go`)

- Extract `taskIDQuery(taskID, teamID string) url.Values` returning the `custom_task_ids`/`team_id` pair when the ID is custom.
- Use it in `GetTask`, `GetTaskComments` and the new `UpdateTaskStatus`.

### 3. List model (`pkg/models/list.go`, new)

```go
type List struct {
    ID       string   `json:"id"`
    Name     string   `json:"name"`
    Statuses []Status `json:"statuses"`
}

// FindStatus matches name case-insensitively, ignoring surrounding whitespace.
func (l *List) FindStatus(name string) (Status, bool)

// StatusNames returns status names ordered by Orderindex.
func (l *List) StatusNames() []string
```

Matching lives on the model so it is a pure function, testable without HTTP.

### 4. API methods

- `internal/api/lists.go` (new): `GetList(listID string) (*models.List, error)` -> `GET /list/{id}`.
- `internal/api/tasks.go`: `UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)` -> `PUT /task/{id}` with `{"status": status}` and `taskIDQuery`. Returns the updated task from the response.

### 5. Command (`internal/commands/tasks_status.go`, new)

- `tasksStatusCmd`: `Use: "status <task_id> <status>"`, registered with `tasksCmd.AddCommand` in its own `init()`.
- Custom `Args` validator: exactly 2 args. With more than 2 it says `status names with spaces must be quoted, e.g. clickup tasks status HGAI-1217 "in progress"` instead of Cobra's generic `accepts 2 arg(s), received 3`.
- `RunE` is a thin wrapper around a testable core:

```go
type statusUpdater interface {
    GetTask(taskID, teamID string) (*models.Task, error)
    GetList(listID string) (*models.List, error)
    UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)
}

func setTaskStatus(w io.Writer, client statusUpdater, teamID, taskID, name string) error
```

  `*api.Client` satisfies the interface; tests pass a fake. The core runs steps 1-5 of the flow above. Errors are wrapped like the rest of the file (`failed to get task: %w`, `failed to get list: %w`, `failed to update task: %w`). The invalid status error is a multi-line message, so `Execute` prints it as `Error: ...` on stderr and exits 1.
- The confirmation uses `task.GetDisplayID()`, so it shows the custom ID when there is one.
- Plain text output only. No `-o json` for this command (nothing has asked for it yet).

### 6. Docs and skill

- `tasksCmd.Long` examples and `rootCmd.Long` "Get started" list: add `clickup tasks status <ID> <status>`.
- `README.md`: usage section.
- `skills/SKILL.md`: add the command, add "change status" trigger phrases to the description, and a rule that the agent only changes a status when the user explicitly asks.
- `make build-all` to refresh the pre-built binaries in `bin/`.

## Testing (TDD, tests first per unit)

| Layer | File | Cases |
|---|---|---|
| Model | `pkg/models/list_test.go` | case-insensitive match returns list spelling; whitespace trimmed; unknown -> false; `StatusNames` sorted by orderindex |
| API | `internal/api/client_test.go` (httptest, sets `baseURL`) | `Put` sends method, JSON body and Content-Type; `Get` sends no body; debug writes to stderr |
| API | `internal/api/tasks_test.go`, `lists_test.go` | `UpdateTaskStatus` body + custom ID query vs native ID; `GetList` decodes name and statuses; `GetTask` still sends custom ID query after refactor |
| Command | `internal/commands/tasks_status_test.go` (fake `statusUpdater`) | success sends canonical casing and prints `ID: old -> new`; invalid status error lists names in order and no update is called; already-in-status prints notice, no update, nil error; list with no statuses -> `list "X" has no statuses`; GetTask/GetList/Update errors are wrapped; Args validator hint for 3+ args |

End-to-end, against a real workspace with a throwaway task (`make build`, then `bin/clickup ...`):

1. `tasks status <custom-id> "in progress"` -> confirmation; `clickup tasks <id>` shows the new status.
2. Same with a native ID.
3. Different casing (`"IN PROGRESS"`) -> works, ClickUp shows the list spelling.
4. Same status again -> notice, exit 0.
5. `tasks status <id> nonsense` -> valid statuses listed, exit 1, task unchanged.
6. Task in a list that inherits statuses from its space -> valid set matches the ClickUp UI.
7. Unquoted multi-word status -> quoting hint.
8. `--debug` output appears on stderr only.

Finish with `make check`.

## Commits

1. `api`: request bodies + `Put`, debug to stderr, `taskIDQuery` extraction (with tests)
2. `models`: `List`, `FindStatus`, `StatusNames` (with tests)
3. `api`: `GetList`, `UpdateTaskStatus` (with tests)
4. `commands`: `tasks status` (with tests)
5. docs: help text, README, skill
6. rebuilt binaries

## Risks and edge cases

- **Statuses change between check and PUT**: ClickUp rejects the PUT with a 400; we surface it as `failed to update task: API error (status 400): ...`. No retry needed.
- **Inherited statuses**: relies on `GET /list/{id}` returning effective statuses. Verified in E2E step 6; if it ever returns an empty set we would wrongly reject everything, so an empty `Statuses` slice returns a clear error (`list "X" has no statuses`) rather than "invalid status".
- **Subcommand name shadowing**: a task whose ID is literally `status` can no longer be viewed via `clickup tasks status`. No real ClickUp ID looks like that.
- **Cost**: three API calls per change (task, list, update). Acceptable for an interactive command.
- **Backwards compatibility**: purely additive. The `doRequest` signature change is internal to `api`. Debug output moving to stderr only affects people piping `--debug` output, which was already broken for JSON.
