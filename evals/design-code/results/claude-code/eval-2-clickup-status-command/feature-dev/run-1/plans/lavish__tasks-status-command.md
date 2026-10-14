# Plan: `clickup tasks status <id> <status>`

## Goal

Change a task's status from the CLI. Validate the requested status against the statuses of the task's list; if it is not valid, fail and print the valid ones.

## Decisions (confirmed)

| Topic | Decision |
|---|---|
| Matching | Case-insensitive exact match on the trimmed input. No prefix matching. |
| Invalid status | Exit 1. Print the list's statuses in board order (`orderindex`), mark the current one, no color. |
| Already in that status | Skip the API call, print a notice, exit 0. |
| Success output | One line `HGAI-1217: to do -> in progress`. `-o json` prints the updated task. |
| Arguments | Exactly 2 (`cobra.ExactArgs(2)`). Multi-word statuses must be quoted. |
| Confirmation | None. |
| Scope | No `statuses` listing command. Regenerate `bin/` with `make build-all`. |

## Current state

- **Build is broken on `main`.** `internal/output/table.go:238` redeclares `DetailFormatter.FormatComments` (first at `:191`), introduced by merge `7411557`. `go vet` and `go test` fail.
- `api.Client.doRequest` (`internal/api/client.go:42`) always sends a nil body; only `Get` exists. Debug logs go to stdout.
- Custom-ID query logic (`custom_task_ids` + `team_id`) is duplicated in `GetTask` and `GetTaskComments`.
- `models.Task.List` (`ListInfo`) has the home list ID but no statuses. `models.Status` already has `Status`, `Color`, `Type`, `Orderindex`.
- `tasksCmd` is `tasks [task_id]` with `Args: cobra.MaximumNArgs(1)`. Because `Args` is set, Cobra routes `tasks status ...` to a subcommand while `tasks HGAI-1217` keeps working.
- No tests in `internal/api` or `internal/commands`.

## Behavior

Each example starts from the same state: HGAI-1217 is in `to do` on list "Sprint 42".

```
$ clickup tasks status HGAI-1217 "In Progress"
HGAI-1217: to do -> in progress

$ clickup tasks status HGAI-1217 doing
Error: "doing" is not a valid status for list "Sprint 42". Valid statuses:
  to do (current)
  in progress
  review
  complete
(exit 1)

$ clickup tasks status HGAI-1217 "To Do"
HGAI-1217 is already "to do"
(exit 0)

$ clickup tasks status HGAI-1217 review -o json
{ ...updated task JSON... }
```

With `-o json`, stdout only ever contains task JSON (the unchanged task in the "already" case). The notice goes to stderr.

## Flow

1. `GET /task/{id}` via existing `GetTask(id, workspaceID)` - handles custom IDs, yields native `task.ID`, `task.List.ID`, current status.
2. `GET /list/{list_id}` via new `GetList` - yields list name + statuses.
3. `list.FindStatus(input)` - canonical status or invalid-status error.
4. If canonical == current (case-insensitive): notice, exit 0.
5. `PUT /task/{task.ID}` with `{"status": "<canonical name>"}` via new `UpdateTaskStatus` - returns updated task.
6. Print one-line transition, or the updated task as JSON.

Sending the canonical name from the list (not the raw input) means ClickUp never sees user casing.

## Architecture options

### A. Minimal - everything in the command
API gets `GetListStatuses` + `UpdateTaskStatus`; matching and error formatting live inline in `runTasksStatus`. No refactors.
- Pro: fewest lines touched.
- Con: matching logic untestable without HTTP; leaves custom-ID duplication to grow to 3 copies; no command-level test possible.

### B. Layered (recommended)
Model owns matching (`List.FindStatus`, `List.SortedStatuses`), API client gets generic body support plus thin `GetList` / `UpdateTaskStatus`, command orchestrates and formats. Small enabling refactors: `taskIDQuery` helper, `SetBaseURL` for tests.
- Pro: each layer does one thing; pure matching is unit-tested; full flow is testable against `httptest`; matches existing `internal/api` per-domain file pattern.
- Con: about 2x the diff of A, touches `client.go`.

### C. Service method in the API client
`api.Client.SetTaskStatus(id, status)` performs get-task, get-list, validate, update and returns a typed `InvalidStatusError`.
- Pro: one-call API for future callers.
- Con: puts business rules into the HTTP client, which today is a thin transport; hides the 3 round trips; the "already in status" and output decisions still leak back to the command.

**Chosen: B** (approved). It is the simplest design where every piece is testable and nothing is in the wrong layer. A saves a few lines at the cost of testability; C abstracts a single caller.

## Changes (option B)

