# Plan: `clickup tasks status <id> <status>`

Review page: [.lavish/tasks-status-implementation.html](tasks-status-implementation.html) (approved 2026-10-01)

## Decision

- New Cobra subcommand `tasks status` changes a task's status.
- It validates up front, in the command: fetch the task, fetch its list, then match the requested status against the list's statuses with a pure `models.List.FindStatus` helper before sending the PUT.
- The API layer only gets thin endpoint methods (`GetList`, `UpdateTaskStatus`) and a body-capable `Put`.
- Step 0: delete the duplicate `DetailFormatter.FormatComments` in `internal/output/table.go` (lines 237-279, the copy without word wrapping) so `go build` / `make check` pass again.

## Units

### `internal/output/table.go` (modified)

Delete the second `func (f *DetailFormatter) FormatComments` (lines 237-279). Keep the wrapping version at lines 190-235. No behaviour change.

### `internal/commands/tasks_status.go` (new)

```go
package commands

var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change the status of a task.

The status must be one of the statuses of the task's list.
Matching ignores case; the valid statuses are shown otherwise.

Examples:
  clickup tasks status HGAI-1217 in progress   Move task to "in progress"
  clickup tasks status HGAI-1217 complete      Complete a task`,
	Args: cobra.MinimumNArgs(2),
	RunE: runTasksStatus,
}

func init() {
	tasksCmd.AddCommand(tasksStatusCmd)
}

// joins args[1:] with single spaces, calls setTaskStatus(cmd.OutOrStdout(), args[0], name)
func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// setTaskStatus validates statusName against the task's list and applies it
func setTaskStatus(w io.Writer, taskID string, statusName string) error { ... }

// invalidStatusError lists the statuses the task's list accepts
func invalidStatusError(statusName string, task *models.Task, list *models.List) error { ... }
```

### `internal/commands/tasks.go`, `internal/commands/root.go` (modified, help text only)

- `tasksCmd.Long` examples: add `clickup tasks status HGAI-1217 in progress   Change task status`.
- `rootCmd.Long` "Get started": add `clickup tasks status <ID> <status>`.
- `tasksCmd` keeps `Args: cobra.MaximumNArgs(1)`. Cobra matches the `status` child before positional args.

### `internal/api/client.go` (modified)

```go
// doRequest performs an HTTP request, sending payload as a JSON body when non-nil
func (c *Client) doRequest(method, path string, query url.Values, payload interface{}) ([]byte, error) { ... }

// Get performs a GET request (unchanged signature, passes nil payload)
func (c *Client) Get(path string, query url.Values) ([]byte, error) { ... }

// Put performs a PUT request with a JSON body
func (c *Client) Put(path string, query url.Values, payload interface{}) ([]byte, error) { ... }
```

- A non-nil payload is `json.Marshal`ed into the request body. Marshal errors are returned as-is.
- Under `--debug`, also print the request body.

### `internal/api/tasks.go` (modified)

```go
// updateTaskRequest is the request body for updating a task
type updateTaskRequest struct {
	Status string `json:"status"`
}

// UpdateTaskStatus sets a task's status and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTaskStatus(taskID string, teamID string, status string) (*models.Task, error) { ... }

// addCustomTaskIDParams adds the query params ClickUp needs to resolve a custom task ID
func addCustomTaskIDParams(query url.Values, taskID string, teamID string) { ... }
```

- `UpdateTaskStatus` sends `PUT /task/{id}` with body `updateTaskRequest{Status: status}`. It decodes the response into `models.Task`.
- `addCustomTaskIDParams` sets `custom_task_ids=true` and `team_id` when `isCustomTaskID(taskID) && teamID != ""`.
- Use `addCustomTaskIDParams` in `GetTask` (replaces lines 66-70), in `UpdateTaskStatus`, and in `GetTaskComments` in `internal/api/comments.go` (replaces lines 17-20). Existing signatures do not change.

### `internal/api/lists.go` (new)

```go
package api

// GetList gets a list, including the statuses its tasks can have
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

`GetList` sends `GET /list/{id}` and decodes the response into `models.List`.

### `pkg/models/list.go` (new)

```go
package models

// List represents a ClickUp list
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the list status matching name, ignoring case and surrounding whitespace
func (l *List) FindStatus(name string) (Status, bool) { ... }

// StatusNames returns the names of the list's statuses in workflow order
func (l *List) StatusNames() []string { ... }
```

- `FindStatus` compares with `strings.EqualFold` after `strings.TrimSpace`. It returns the list's own `Status`, so ClickUp gets the canonical spelling.
- `StatusNames` sorts by `Orderindex`.

### Docs and release

- `README.md` Usage: add a "Change Task Status" block.
- `skills/SKILL.md`: add a "Change Task Status" block under "Available Commands", and add "change task status" and "move task to" to the description triggers.
- Run `make build-all` to refresh the binaries in `bin/`.

## Data

| Type | Status | Fields | Crosses |
|---|---|---|---|
| `models.List` | new | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON -> api -> commands |
| `api.updateTaskRequest` | new, unexported | `Status string \`json:"status"\`` | api -> ClickUp (PUT body) |
| `models.Status` | existing | `ID, Status, Color, Type, Orderindex` | reused for list statuses |
| `models.Task` | existing | uses `ID`, `Status`, `List.ID`, `GetDisplayID()` | ClickUp -> api -> commands |

## Call chains

