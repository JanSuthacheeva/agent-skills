# Plan: `clickup tasks status <id> <status>`

Review surface: [.lavish/tasks-status-implementation.html](tasks-status-implementation.html)

## Decision

Approach A. A new `status` subcommand under `tasks` chains three client calls (GET task, GET list, PUT task), the same way `getTask` chains calls. Validation is a pure method on a new `models.List`. The API client keeps one method per endpoint.

Decided in review:
- On success, print one line: `HGAI-1217: open -> in progress`. No `-o` flag on `tasks status`.
- If the task is already in the requested status, skip the PUT, print `HGAI-1217 is already "in progress"` and exit 0.
- Match the full status name only, case-insensitively. No prefix matching.

## Units

### `internal/commands/tasks_status.go` (new)

```go
var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change the status of a task. The status must exist in the task's list.

Examples:
  clickup tasks status HGAI-1217 "in progress"
  clickup tasks status 86a3xyzw review`,
	Args: cobra.ExactArgs(2),
	RunE: runTasksStatus,
}

func init() {
	tasksCmd.AddCommand(tasksStatusCmd)
}

// Cobra entry point; calls changeTaskStatus(args[0], args[1])
func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// Fetches task and list, validates, updates unless already in that status, prints the result
func changeTaskStatus(taskID, statusName string) error { ... }

// Builds: status "<name>" not found in list "<list>"\nValid statuses: "a", "b", ...
func invalidStatusError(statusName string, list *models.List) error { ... }
```

### `internal/api/client.go` (modified)

```go
// doRequest performs an HTTP request, sending body as JSON when non-nil
// (was: doRequest(method, path string, query url.Values)); --debug also prints the request body
func (c *Client) doRequest(method, path string, query url.Values, body interface{}) ([]byte, error) { ... }

// Get performs a GET request (unchanged signature, passes nil body)
func (c *Client) Get(path string, query url.Values) ([]byte, error) { ... }

// Put performs a PUT request with a JSON body
func (c *Client) Put(path string, query url.Values, body interface{}) ([]byte, error) { ... }
```

### `internal/api/tasks.go` (modified)

```go
// updateTaskRequest is the request body for updating a task
type updateTaskRequest struct {
	Status string `json:"status"`
}

// UpdateTaskStatus sets the status of a task and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error) { ... }

// addCustomTaskIDQuery adds the query params ClickUp needs to resolve custom task IDs
func addCustomTaskIDQuery(query url.Values, taskID, teamID string) { ... }
```

`GetTask` (tasks.go:66-70) and `GetTaskComments` (comments.go:17-20) replace their duplicated custom ID blocks with a call to `addCustomTaskIDQuery`. Their behaviour does not change.

### `internal/api/lists.go` (new)

```go
// GetList gets a list including its statuses (GET /list/{id})
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

### `pkg/models/list.go` (new)

```go
// List represents a ClickUp list
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the list status matching name case-insensitively (full name only)
func (l *List) FindStatus(name string) (Status, bool) { ... }

// StatusNames returns the status names in board order (by Orderindex)
func (l *List) StatusNames() []string { ... }
```

### Help text and docs (modified)

- `internal/commands/tasks.go:28-36`: add `clickup tasks status HGAI-1217 "in progress"` to the `Long` examples.
- `internal/commands/root.go:28-42`: add the command under "Get started".
- `README.md` (Tasks section) and `skills/SKILL.md`: document the command and add "change status" and "move task to" to the skill description triggers.

## Data

| Type | Status | Fields | Boundary |
|------|--------|--------|----------|
| `models.List` | new | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON -> api -> commands |
| `models.Status` | existing, reused | `ID`, `Status`, `Color`, `Type`, `Orderindex` | list statuses |
| `api.updateTaskRequest` | new, unexported | `Status string \`json:"status"\`` | api -> ClickUp request body |

No config, storage or migration changes.

## Call chain: `clickup tasks status HGAI-1217 "in progress"`

1. `cobra -> runTasksStatus(cmd, ["HGAI-1217", "in progress"]): error` -> `changeTaskStatus("HGAI-1217", "in progress"): error`
2. `changeTaskStatus -> getAPIClient(): (*api.Client, error)`
3. `changeTaskStatus -> getConfig(): (*config.Config, error)`
4. `changeTaskStatus -> Client.GetTask(taskID, cfg.WorkspaceID): (*models.Task, error)`
5. `changeTaskStatus -> Client.GetList(task.List.ID): (*models.List, error)` -> `Client.Get("/list/{id}", nil)`
6. `changeTaskStatus -> List.FindStatus(statusName): (models.Status, bool)`
7. If `strings.EqualFold(task.Status.Status, target.Status)`: print `HGAI-1217 is already "in progress"` and return `nil`. No PUT.
8. `changeTaskStatus -> Client.UpdateTaskStatus(taskID, cfg.WorkspaceID, target.Status): (*models.Task, error)` -> `Client.Put("/task/{id}", query, updateTaskRequest{Status: target.Status}): ([]byte, error)` -> `doRequest(http.MethodPut, ...)`
9. Print `HGAI-1217: open -> in progress` to stdout, using `task.GetDisplayID()`, `task.Status.Status` and `updated.Status.Status`. Exit 0.

### Error paths

`changeTaskStatus` returns every error. `Execute()` prints `Error: ...` to stderr and exits 1.

- E0, wrong arg count: `cobra.ExactArgs(2)` -> `accepts 2 arg(s), received N`
- E1, config missing or invalid: the error from `getAPIClient` is returned unchanged.
- E2, GetTask fails: `failed to get task: %w` (wraps `*APIError`, e.g. a 404).
- E3, GetList fails: `failed to get list statuses: %w`
- E4, `FindStatus` returns false: `invalidStatusError` is returned and no PUT is sent:
  ```
  Error: status "doing" not found in list "Sprint 12"
  Valid statuses: "open", "in progress", "review", "complete"
  ```
- E5, PUT rejected: `failed to update task status: %w`

## Test seams

- `models.List.FindStatus` / `StatusNames`: table-driven tests in `pkg/models/list_test.go` covering exact match, different case, missing, empty list and ordering by `Orderindex`.
- `models.List` JSON: deserialization test from a trimmed real `GET /list` response.
- `api.Client` (`GetList`, `UpdateTaskStatus`, `Put`): an in-package `httptest.Server` test that sets `baseURL`. Assert method, path, custom ID query and JSON body. These are the first API tests in the repo.
- `tasksStatusCmd`: no unit seam because of package globals. Verify E2E against a real workspace: valid status, wrong case, invalid status, same status, custom ID and native ID.

## Assumptions

1. `GET /list/{id}` returns the list's effective statuses, including statuses inherited from the folder or space. Verify this E2E as the first implementation step.
2. The canonical status name from the list, not the user's casing, is what gets sent.
3. Multi-word statuses must be quoted (`ExactArgs(2)`). Accepting unquoted words later would not break anything.
4. The error lists valid statuses in board order, quoted and comma-separated.
5. Closed and done-type statuses are allowed like any other status.
6. The parent's aliases apply: `clickup t status ...` and `clickup task status ...`.
7. `--debug` also prints the PUT request body.
8. The existing `models.Status` type is reused as-is for list statuses.