### 0. Fix the broken build - `internal/output/table.go`
Delete the second `DetailFormatter.FormatComments` (`:237-279`). Keep the first one (word-wrapped, from #3). Separate commit.

### 1. API transport - `internal/api/client.go`
- `doRequest(method, path string, query url.Values, body any)`: if `body != nil`, `json.Marshal` it and pass `bytes.NewReader` to `http.NewRequest`. `Content-Type: application/json` is already set.
- Add `Put(path string, query url.Values, body any) ([]byte, error)`. `Get` passes `nil`.
- `SetBaseURL(url string)` alongside `SetDebug`, so tests outside the package can point the client at `httptest`.
- Debug output to `os.Stderr` (currently stdout, which corrupts `-o json` with `--debug`). Log request body in debug mode.

### 2. Task ID query helper - `internal/api/tasks.go`, `internal/api/comments.go`
```go
func taskIDQuery(taskID, teamID string) url.Values
```
Returns `custom_task_ids=true&team_id=...` for custom IDs, empty otherwise. Used by `GetTask`, `GetTaskComments`, `UpdateTaskStatus`.

### 3. Lists - new `pkg/models/list.go`, new `internal/api/lists.go`
```go
type List struct {
    ID       string   `json:"id"`
    Name     string   `json:"name"`
    Statuses []Status `json:"statuses"`
}

func (l *List) FindStatus(name string) (Status, bool)   // strings.EqualFold on TrimSpace(name)
func (l *List) SortedStatuses() []Status                // copy sorted by Orderindex
```
```go
func (c *Client) GetList(listID string) (*models.List, error)  // GET /list/{id}
```

### 4. Status update - `internal/api/tasks.go`
```go
func (c *Client) UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)
// PUT /task/{id}?{taskIDQuery}  body {"status": status}  -> decoded Task
```
The command passes native `task.ID`, so no custom-ID query is sent in practice; the `teamID` param keeps the signature consistent with `GetTask`.

### 5. Command - new `internal/commands/tasks_status.go`
```go
var tasksStatusCmd = &cobra.Command{
    Use:   "status <task_id> <status>",
    Short: "Change a task's status",
    Args:  cobra.ExactArgs(2),
    RunE:  runTasksStatus,
}

func init() { tasksCmd.AddCommand(tasksStatusCmd) }
```
- `runTasksStatus` implements the flow above. Error wrapping matches existing style: `failed to get task: %w`, `failed to get list: %w`, `failed to update status: %w`.
- `invalidStatusError(input string, list *models.List, current string) error` builds the multi-line message from `list.SortedStatuses()`, appending ` (current)` on the case-insensitive match with `current`.
- If the list returns zero statuses: `list "X" returned no statuses` (guards against a misleading empty "Valid statuses:" block).
- Writes via `cmd.OutOrStdout()` / `cmd.ErrOrStderr()` so the command test can capture output.
- `--output` moves from `tasksCmd.Flags()` to `tasksCmd.PersistentFlags()` so `status` inherits `-o` without a second binding. No behavior change for `tasks`.

### 6. Docs and help text
- `tasksCmd.Long` and `rootCmd.Long`: add `clickup tasks status <ID> <status>` example.
- `README.md`: new "Change Status" section.
- `skills/SKILL.md`: add the command under a "Change Task Status" heading, extend the description triggers ("change status", "move task to", "mark as done"), and note that on an invalid-status error the agent should show the listed valid statuses verbatim.

### 7. Binaries
`make build-all` to refresh `bin/`. Separate commit.

## Tests

| File | Cases |
|---|---|
| `pkg/models/list_test.go` (new) | `FindStatus`: exact, different case, surrounding whitespace, prefix `"prog"` does not match, unknown. `SortedStatuses`: out-of-order input sorted by `Orderindex`, original slice untouched. JSON decode of a `GET /list` payload. |
| `internal/api/client_test.go` (new) | `httptest` server: `Put` sends method PUT, JSON body, `Authorization` and `Content-Type` headers; `Get` sends no body; 4xx returns `*APIError`. |
| `internal/api/tasks_test.go` (new) | `UpdateTaskStatus` path, body `{"status":"in progress"}`, custom-ID query for `HGAI-1217`, none for native ID; `taskIDQuery` table test. `GetList` decodes statuses. |
| `internal/commands/tasks_status_test.go` (new) | Fake ClickUp via `httptest` + `SetBaseURL`, set `cfg`/`apiClient` globals, run `rootCmd` with `SetArgs`. Cases: success prints transition and sends canonical name; invalid status returns error with board-ordered list and `(current)` marker, no PUT made; already-in-status prints notice, no PUT made; `-o json` prints decoded task; wrong arg count errors. Reset globals per test. |

## Manual E2E (real workspace)

Build with `make build`, then against a real task (reverting at the end):
1. Valid change with native ID and with custom ID.
2. Mixed-case input.
3. Invalid status - verify list order matches the ClickUp board and the current marker.
4. Same status - notice, no change in ClickUp activity log.
5. Subtask.
6. Task in a list that inherits statuses from its folder/space - confirm `GET /list` returns the effective statuses (see risks).
7. `-o json` and `--debug -o json | jq .` (debug no longer corrupts stdout).
8. `clickup tasks`, `clickup tasks HGAI-1217`, `clickup tasks --status open` still behave as before.

## Build sequence and commits

1. `fix: remove duplicate DetailFormatter.FormatComments` - restore `make check`.
2. `refactor(api): request bodies, Put, SetBaseURL, taskIDQuery` + client tests.
3. `feat(api): GetList and UpdateTaskStatus` + model and API tests.
4. `feat: clickup tasks status command` + command tests.
5. `docs: document tasks status in help, README and skill`.
6. `build: refresh pre-built binaries`.

`make check` must pass after each commit.

## Risks

- **Inherited statuses.** Lists that do not override statuses inherit them from folder/space. ClickUp's `GET /list/{id}` is expected to return the effective `statuses` array regardless; the zero-status guard and E2E step 6 cover the case where it does not. If it does not, fall back to `GET /folder/{id}` then `GET /space/{id}` - only add this if E2E shows it is needed.
- **Three round trips.** `GetTask` also fetches subtasks and markdown description, which is unused here. Acceptable for an interactive command; not worth a second `GetTask` variant now.
- **`status` as a reserved word under `tasks`.** A task whose ID is literally `status` can no longer be viewed via `clickup tasks status`. ClickUp IDs never take that form, so no real impact.
- **Race.** Someone else may change the list's statuses between validation and PUT; ClickUp then rejects the PUT and the API error is surfaced via `failed to update status: ...`. No extra handling needed.
- **`--output` becoming persistent** makes it appear under "Global Flags" in `clickup tasks status --help`. Intended.
