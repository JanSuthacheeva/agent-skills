# Plan: `clickup tasks status <id> <status>`

Review page: [.lavish/tasks-status-command-implementation.html](tasks-status-command-implementation.html)

## Decision

- Approach A: a new `status` subcommand of `tasks` coordinates the flow in the command layer, the same way `getTask` does. It gets the task, gets the task's home list, validates the name with a pure `models.List.FindStatus`, and then PUTs the list's own spelling of the status.
- No service layer. The API client gains write support (`Put`, a body parameter on `doRequest`) plus `GetList` and `UpdateTaskStatus`.
- Validation happens before the write. An invalid name writes nothing and lists the valid statuses.

## Step 0 - fix the broken build

`internal/output/table.go` declares `DetailFormatter.FormatComments` twice, at :191 and :238, so `go build ./...` fails. Delete the older copy (lines 237-279, the one without word wrapping). Run `make check` to confirm the build is green before starting on the feature.

## Units

### `internal/commands/tasks_status.go` (new)

```go
var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change the status of a task. The status must exist in the task's list.

Examples:
  clickup tasks status HGAI-1217 "in progress"   Move task to in progress
  clickup tasks status HGAI-1217 review          Move task to review`,
	Args: cobra.ExactArgs(2),
	RunE: runTasksStatus,
}

func init() {
	tasksCmd.AddCommand(tasksStatusCmd)
}

func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// invalidStatusError lists the valid statuses of the task's list, marking the current one
func invalidStatusError(name string, task *models.Task, list *models.List) error { ... }
```

### `pkg/models/list.go` (new)

```go
// List represents a ClickUp list with the statuses its tasks can have
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the status matching name, ignoring case and surrounding whitespace
func (l *List) FindStatus(name string) (*Status, bool) { ... }

// StatusNames returns the status names in board order
func (l *List) StatusNames() []string { ... }
```

- `FindStatus` returns a pointer to the list's own `Status`, so the name keeps the list's spelling and casing. It does no prefix or fuzzy matching.
- `StatusNames` sorts by `Orderindex`.

### `internal/api/lists.go` (new)

```go
// GetList gets a list, including the statuses its tasks can have
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

This calls `GET /list/{list_id}`. It returns the `*APIError` from `doRequest` unchanged, or a JSON decode error.

### `internal/api/tasks.go` (modified - added members)

```go
// updateTaskRequest is the request body for updating a task
type updateTaskRequest struct {
	Status string `json:"status"`
}

// UpdateTaskStatus sets a task's status and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error) { ... }

// setCustomTaskIDParams adds the query params ClickUp needs to resolve custom task IDs
func setCustomTaskIDParams(query url.Values, taskID, teamID string) { ... }
```

- `UpdateTaskStatus` sends `PUT /task/{task_id}` with the body `{"status": status}`.
- `GetTask` (tasks.go:66-70) and `GetTaskComments` (comments.go:17-20) switch to `setCustomTaskIDParams`. Their behaviour doesn't change.

### `internal/api/client.go` (modified)

```go
// doRequest performs an HTTP request, sending body as JSON when non-nil
func (c *Client) doRequest(method, path string, query url.Values, body interface{}) ([]byte, error) { ... }

// Get performs a GET request
func (c *Client) Get(path string, query url.Values) ([]byte, error) { ... }

// Put performs a PUT request with a JSON body
func (c *Client) Put(path string, query url.Values, body interface{}) ([]byte, error) { ... }
```

- A nil body sends no request body, which is today's behaviour. A non-nil body is JSON-marshalled.
- With `--debug`, the request body is logged next to the URL.
- `Get` passes `nil` as the body.

### Help text and docs (modified)

- `internal/commands/tasks.go`: add `clickup tasks status HGAI-1217 "in progress"   Change task status` to the `tasksCmd.Long` examples.
- `internal/commands/root.go`: add `clickup tasks status <ID> <status>` to "Get started" in `rootCmd.Long`.
- `README.md`, `skills/SKILL.md`: add a usage line next to the existing `--status` filter example.

## Data

| Type | Status | Fields | Crosses |
|---|---|---|---|
| `models.List` | new | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON -> api -> commands |
| `api.updateTaskRequest` | new, unexported | `Status string` (`json:"status"`) | api -> ClickUp (PUT body) |
| `models.Status` | existing | `ID, Status, Color, Type, Orderindex` | element of `List.Statuses`, `Task.Status` |
| `models.Task` | existing | uses `List.ID`, `Status`, `GetDisplayID()` | returned by `GetTask`, `UpdateTaskStatus` |

