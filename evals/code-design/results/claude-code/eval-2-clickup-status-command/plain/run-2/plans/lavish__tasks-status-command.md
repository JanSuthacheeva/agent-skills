# Plan: `clickup tasks status <id> <status>`

## Goal

Change a task's status from the CLI. The status is checked against the statuses of the task's own list. If it doesn't match, the command fails and prints the valid statuses.

```
$ clickup tasks status HGAI-1217 "in progress"
HGAI-1217: to do -> in progress

$ clickup tasks status HGAI-1217 done
Error: invalid status "done" for list "Sprint 12". Valid statuses:
  to do
  in progress
  review
  complete
```

## Current state (verified in code)

- `tasksCmd` (`internal/commands/tasks.go:24`) takes an optional positional `[task_id]` with `cobra.MaximumNArgs(1)` and has no subcommands yet.
- The API client is read-only. `doRequest` (`internal/api/client.go:42`) always sends a `nil` body, and only `Get` exists.
- `GetTask` (`internal/api/tasks.go:59`) already handles custom IDs like `HGAI-1217` via `custom_task_ids` + `team_id`. The returned task has the native `ID`, `Status`, and `List.ID`.
- `models.Status` already exists (`pkg/models/task.go:55`). There is no `List` model and no list endpoint.
- No `internal/api` tests exist yet. `Client.baseURL` is a field, so in-package tests can point it at `httptest.Server`.

## Flow

1. `GetTask(id, workspace)`: resolves custom or native ID, gives current status and `list.id`.
2. `GetList(list.id)`: `GET /list/{id}`, returns the list's effective `statuses` (inherited from folder/space when the list doesn't override them).
3. `list.FindStatus(input)`: case-insensitive, trimmed exact match.
   - No match: return an error listing the valid statuses, sorted by `orderindex`. Exit 1, no write.
   - Same as current status: print `HGAI-1217 is already "in progress"`. Exit 0, no write.
4. `UpdateTask(task.ID, {status})`: `PUT /task/{native id}`. We use the native ID from step 1, so no custom-ID query params are needed.
5. Print `HGAI-1217: to do -> in progress`.

## Design decisions

| Decision | Choice | Why |
|---|---|---|
| Command shape | `status` as a Cobra subcommand of `tasks` | Matches the requested syntax. Cobra resolves subcommands before positional args, so `clickup tasks HGAI-1217` still works. The `t` and `task` aliases also work (`clickup t status ...`). |
| Validation source | `GET /list/{id}` statuses | The list is the authority on statuses. The API also rejects bad statuses, but its error doesn't list the valid ones. |
| Matching | Case-insensitive exact, send canonical name | `In Progress` should work. No fuzzy/prefix matching - it's too risky for a write. |
| Write payload | Generic `UpdateTask(id, models.TaskUpdate)` with `Status string \`json:"status,omitempty"\`` | Matches the API resource. Adding assignee/priority later means adding a field, not a new method. |
| Request bodies | `doRequest(method, path, query, payload any)` JSON-marshals non-nil payloads; add `Put` | A single place for auth, debug and error handling. `Get` passes `nil`. |
| Status lookup location | `(*models.List).FindStatus(name) (Status, bool)` | A pure function that is easy to unit test and sits next to the data. |
| Command file | New `internal/commands/tasks_status.go` with its own `init()` | Follows the "commands register in init()" convention without making `tasks.go` bigger. |
| Output | One plain confirmation line, no `--output` flag | It's a mutation, so a short receipt is enough. `clickup tasks <id> -o json` already exists for reading. |

## File changes

### `internal/api/client.go` - support request bodies

```go
func (c *Client) doRequest(method, path string, query url.Values, payload any) ([]byte, error) {
	// ... build fullURL as today ...
	var reqBody io.Reader
	if payload != nil {
		data, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}
		reqBody = bytes.NewReader(data)
	}
	req, err := http.NewRequest(method, fullURL, reqBody)
	// ... rest unchanged ...
}

func (c *Client) Get(path string, query url.Values) ([]byte, error) {
	return c.doRequest(http.MethodGet, path, query, nil)
}

func (c *Client) Put(path string, query url.Values, payload any) ([]byte, error) {
	return c.doRequest(http.MethodPut, path, query, payload)
}
```

### `pkg/models/list.go` (new)

```go
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

func (l *List) FindStatus(name string) (Status, bool) {
	want := strings.TrimSpace(name)
	for _, s := range l.Statuses {
		if strings.EqualFold(s.Status, want) {
			return s, true
		}
	}
	return Status{}, false
}

// TaskUpdate is the request body for PUT /task/{id}  (in pkg/models/task.go)
type TaskUpdate struct {
	Status string `json:"status,omitempty"`
}
```

### `internal/api/lists.go` (new)

```go
func (c *Client) GetList(listID string) (*models.List, error) {
	body, err := c.Get(fmt.Sprintf("/list/%s", listID), nil)
	if err != nil {
		return nil, err
	}
	var list models.List
	if err := json.Unmarshal(body, &list); err != nil {
		return nil, err
	}
	return &list, nil
}
```

### `internal/api/tasks.go` - add `UpdateTask`

