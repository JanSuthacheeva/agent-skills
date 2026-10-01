# `clickup tasks status <id> <status>` - Implementation Plan

Design review page: [.lavish/tasks-status-command-implementation.html](tasks-status-command-implementation.html) (approved 2026-10-01)

## Decision

- New `tasks status` subcommand, built the same way as `getTask`: the command handles the whole flow itself (get task, get its list, match the status, update, print). No service layer; no more write commands are planned.
- Status matching is a pure method on a new `models.List`.
- Prerequisite, own commit: `main` does not build. Delete the duplicate `DetailFormatter.FormatComments` at `internal/output/table.go:237-281` (the copy without word wrap) and keep the one at line 191.

## Units

### `internal/commands/tasks_status.go` (new)

```go
package commands

var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change the status of a task. The status must exist on the task's list.

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

// Joins args[1:] with " " so quotes are optional, then calls changeTaskStatus.
func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// get task -> get list -> FindStatus -> skip if unchanged -> UpdateTaskStatus -> print.
func changeTaskStatus(taskID string, statusName string) error { ... }

// Builds the multi-line error naming the list and its valid statuses, in list order.
func invalidStatusError(statusName string, list *models.List) error { ... }
```

### `internal/commands/tasks.go`, `root.go` (modified, help text only)

- `tasksCmd.Long` examples: add `clickup tasks status HGAI-1217 "in progress"   Change task status`.
- `rootCmd.Long` "Get started": add `clickup tasks status <ID> <status>`.
- `tasksCmd` keeps `MaximumNArgs(1)`; Cobra resolves the `status` subcommand first.

### `internal/api/client.go` (modified)

```go
// payload, when non-nil, is JSON-marshalled into the request body (printed under --debug).
func (c *Client) doRequest(method, path string, query url.Values, payload interface{}) ([]byte, error) { ... }

// Unchanged signature; passes nil payload.
func (c *Client) Get(path string, query url.Values) ([]byte, error) { ... }

func (c *Client) Put(path string, query url.Values, payload interface{}) ([]byte, error) { ... }
```

### `internal/api/tasks.go` (modified)

```go
type updateTaskStatusRequest struct {
	Status string `json:"status"`
}

// UpdateTaskStatus sets the status of a task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTaskStatus(taskID string, teamID string, status string) (*models.Task, error) { ... }

// Sets custom_task_ids=true and team_id when taskID is a custom ID.
func setCustomTaskIDParams(query url.Values, taskID string, teamID string) { ... }
```

`GetTask` (`api/tasks.go:66-70`) and `GetTaskComments` (`api/comments.go:17-20`) switch to `setCustomTaskIDParams`.

### `internal/api/lists.go` (new)

```go
package api

// GetList gets a list including its statuses
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

### `pkg/models/list.go` (new)

```go
package models

