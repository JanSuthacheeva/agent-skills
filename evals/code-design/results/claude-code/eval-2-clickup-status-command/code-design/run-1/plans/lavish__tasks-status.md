# Plan: `clickup tasks status <id> <status>`

Design review page: [tasks-status-implementation.html](tasks-status-implementation.html)

## Decision

- Approach A: a new `status` subcommand of `tasks` orchestrates thin API calls like `getTask` does - get task, get its list, match the status with a pure helper on a new `models.List`, then update.
- Nothing is written if the status is not in the list; the valid statuses are printed instead.
- Step 0: delete the stale duplicate `DetailFormatter.FormatComments` in `internal/output/table.go:237-281` (main does not build).
- Review: add `Client.SetBaseURL` for command tests (Q1); use generic `UpdateTask` + `UpdateTaskRequest` (Q2).

## Steps

0. Delete the second `func (f *DetailFormatter) FormatComments` (`internal/output/table.go:237-281`, the copy without `wrapText`). `make check` must be green before continuing.
1. E2E check with `--debug` against a real workspace: `GET /list/{id}` returns the effective statuses, including statuses inherited from folder/space. If it does not, stop and revisit the design.
2. `pkg/models/list.go` + tests.
3. `internal/api/client.go` (payload, `Put`, `SetBaseURL`) + tests.
4. `internal/api/tasks.go` (`taskIDQuery`, `UpdateTask`), `internal/api/comments.go` (use `taskIDQuery`), `internal/api/lists.go` + tests.
5. `internal/commands/tasks_status.go` + tests.
6. Help text and docs: `root.go:33-36` "Get started", `tasksCmd.Long` example (`tasks.go:30-36`), `README.md` Tasks section, `skills/SKILL.md` commands and trigger phrases ("change status", "move task to ...").
7. `make check`, E2E with the built binary, `make build-all`.

## Units

### `pkg/models/list.go` (new)

```go
package models

// List represents a ClickUp list with its effective statuses
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the status matching name, ignoring case and surrounding whitespace
func (l *List) FindStatus(name string) (Status, bool) { ... }

// StatusNames returns the status names in board order (sorted by Orderindex)
func (l *List) StatusNames() []string { ... }
```

### `internal/api/client.go` (modified)

`doRequest` encodes `payload` as a JSON body when non-nil (and prints it in debug mode). `Get` passes `nil`.

```go
// doRequest performs an HTTP request, sending payload as a JSON body when non-nil
func (c *Client) doRequest(method, path string, query url.Values, payload interface{}) ([]byte, error) { ... }

// Get performs a GET request
func (c *Client) Get(path string, query url.Values) ([]byte, error) { ... }

// Put performs a PUT request with a JSON body
func (c *Client) Put(path string, query url.Values, payload interface{}) ([]byte, error) { ... }

// SetBaseURL overrides the API base URL
func (c *Client) SetBaseURL(baseURL string) { ... }
```

### `internal/api/tasks.go` (modified)

`GetTask` starts from `taskIDQuery` and adds its `include_*` params; behaviour unchanged.

```go
// UpdateTaskRequest contains the task fields to change
type UpdateTaskRequest struct {
	Status string `json:"status,omitempty"`
}

// UpdateTask updates a task and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTask(taskID string, teamID string, req *UpdateTaskRequest) (*models.Task, error) { ... }

// taskIDQuery returns the query needed to address a task by native or custom ID
// (empty for native IDs, custom_task_ids + team_id for custom IDs)
func taskIDQuery(taskID string, teamID string) url.Values { ... }
```

### `internal/api/comments.go` (modified)

`GetTaskComments` replaces its inline custom-ID block (`comments.go:16-20`) with `query := taskIDQuery(taskID, teamID)`. Signature unchanged.

### `internal/api/lists.go` (new)

```go
package api

// GetList gets a list including its statuses (GET /list/{list_id})
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

### `internal/commands/tasks_status.go` (new)

```go
package commands

var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change the status of a task. The status must exist in the task's list;
otherwise the valid statuses are shown.

Examples:
  clickup tasks status HGAI-1217 "in progress"
  clickup tasks status HGAI-1217 in progress
  clickup tasks status 86a3xyzw complete`,
	Args: cobra.MinimumNArgs(2),
	RunE: runTasksStatus,
}

func init() {
	tasksCmd.AddCommand(tasksStatusCmd)
}

// joins args[1:] with single spaces, calls setTaskStatus(cmd.OutOrStdout(), args[0], status)
func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// setTaskStatus validates status against the task's list and updates the task
func setTaskStatus(w io.Writer, taskID string, status string) error { ... }

// invalidStatusError lists the valid statuses of the list
func invalidStatusError(status string, list *models.List) error { ... }
```

## Data

| Type | Status | Fields | Boundary |
|---|---|---|---|
| `models.List` | new | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON (`GET /list/{id}`) -> `api.GetList` -> command |
| `api.UpdateTaskRequest` | new | `Status string \`json:"status,omitempty"\`` | command -> `api.UpdateTask` -> JSON body of `PUT /task/{id}` |
| `models.Status` | existing | `ID, Status, Color, Type string`, `Orderindex int` | element of `List.Statuses`, `Task.Status` |
| `models.Task` | existing | uses `List.ID`, `Status.Status`, `GetDisplayID()` | returned by `GetTask`, `UpdateTask` |

