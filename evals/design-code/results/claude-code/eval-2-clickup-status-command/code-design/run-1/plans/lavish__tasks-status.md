# `clickup tasks status <id> <status>` - code design

Review page: [.lavish/tasks-status-implementation.html](tasks-status-implementation.html)

## Decision

Approach A: a new `tasks status` Cobra subcommand orchestrates fetch task -> fetch its list -> match -> update. The API client gets thin endpoint methods; the matching rule lives on the models.

- Everything after the task ID is joined into one status (`clickup tasks status HGAI-1217 in progress` works unquoted).
- Matching: exact, case-insensitive, surrounding whitespace trimmed. No prefix or fuzzy matching.
- Success: one line `HGAI-1217: open -> in progress`; with `-o json` the updated task as JSON.
- Already in that status: notice on stderr in every output mode, no write, exit 0. With `-o json`, stdout additionally gets the current task as JSON.
- Invalid status: error listing the valid statuses in board order, exit 1, no write.
- No confirmation prompt.

## Commit 0 - prerequisite

`main` does not compile: `DetailFormatter.FormatComments` is declared twice. Delete the older, non-wrapping copy at `internal/output/table.go:238-279`; keep the one at `:191`. Commit separately.

## Units

### `internal/commands/tasks_status.go` (new)

```go
var statusOutputFormat string

var tasksStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change a task's status. The status must exist in the task's list.

Examples:
  clickup tasks status HGAI-1217 in progress    Move task to "in progress"
  clickup tasks status HGAI-1217 done -o json   Print the updated task as JSON`,
	Args: cobra.MinimumNArgs(2),
	RunE: runTasksStatus,
}

func init() {
	tasksCmd.AddCommand(tasksStatusCmd)

	tasksStatusCmd.Flags().StringVarP(&statusOutputFormat, "output", "o", "", "output format (table, json)")
}

// runTasksStatus joins all args after the task ID into one status name
func runTasksStatus(cmd *cobra.Command, args []string) error { ... }

// changeTaskStatus validates statusName against the task's list and updates the task
func changeTaskStatus(out io.Writer, errOut io.Writer, taskID string, statusName string) error { ... }

// invalidStatusError lists the list's valid statuses in board order
func invalidStatusError(statusName string, list *models.List) error { ... }

// printStatusChange prints "ID: from -> to", or the updated task as JSON
func printStatusChange(out io.Writer, task *models.Task, from string) error { ... }

// printStatusUnchanged writes the already-set notice to errOut, plus the task as JSON to out with -o json
func printStatusUnchanged(out io.Writer, errOut io.Writer, task *models.Task) error { ... }
```

- `runTasksStatus`: `args[0]` is the ID; `strings.TrimSpace(strings.Join(args[1:], " "))` is the status; blank -> `status must not be empty`. Calls `changeTaskStatus(cmd.OutOrStdout(), cmd.ErrOrStderr(), ...)`.
- `printStatusChange` / `printStatusUnchanged`: JSON via `output.GetFormatter(output.FormatJSON).FormatTask`; any non-`json` value of `-o` prints text.

### `internal/api/tasks.go` (modified)

```go
// updateTaskRequest is the request body for updating a task
type updateTaskRequest struct {
	Status string `json:"status"`
}

// UpdateTaskStatus sets a task's status and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTaskStatus(taskID string, teamID string, status string) (*models.Task, error) { ... }

// addCustomTaskIDParams adds the query params ClickUp needs to resolve custom task IDs
func addCustomTaskIDParams(query url.Values, taskID string, teamID string) { ... }
```

- `UpdateTaskStatus`: `PUT /task/{id}` with `updateTaskRequest`, decodes response into `models.Task`.
- `GetTask` (`:66-70`) and `GetTaskComments` (`comments.go:17-20`) switch to `addCustomTaskIDParams`; behaviour unchanged.

### `internal/api/lists.go` (new)

```go
// GetList gets a list, including the statuses available to its tasks
func (c *Client) GetList(listID string) (*models.List, error) { ... }
```

`GET /list/{id}`; returns effective statuses (including inherited ones).

### `internal/api/client.go` (modified)

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

`Get` passes `nil` payload. `--debug` also prints the request body.

### `pkg/models/list.go` (new)

```go
// List represents a ClickUp list with the statuses its tasks can have
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the status matching name, or nil if the list has none
func (l *List) FindStatus(name string) *Status { ... }