```go
// UpdateTask updates a task by its native ID
func (c *Client) UpdateTask(taskID string, update models.TaskUpdate) (*models.Task, error) {
	body, err := c.Put(fmt.Sprintf("/task/%s", taskID), nil, update)
	if err != nil {
		return nil, err
	}
	var task models.Task
	if err := json.Unmarshal(body, &task); err != nil {
		return nil, err
	}
	return &task, nil
}
```

### `internal/commands/tasks_status.go` (new)

```go
var taskStatusCmd = &cobra.Command{
	Use:   "status <task_id> <status>",
	Short: "Change a task's status",
	Long: `Change a task's status. The status must exist in the task's list.

Examples:
  clickup tasks status HGAI-1217 "in progress"
  clickup tasks status HGAI-1217 complete`,
	Args: cobra.MinimumNArgs(2),
	RunE: runTaskStatus,
}

func init() {
	tasksCmd.AddCommand(taskStatusCmd)
}

func runTaskStatus(cmd *cobra.Command, args []string) error {
	taskID := args[0]
	name := strings.Join(args[1:], " ")

	client, err := getAPIClient()
	if err != nil {
		return err
	}
	cfg, err := getConfig()
	if err != nil {
		return err
	}

	task, err := client.GetTask(taskID, cfg.WorkspaceID)
	if err != nil {
		return fmt.Errorf("failed to get task: %w", err)
	}
	list, err := client.GetList(task.List.ID)
	if err != nil {
		return fmt.Errorf("failed to get list: %w", err)
	}

	status, ok := list.FindStatus(name)
	if !ok {
		return invalidStatusError(name, list)
	}
	if strings.EqualFold(task.Status.Status, status.Status) {
		fmt.Printf("%s is already %q\n", task.GetDisplayID(), status.Status)
		return nil
	}

	if _, err := client.UpdateTask(task.ID, models.TaskUpdate{Status: status.Status}); err != nil {
		return fmt.Errorf("failed to update status: %w", err)
	}
	fmt.Printf("%s: %s -> %s\n", task.GetDisplayID(), task.Status.Status, status.Status)
	return nil
}

func invalidStatusError(name string, list *models.List) error {
	statuses := slices.Clone(list.Statuses)
	slices.SortFunc(statuses, func(a, b models.Status) int { return a.Orderindex - b.Orderindex })

	var b strings.Builder
	fmt.Fprintf(&b, "invalid status %q for list %q. Valid statuses:", name, list.Name)
	for _, s := range statuses {
		fmt.Fprintf(&b, "\n  %s", s.Status)
	}
	return errors.New(b.String())
}
```

### Docs

- `tasks.go` Long help: add the `clickup tasks status HGAI-1217 "in progress"` example.
- `root.go` Long help "Get started": add a `clickup tasks status <ID> <status>` line.
- `README.md` usage block: add the command.
- `skills/SKILL.md`: add a "Change Task Status" section, extend the `description` triggers ("move task to", "set status", "mark as done"), and add a rule to always confirm the task and target status before running it, since it's a write.
- `make build-all` to refresh the pre-built binaries in `bin/` (same as the previous feature).

## Tests

- `pkg/models/list_test.go`: `FindStatus` table test covering exact match, mixed case, surrounding whitespace, no match, and an empty list.
- `internal/api/client_test.go`: an `httptest.Server` checks that `Put` sends the method, `Content-Type`, auth header and JSON body, that `Get` still sends no body, and that 4xx responses map to `APIError`.
- `internal/api/lists_test.go`: `GetList` decodes `statuses` from a recorded-shape fixture.
- `internal/api/tasks_test.go`: `UpdateTask` sends `PUT /task/{id}` with `{"status":"..."}`.
- `internal/commands`: `invalidStatusError` output check, including `orderindex` ordering.
- `make check` must pass.

## E2E verification (real binary, real workspace)

Run `make build` and use the throwaway task Jan provides:

1. `bin/clickup tasks status <custom-id> "in progress"` changes the status. Confirm with `bin/clickup tasks <id>` and in the ClickUp UI.
2. Native ID works too.
3. `In Progress` (mixed case) matches, and the canonical name is sent.
4. Unquoted `in progress` (two args) matches.
5. An invalid status prints the list in board order, exits 1, and leaves the task unchanged.
6. Running it again with the current status prints "already" and makes no PUT (check with `--debug`).
7. A subtask in a list with custom statuses validates against that list.
8. `clickup tasks HGAI-1217` and `clickup tasks` behave exactly as before.

## Risks

- **Effective statuses from `GET /list/{id}`.** It should return inherited statuses when the list doesn't override them. E2E check 7 plus one list without an override covers this. If it turns out to be empty for inheriting lists, fall back to `GET /space/{task.space.id}` statuses.
- **A task literally named `status`.** It would be routed to the subcommand. ClickUp IDs never look like that, so this is acceptable.
- **`--debug` prints to stdout** (existing behavior). It won't print the request body. That's unchanged and out of scope.

## Resolved decisions

1. **Unquoted multi-word statuses:** join `args[1:]` (`cobra.MinimumNArgs(2)`), so `clickup tasks status X in progress` works.
2. **E2E test task:** Jan will provide a throwaway task when the E2E runs start.