// List represents a ClickUp list
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the list status matching name, ignoring case
// (and surrounding whitespace). Returns the list's own spelling.
func (l *List) FindStatus(name string) (Status, bool) { ... }
```

### `internal/output/table.go` (modified)

Delete the duplicate `FormatComments` (lines 237-281). No new output code.

### Docs (modified)

- `README.md` "Tasks": add the command.
- `skills/SKILL.md`: new "Change Task Status" block; add "set task status", "move task to" to the `description` triggers; tell the skill to show the valid statuses to the user when the CLI rejects a status.

## Data

| Type | Status | Fields | Crosses |
|------|--------|--------|---------|
| `models.List` | new | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON -> `api.GetList` -> command |
| `models.Status` | reused (`task.go:55`) | `ID`, `Status`, `Color`, `Type`, `Orderindex int` | inside `List`/`Task`; `FindStatus` -> command |
| `api.updateTaskStatusRequest` | new, unexported | `Status string` | `UpdateTaskStatus` -> HTTP body |
| `models.Task` | unchanged | reads `List.ID`, `Status.Status` | `GetTask` / `UpdateTaskStatus` -> command |

No config, schema or migration changes.

## Call chain - `clickup tasks status <id> <status...>`

1. Cobra -> `runTasksStatus(cmd, args): error`
2. `runTasksStatus` -> `changeTaskStatus(args[0], strings.Join(args[1:], " ")): error` (after `getAPIClient()`, `getConfig()`; their errors return as-is, like `getTask`)
3. `changeTaskStatus` -> `api.Client::GetTask(taskID, cfg.WorkspaceID): (*models.Task, error)` -> `GET /task/{id}`
   - E1: error -> `fmt.Errorf("failed to get task: %w", err)`
4. `changeTaskStatus` -> `api.Client::GetList(task.List.ID): (*models.List, error)` -> `GET /list/{id}`
   - E2: error -> `fmt.Errorf("failed to get statuses of list %q: %w", task.List.Name, err)`
5. `changeTaskStatus` -> `models.List::FindStatus(statusName): (models.Status, bool)`
   - E3: not found -> `invalidStatusError(statusName, list)`; no PUT. User sees:
     ```
     Error: "done" is not a status of list "Sprint 12". Valid statuses:
       to do
       in progress
       review
       complete
     ```
6. `strings.EqualFold(task.Status.Status, status.Status)` -> `fmt.Printf("%s is already %q\n", task.GetDisplayID(), status.Status)`; return nil (no PUT)
7. `changeTaskStatus` -> `api.Client::UpdateTaskStatus(taskID, cfg.WorkspaceID, status.Status): (*models.Task, error)` -> `Client::Put("/task/{id}", query, updateTaskStatusRequest{...}): ([]byte, error)` -> `PUT /task/{id}`
   - E4: error -> `fmt.Errorf("failed to update task status: %w", err)`
8. `fmt.Printf("%s: %s -> %s\n", updated.GetDisplayID(), task.Status.Status, updated.Status.Status)`; return nil

All errors come back up to `Execute`, which prints `Error: %v` and exits 1. If there are too few arguments, Cobra rejects the command with `requires at least 2 arg(s)` before any API call.

## Test seams

- `pkg/models/list_test.go` - unit: `FindStatus` table test (exact, different case, padded, missing, empty list); `List` unmarshals `statuses`.
- `internal/api/tasks_test.go` - in-package `httptest.Server` (set `baseURL`): `UpdateTaskStatus` sends PUT with `{"status":"in progress"}`, custom-ID params only for `HGAI-1217`, decodes the task, 400 becomes `*APIError`; `GetTask` query unchanged after the helper refactor.
- `internal/api/lists_test.go` - `httptest.Server`: `GetList` path and statuses in order.
- `internal/commands/tasks_status_test.go` - unit: `invalidStatusError` message and order. The flow itself is covered only by E2E.
- E2E, real workspace, `make run ARGS="tasks status ..."`: valid, different case, unquoted multi-word, invalid, unchanged, custom and native ID, subtask, list inheriting folder statuses. Then `make check` and `make build-all`.

## Assumptions

1. Matching ignores case and surrounding whitespace; the list's spelling is sent and printed.
2. On a wrong status: exit 1, the list name in the message, valid statuses one per line in list order, no update sent.
3. `GET /list/{id}` returns the statuses the list actually uses, including any inherited from its folder or space (check this in the E2E run).
4. Setting the status the task already has: no PUT, prints `<ID> is already "<status>"`, exits 0.
5. Closed or done-type statuses are allowed; no confirmation prompt.
6. No `--output json` on this subcommand; `-o` stays local to `tasks`.
7. Works with custom and native IDs and the aliases `task status` / `t status`.
8. Subtasks are validated against their own list.
9. A native task with the literal ID `status` can no longer be viewed via `clickup tasks status`; accepted.
10. `bin/` binaries rebuilt with `make build-all`.
11. `FormatComments` duplicate fixed first, in its own commit.

## Decisions made during review

- Approach A (command orchestrates, matching on `models.List`); no service layer.
- Success output is one line: `HGAI-1217: to do -> in progress`.
- Multi-word statuses work without quotes: `MinimumNArgs(2)`, join `args[1:]` with a space.