No stored data, config or migrations change.

## Call chain - `clickup tasks status HGAI-1217 "in progress"`

1. `rootCmd.Execute -> tasksStatusCmd.RunE runTasksStatus(cmd, args): error`
   - Error: any argument count other than 2 is rejected by cobra with `Error: accepts 2 arg(s), received N`.
2. `runTasksStatus -> getAPIClient(): (*api.Client, error)`
   - Error: a config error is returned unchanged.
3. `runTasksStatus -> getConfig(): (*config.Config, error)`
4. `runTasksStatus -> Client::GetTask(args[0], cfg.WorkspaceID): (*models.Task, error)`
   - Error: returns `fmt.Errorf("failed to get task: %w", err)`.
5. `runTasksStatus -> Client::GetList(task.List.ID): (*models.List, error)`
   - Error: returns `fmt.Errorf("failed to get list statuses: %w", err)`.
6. `runTasksStatus -> List::FindStatus(args[1]): (*models.Status, bool)`
   - Error: on `false`, returns `invalidStatusError(args[1], task, list)`. Nothing is written, and the command exits 1 with this on stderr:
     ```
     Error: "doing" is not a status in list "Sprint 42". Valid statuses:
       to do (current)
       in progress
       review
       complete
     ```
7. If `strings.EqualFold(status.Status, task.Status.Status)`:
   - print `fmt.Printf("%s is already %s\n", task.GetDisplayID(), task.Status.Status)`
   - return `nil` (exit 0) without sending the PUT
8. `runTasksStatus -> Client::UpdateTaskStatus(args[0], cfg.WorkspaceID, status.Status): (*models.Task, error)`
   - Internally: `-> Client::Put("/task/{id}", query, updateTaskRequest{Status: status}) -> Client::doRequest(PUT, ...)`.
   - Error: returns `fmt.Errorf("failed to update task status: %w", err)`.
9. `runTasksStatus -> fmt.Printf("%s: %s -> %s\n", updated.GetDisplayID(), task.Status.Status, updated.Status.Status)`, then return `nil`.
   - Example output: `HGAI-1217: to do -> in progress`.

Every error is printed once by `Execute` (root.go:48-53) as `Error: ...`, with exit 1.

## Test seams

- `pkg/models/list_test.go` - unit tests:
  - `FindStatus`: exact match, different case, padded name, missing name, empty list.
  - `StatusNames`: ordering by `Orderindex`.
  - Decoding a recorded `GET /list` payload.
- `internal/commands/tasks_status_test.go` - unit test of the `invalidStatusError` message: names in board order and the `(current)` marker.
- `internal/api` tests - an `httptest.Server` stands in for ClickUp, with `baseURL` set from inside the package. For `GetList`, `UpdateTaskStatus` and `Put`, assert:
  - the method and path
  - the custom-ID query
  - the JSON body
  - that a 4xx comes back as `*APIError`
- `runTasksStatus` - no unit test, same as `getTask`. Verify E2E with the built binary against a real workspace:
  - success
  - a name in different case
  - an invalid name
  - a task that already has that status
  - an unknown task ID
  - a custom ID versus a native ID

Finish with `make check`, then `make build-all`, which refreshes the pre-built binaries.

## Assumptions

1. Matching is case-insensitive and whitespace-trimmed, with no prefix or fuzzy matching. The list's own spelling is what gets sent.
2. Validation uses the task's home list (`task.List`).
3. Closed-type statuses (e.g. `complete`) are allowed like any other status.
4. Valid statuses are listed in `Orderindex` order, one per line, with the current one marked `(current)`.
5. An invalid status goes through the normal error path: stderr, exit 1, nothing written.
6. `status` has no `--output` flag.
7. `--debug` also logs the JSON request body.
8. The custom-ID query logic is extracted into `setCustomTaskIDParams` and used by all three task endpoints.

## Decisions made in review

- Success prints one line: `HGAI-1217: to do -> in progress`.
- If the task already has the target status, the PUT is skipped, the command prints `HGAI-1217 is already <status>`, and it exits 0.
- Multi-word statuses must be quoted (`cobra.ExactArgs(2)`).