## Call chains

### A. Valid status: `clickup tasks status HGAI-1217 In Progress`

1. `cobra -> runTasksStatus(cmd, ["HGAI-1217", "In", "Progress"]): error`
2. `runTasksStatus -> setTaskStatus(cmd.OutOrStdout(), "HGAI-1217", "In Progress"): error`
3. `setTaskStatus -> getAPIClient(): (*api.Client, error)`
4. `setTaskStatus -> getConfig(): (*config.Config, error)`
5. `setTaskStatus -> Client::GetTask("HGAI-1217", cfg.WorkspaceID): (*models.Task, error)` - `GET /task/HGAI-1217?custom_task_ids=true&team_id=...`
6. `setTaskStatus -> Client::GetList(task.List.ID): (*models.List, error)` - `GET /list/{list_id}`
7. `setTaskStatus -> List::FindStatus("In Progress"): (models.Status, bool)` - `{Status: "in progress"}, true`
8. If `strings.EqualFold(task.Status.Status, match.Status)`: print `HGAI-1217 is already "in progress"` to `w`, return `nil` (no PUT).
9. `setTaskStatus -> Client::UpdateTask("HGAI-1217", cfg.WorkspaceID, &api.UpdateTaskRequest{Status: "in progress"}): (*models.Task, error)`
   1. `UpdateTask -> taskIDQuery("HGAI-1217", teamID): url.Values`
   2. `UpdateTask -> Client::Put("/task/HGAI-1217", query, req): ([]byte, error)` -> `doRequest(http.MethodPut, path, query, req)`, body `{"status":"in progress"}`
   3. Decode body into `models.Task`.
10. `setTaskStatus -> fmt.Fprintf(w, "%s: %s -> %s\n", updated.GetDisplayID(), task.Status.Status, updated.Status.Status)` - prints `HGAI-1217: to do -> in progress`; return `nil`, exit 0.

Error paths (returned to `Execute`, printed to stderr as `Error: ...`, exit 1, nothing written):

- Fewer than 2 args: cobra `MinimumNArgs(2)` -> `requires at least 2 arg(s), only received 1` (usage silenced).
- Steps 3-4: config load error, returned unwrapped (as in `getTask`).
- Step 5: `failed to get task: %w` (wraps `*api.APIError` or network error).
- Step 6: `failed to get list: %w`.
- Step 7 no match: chain B.
- Step 9: `failed to update task status: %w` (e.g. statuses changed after step 6). No retry.

### B. Invalid status: `clickup tasks status HGAI-1217 inprogress`

1. Steps 1-6 as in A.
2. `setTaskStatus -> List::FindStatus("inprogress"): (models.Status, bool)` - `Status{}, false`
3. `setTaskStatus -> invalidStatusError("inprogress", list): error` -> `List::StatusNames(): []string`; returned. No `UpdateTask` call.
4. `Execute` prints to stderr, exit 1:

```
Error: invalid status "inprogress" for list "Sprint 12". Valid statuses:
  to do
  in progress
  review
  complete
```

If the list has no statuses, `invalidStatusError` returns `list "Sprint 12" has no statuses`.

## Test seams

- `pkg/models/list_test.go` - pure: `FindStatus` exact / case / surrounding whitespace / missing; `StatusNames` sorted by `Orderindex`.
- `internal/api/tasks_test.go` - `httptest.Server`: `UpdateTask` sends PUT with `{"status":"..."}` body and custom-ID query, decodes task; `taskIDQuery` native vs custom.
- `internal/api/lists_test.go` - `httptest.Server`: `GetList` path, `statuses` decoding, 4xx -> `*APIError`.
- `internal/commands/tasks_status_test.go` - `httptest.Server` faking task/list/update; set globals `apiClient` (built with `SetBaseURL(server.URL)`) and `cfg`; output in `bytes.Buffer`: happy path, invalid status (assert no PUT), already-in-status (assert no PUT).
- `internal/output/table_test.go` - existing tests cover step 0.
- E2E with the built binary on a real workspace: valid, wrong case, unquoted multi-word, invalid, already-in-status, native and custom ID, `--debug` to inspect the PUT body.

## Assumptions

1. Matching ignores case and surrounding whitespace; the list's exact spelling is sent.
2. Multi-word statuses work with or without quotes (args after the ID joined with single spaces).
3. Already in that status: prints `HGAI-1217 is already "in progress"`, exit 0, no write.
4. Success prints one line to stdout: `HGAI-1217: to do -> in progress`. No `-o/--output` on this subcommand.
5. Invalid status: nothing written; stderr lists all valid statuses in board order, one per line; exit 1.
6. No "did you mean" suggestion.
7. Closed/done-type statuses are allowed like any other.
8. `GET /list/{id}` returns effective statuses (verified in step 1).
9. A list with no statuses is an error, never "skip validation".
10. Native and custom IDs both work; `--workspace` override honoured via `getConfig`.
11. Status changes between check and update surface as `failed to update task status: ...`; no retry.
12. Docs updated and `bin/` binaries rebuilt with `make build-all`.

## Decisions made during review

- Q1: add `Client.SetBaseURL`; command-level tests use `httptest`.
- Q2: generic `UpdateTask(taskID, teamID, *UpdateTaskRequest)`.