### 1. Valid status: `clickup tasks status HGAI-1217 in progress`

1. `Cobra -> runTasksStatus(cmd *cobra.Command, args []string): error` (after `MinimumNArgs(2)` passes)
2. `runTasksStatus -> setTaskStatus(cmd.OutOrStdout(), args[0], strings.Join(args[1:], " ")): error`
3. `setTaskStatus -> getAPIClient(): (*api.Client, error)`, then `getConfig(): (*config.Config, error)`
4. `setTaskStatus -> Client::GetTask(taskID, cfg.WorkspaceID): (*models.Task, error)`, which calls `Client::Get("/task/{id}", query)`
5. `setTaskStatus -> Client::GetList(task.List.ID): (*models.List, error)`, which calls `Client::Get("/list/{id}", nil)`
6. `setTaskStatus -> List::FindStatus(statusName): (models.Status, bool)` returns `(match, true)`
7. If `strings.EqualFold(task.Status.Status, match.Status)`: write `HGAI-1217 is already "in progress"` to `w` and return `nil`. No PUT is sent; exit 0.
8. `setTaskStatus -> Client::UpdateTaskStatus(task.ID, cfg.WorkspaceID, match.Status): (*models.Task, error)`
   - This calls `Client::Put("/task/{id}", query, updateTaskRequest{Status: status})`.
   - `Put` calls `doRequest(http.MethodPut, path, query, payload)`.
9. `setTaskStatus -> fmt.Fprintf(w, "%s: %s -> %s\n", task.GetDisplayID(), task.Status.Status, updated.Status.Status)`, then return `nil`; exit 0.

Error paths. All errors are returned from `setTaskStatus` and printed by `Execute()` as `Error: ...` on stderr, with exit 1.

- Fewer than 2 args: Cobra returns `requires at least 2 arg(s), only received 1` before `RunE` runs.
- Config missing or unreadable: the `getAPIClient` / `getConfig` error is returned unwrapped.
- Step 4 fails (404 unknown ID, 401 token): `fmt.Errorf("failed to get task: %w", err)`, wrapping `*api.APIError`.
- Step 5 fails: `fmt.Errorf("failed to get list statuses: %w", err)`.
- Step 8 fails (statuses changed since step 5, no permission): `fmt.Errorf("failed to update task status: %w", err)`.

### 2. Invalid status: `clickup tasks status HGAI-1217 done`

1. Steps 1-5 of chain 1.
2. `setTaskStatus -> List::FindStatus("done"): (models.Status{}, false)`
3. `setTaskStatus -> invalidStatusError("done", task, list): error`
   - This calls `List::StatusNames(): []string`.
   - The status matching `task.Status.Status` gets the suffix ` (current)`.
4. The error is returned through `runTasksStatus` to `Execute()`, which prints to stderr and exits 1. No PUT is sent.

```
Error: invalid status "done" for list "Sprint 12". Valid statuses:
  to do (current)
  in progress
  review
  complete
```

## Test seams

- `pkg/models/list_test.go` - unit tests, no fakes.
  - FindStatus: exact match, different case, surrounding spaces, unknown status.
  - StatusNames: sorted by Orderindex.
- `internal/api/client_test.go`, `tasks_test.go`, `lists_test.go` - use `httptest.Server` and set the unexported `c.baseURL`. Assert:
  - PUT method, path, custom-ID query and JSON body
  - decoded List statuses
  - `*APIError` on 4xx
- `internal/commands/tasks_status_test.go` - set the package globals `apiClient` (pointing at an httptest fake ClickUp) and `cfg`, and reset them in `t.Cleanup`. Cases:
  - valid status
  - wrong case
  - multi-word status
  - already in status (assert no PUT)
  - invalid status (error text, and assert no PUT)
  - 404 task
- `internal/output`: the existing tests compile and pass again after step 0.
- E2E: run `make build`, then run `bin/clickup tasks status` against a scratch task in a real workspace. Use both a custom ID and a native ID, and try a valid, a wrong-case, a multi-word and an invalid status. Confirm the result in the ClickUp UI.

## Assumptions

1. Matching ignores case and surrounding whitespace; the list's own spelling is sent to ClickUp.
2. Multi-word statuses work without quotes: `args[1:]` are joined with single spaces. The quoted form also works.
3. If the task is already in the requested status, print `HGAI-1217 is already "in progress"`, send no PUT, and exit 0.
4. On success, print one line to stdout: `HGAI-1217: to do -> in progress`.
5. Invalid status:
   - exit 1, with the error on stderr
   - list the valid statuses one per line, in workflow order
   - mark the current status `(current)`
   - no "did you mean" suggestions
6. `GET /list/{id}` returns the effective statuses, including ones inherited from the folder or space. Verify this in E2E; if it's wrong, the design needs a fallback.
7. The PUT uses the native `task.ID` from the fetched task.
8. Closed and done-type statuses are treated like any other, with no confirmation prompt.
9. Subtasks work the same way, using their own `list.id`.
10. Help text, README, SKILL.md and `bin/` binaries are updated in the same change.

## Decisions made during review

- Approach A (validate up front in the command) was chosen over an optimistic write and over a validating API-layer method.
- The duplicate `FormatComments` is deleted as the first step.
- Q1: trailing args are joined (`cobra.MinimumNArgs(2)`).
- Q2: confirmation line only, no `--output json` flag on `tasks status`.
