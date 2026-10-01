# Plan: `clickup tasks status <id> <status>`

Path: bounded. New subcommand on the existing `tasks` command, plus write support in the API client.

## Goal

Change a task's status from the terminal in one command. The status is validated against the statuses of the task's own list. An invalid status changes nothing, exits 1, and prints the valid statuses.

## Agreed decisions

- **Matching:** case-insensitive, otherwise exact (`strings.EqualFold`). The list's own spelling is sent to the API.
- **Success output:** one line by default, `HGAI-1217: to do -> in progress`. With `--output json`, the updated task (the PUT response) is printed as JSON.
- **Already in that status:** the notice `HGAI-1217 is already "in progress"` is printed, the PUT is skipped, and the command exits 0. In `--output json` mode, the notice goes to stderr and the current task JSON goes to stdout.

Status: approved 2026-10-01.

## Current state (verified)

- `tasksCmd` takes an optional `[task_id]` with `cobra.MaximumNArgs(1)` (`internal/commands/tasks.go:24-39`). Cobra resolves subcommands before positional args, so `tasks status ...` routes to the new command and `tasks HGAI-1217` keeps working. A task literally named `status` could not be viewed. That is acceptable.
- `--output` is a local flag on `tasksCmd` (`tasks.go:46`), so subcommands don't see it.
- `Client.doRequest(method, path, query)` sends no body. Only `Get` exists (`internal/api/client.go:42-96`).
- The custom-ID query logic (`custom_task_ids=true&team_id=...`) is duplicated in `GetTask` and `GetTaskComments`.
- `GetTask` returns `task.List.ID` and `task.Status.Status` (`pkg/models/task.go:16,26`).
- Debug output in `doRequest` is printed to **stdout** with `fmt.Printf`, so `--debug --output json` produces invalid JSON.
- There are no API-layer tests. `baseURL` is an unexported field, so in-package tests can point it at `httptest`.

## Flow

```
GetTask(id)                      -> task (home list ID, current status, native ID)
  current == requested (fold)?   -> print "already" notice, exit 0
GetList(task.List.ID)            -> list name + statuses (effective, incl. inherited)
  list.FindStatus(requested)     -> not found: error with valid statuses, exit 1
UpdateTaskStatus(task.ID, s.Status) -> PUT /task/{native id} {"status": "<canonical>"}
print "ID: old -> new"  |  JSON of updated task
```

The PUT uses the task's **native** ID returned by `GetTask`, so the custom-ID query is only needed on the first call.

## Error output (invalid status)

Returned from `RunE`. `Execute()` already prints `Error: ...` to stderr and exits 1:

```
Error: invalid status "done" for list "Sprint 12". Valid statuses:
  to do
  in progress
  review
  complete
```

Statuses are listed in `orderindex` order, in the list's own spelling.

## Changes by file

### `pkg/models/list.go` (new)
- `type List struct { ID, Name string; Statuses []Status }`
- `func (l *List) FindStatus(name string) (Status, bool)`: uses `strings.EqualFold` and returns the canonical `Status`.
- `func (l *List) StatusNames() []string`: names sorted by `Orderindex`, without mutating `Statuses`.

### `internal/api/client.go`
- `doRequest(method, path string, query url.Values, payload any)`: if `payload != nil`, JSON-marshal it and send it as the body.
- Add `Put(path, query, payload)`. `Get` passes `nil`.
- Write the `[DEBUG]` lines to `os.Stderr` instead of stdout.

### `internal/api/tasks.go`
- Extract `taskIDQuery(taskID, teamID string) url.Values`, and use it in `GetTask` and `GetTaskComments`.
- Add `UpdateTaskStatus(taskID, status string) (*models.Task, error)`, which calls `PUT /task/{id}` with `{"status": status}` and decodes the returned task.

### `internal/api/lists.go` (new)
- `GetList(listID string) (*models.List, error)`, which calls `GET /list/{id}`.

### `internal/commands/tasks_status.go` (new)
- `tasksStatusCmd`: `Use: "status <task_id> <status>"`, `Args: cobra.ExactArgs(2)`, registered via `tasksCmd.AddCommand` in `init()`.
- Small consumer-side interface for testability:
  ```go
  type statusUpdater interface {
      GetTask(taskID, teamID string) (*models.Task, error)
      GetList(listID string) (*models.List, error)
      UpdateTaskStatus(taskID, status string) (*models.Task, error)
  }
  ```
- `changeStatus(client statusUpdater, w io.Writer, teamID, taskID, name string, format output.Format) error` holds all the logic. `RunE` only wires up the config, the client, and `os.Stdout`.
- JSON mode on a no-op: the "already" notice goes to stderr and the current task JSON goes to stdout, so scripts always get a task object.

### `internal/commands/tasks.go`
- Move `--output` to `tasksCmd.PersistentFlags()` so `tasks status` inherits it.
- Add `clickup tasks status HGAI-1217 "in progress"` to the `Long` examples.

### Docs and binaries
- `internal/commands/root.go`: add the command to the root help.
- `README.md`: add a usage example.
- `skills/SKILL.md`: add a "Change Task Status" section and add "change status", "move task to" to the trigger phrases in `description`.
- `make build-all` to refresh the pre-built binaries in `bin/`.

## Testing (TDD)

1. **`pkg/models/list_test.go`**: `FindStatus` matches `"In Progress"` to `in progress` and returns the canonical spelling, rejects `"progress"` and `""`, and `StatusNames` follows orderindex order regardless of input order.
2. **`internal/api/client_test.go`**: `Put` sends method PUT, a JSON body, and the auth header. `Get` sends no body. Debug output goes to stderr.
3. **`internal/api/tasks_test.go` / `lists_test.go`** (httptest): `UpdateTaskStatus` hits `/task/{id}` with the right body. `GetList` decodes statuses. `GetTask` with a custom ID still sets `custom_task_ids` and `team_id` (guards the helper refactor).
4. **`internal/commands/tasks_status_test.go`** (fake `statusUpdater`):
   - valid status: PUT is sent with the canonical spelling, and the output is `HGAI-1217: to do -> in progress`
   - case mismatch: the canonical name is sent
   - invalid status: no PUT, the error contains the list name and every status in order
   - already in status (any case): no GetList, no PUT, the notice is printed, and nil is returned
   - JSON mode: prints the updated task JSON
   - GetTask / GetList / PUT failures are wrapped with context (`failed to get task: ...`)
5. `make check` passes.
6. **E2E against a real workspace** with `make build` on a throwaway task: valid change with a custom ID, valid change with a native ID, wrong case, invalid status (exit code 1, list shown), no-op, `--output json`, and `--debug --output json | jq .` (stays valid JSON).

## Risks

- **Status inheritance:** `GET /list/{id}` returns the list's effective statuses, including statuses inherited from the folder or space. That is what the PUT validates against. This gets checked in the E2E step with a list that inherits its statuses.
- **Tasks in multiple lists:** a task's status belongs to its home list, and `task.List` is the home list, so this is correct.
- **Extra API call:** one GET for the list per change. It is skipped on a no-op. This is acceptable for an interactive CLI.

## Commits

1. `models: add List with FindStatus/StatusNames`
2. `api: support request bodies, add Put, send debug to stderr`
3. `api: add GetList and UpdateTaskStatus, extract taskIDQuery`
4. `commands: add tasks status subcommand`
5. `docs: document tasks status in help, README, and skill`
6. `build: refresh pre-built binaries`