// OrderedStatuses returns the statuses sorted by board order
func (l *List) OrderedStatuses() []Status { ... }
```

`OrderedStatuses` sorts a copy by `Orderindex`; does not mutate the receiver.

### `pkg/models/task.go` - `Status` (modified)

```go
// Matches reports whether name refers to this status, ignoring case and surrounding whitespace
func (s Status) Matches(name string) bool { ... }
```

`strings.EqualFold` after `strings.TrimSpace` on both sides. Single rule used by `FindStatus` and the already-set check.

### Small edits

- `internal/commands/tasks.go`: add `clickup tasks status HGAI-1217 in progress` to `Long` examples.
- `internal/commands/root.go`: add `clickup tasks status <ID> <status>` to "Get started".
- `skills/SKILL.md`, `README.md`: "Change Task Status" section; add "change status" / "move task to" to the skill `description` triggers.

## Data

| Type | Fields | Crosses |
|---|---|---|
| `models.List` (new) | `ID string`, `Name string`, `Statuses []Status` | ClickUp JSON -> api -> commands |
| `models.Status` (+`Matches`) | unchanged | inside Task and List |
| `api.updateTaskRequest` (new, unexported) | `Status string` json `status` | api -> ClickUp PUT body |
| `models.Task` | unchanged; PUT response decodes into it | ClickUp -> api -> commands -> JSON output |

## Call chains

### Status changes: `clickup tasks status HGAI-1217 in progress`

1. cobra -> runTasksStatus(cmd, ["HGAI-1217", "in", "progress"]): error
2. runTasksStatus -> changeTaskStatus(cmd.OutOrStdout(), cmd.ErrOrStderr(), "HGAI-1217", "in progress"): error
3. changeTaskStatus -> getAPIClient(): (*api.Client, error); getConfig(): (*config.Config, error)
4. changeTaskStatus -> Client::GetTask("HGAI-1217", cfg.WorkspaceID): (*models.Task, error)
5. changeTaskStatus -> Client::GetList(task.List.ID): (*models.List, error)
6. changeTaskStatus -> List::FindStatus("in progress"): *models.Status
7. changeTaskStatus -> Status::Matches(match.Status) on task.Status: bool (false)
8. changeTaskStatus -> Client::UpdateTaskStatus("HGAI-1217", cfg.WorkspaceID, match.Status): (*models.Task, error) -> Client::Put("/task/HGAI-1217", query, updateTaskRequest{Status}): ([]byte, error) -> Client::doRequest("PUT", path, query, payload): ([]byte, error)
9. changeTaskStatus -> printStatusChange(out, updated, task.Status.Status): error -> `HGAI-1217: open -> in progress` or updated task JSON. Exit 0.

### Invalid status

1-6. As above; FindStatus returns nil.
7. changeTaskStatus -> invalidStatusError("in progres", list): error -> List::OrderedStatuses(): []models.Status
8. Execute prints to stderr, exit 1, no PUT:

```
Error: status "in progres" does not exist in list "Sprint 12". Valid statuses:
  open
  in progress
  review
  done
```

### Already in that status

1-6. As above.
7. changeTaskStatus -> Status::Matches(match.Status) on task.Status: bool (true)
8. changeTaskStatus -> printStatusUnchanged(out, errOut, task): error -> errOut: `HGAI-1217 is already in progress, nothing changed`; with `-o json` also current task JSON on out. Exit 0, no PUT.

### Error paths (stderr via Execute, exit 1)

| Fails at | Returned | User sees |
|---|---|---|
| cobra args (< 2) | cobra error | `Error: requires at least 2 arg(s), only received 1` |
| runTasksStatus, blank status | `fmt.Errorf` | `Error: status must not be empty` |
| step 3 config | config error, passed through | same as `clickup tasks` today |
| step 4 GetTask | `failed to get task: %w` (`*APIError`) | `Error: failed to get task: API error (status 404): ...` |
| step 5 GetList | `failed to get list statuses: %w` | `Error: failed to get list statuses: API error (...)` |
| step 8 UpdateTaskStatus | `failed to update task status: %w` | `Error: failed to update task status: API error (...)` |

## Test seams

- `pkg/models/list_test.go`: table tests for `Status.Matches` (case, whitespace, "in" does not match "in progress"), `FindStatus` (hit and nil), `OrderedStatuses` (sorted, receiver unchanged); decode a `GET /list` JSON fixture.
- `internal/api/tasks_test.go`, `lists_test.go`: `httptest.Server` + `SetBaseURL`; assert method, path, custom-ID query params, PUT JSON body, 4xx -> `*APIError`.
- `internal/commands/tasks_status_test.go`: fake ClickUp `httptest.Server`; set/reset globals `cfg`, `apiClient`, `statusOutputFormat`; call `changeTaskStatus` with separate `bytes.Buffer`s for out/errOut. Cases: change; invalid (no PUT, message and order); unchanged (no PUT, notice in errOut); unchanged + `-o json` (notice in errOut, only valid JSON in out); change + `-o json`.
- E2E before committing: `make run ARGS="tasks status <sandbox task> ..."` against a real ClickUp list for all three outcomes and a custom ID.

## Assumptions

1. Valid statuses come from the task's home list (`task.List.ID`), even if the task also appears in other lists.
2. The PUT sends the list's own spelling of the status (`match.Status`), not the typed input.
3. The already-set notice always goes to stderr (like existing warnings); with `-o json` the current task also goes to stdout.
4. `-o` on `status` only switches on `json`; any other value prints the one-line text.
5. Invalid-status error lists one status per line, two-space indent, board order, names only.
6. Closed/done statuses are valid targets, no extra warning.
7. `--debug` also prints the PUT request body.
8. On ship, `make build-all` refreshes the pre-built binaries in `bin/`.

## Decisions made during review

- Already-set notice is shown in every output mode, on stderr, so `-o json` stdout stays valid JSON. This required `changeTaskStatus` and `printStatusUnchanged` to take separate `out` and `errOut` writers.
