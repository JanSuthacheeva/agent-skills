# Plan: `clickup tasks status <id> <status>`

## Goal

Let users change a task's status from the terminal. The requested status is validated against the statuses of the task's home list. If it is wrong, the command fails and lists the valid statuses in workflow order.

```
$ clickup tasks status HGAI-1217 review
HGAI-1217: in progress -> review

$ clickup tasks status HGAI-1217 revew
Error: invalid status "revew" for list "Sprint 42"
Valid statuses: to do, in progress, review, complete
```

## Current state (verified)

- `tasksCmd` (`internal/commands/tasks.go`) is `tasks [task_id]` with `cobra.MaximumNArgs(1)` and local flags only (`--status`, `--output`, ...). It has no subcommands yet.
- `api.Client` only exposes `Get`. `doRequest(method, path, query)` sends no request body (`internal/api/client.go:43`).
- Custom task ID handling (`isCustomTaskID` + `custom_task_ids`/`team_id` query) is duplicated in `GetTask` and `GetTaskComments`.
- `models.Task.List` is `ListInfo{ID, Name, Access}`. `models.Status` already exists.
- There are no tests for `internal/api` or `internal/commands`.

## Approach

### Flow

1. `GetTask(id, workspace)` - resolves custom IDs, gives current status and `list.id`.
2. `GetList(task.List.ID)` - returns the list's effective `statuses` (ClickUp resolves list/folder/space inheritance server-side).
3. `list.FindStatus(input)` - case-insensitive, whitespace-trimmed match.
   - No match: return an error listing valid statuses (by `orderindex`). No write happens.
   - Same as current status: print `HGAI-1217 is already "review"` and exit 0 without a write.
4. `UpdateTaskStatus(id, workspace, canonical)` - `PUT /task/{id}` with `{"status": "<canonical>"}`.
5. Print `HGAI-1217: in progress -> review` (or the updated task as JSON with `-o json`).

The canonical name from the list is sent, not the raw user input, so `clickup tasks status X "In Progress"` works regardless of casing.

### Command shape

`status` becomes a Cobra subcommand of `tasksCmd`. Cobra matches subcommand names before falling back to the parent's positional arg, so `clickup tasks HGAI-1217` is unaffected (parent has explicit `Args`, so legacy arg validation does not apply). The parent's flags are local, so `--status`, `--closed` etc. do not leak into the subcommand.

`Args: cobra.MinimumNArgs(2)` and the status is `strings.Join(args[1:], " ")`, so both `clickup tasks status X in progress` and `clickup tasks status X "in progress"` work. The ID is always the first arg, so this is unambiguous.

### Changes by file

| File | Change |
|---|---|
| `internal/api/client.go` | `doRequest` gains a `payload any` param; marshals JSON body when non-nil. Add `Put(path, query, payload)`. `Get` passes `nil`. |
| `internal/api/tasks.go` | Extract `taskIDQuery(taskID, teamID) url.Values` (custom ID handling), use it in `GetTask`, `GetTaskComments`, new `UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)`. |
| `internal/api/lists.go` (new) | `GetList(listID string) (*models.List, error)` - `GET /list/{id}`. |
| `pkg/models/list.go` (new) | `List{ID, Name, Statuses []Status}`, `FindStatus(name) (Status, bool)`, `StatusNames() []string` sorted by `Orderindex`. |
| `internal/commands/tasks_status.go` (new) | `tasksStatusCmd`, registered via `tasksCmd.AddCommand` in `init()`. Supports `-o json`. |
| `internal/commands/tasks.go` | Add `clickup tasks status HGAI-1217 review` to the `Long` examples. |
| `internal/commands/root.go` | Add the status command to the root `Long` help. |
| `README.md`, `skills/SKILL.md` | Document the command. Update the skill description/triggers ("move task to", "set status", "mark as done") and add a guideline: never guess a status, run the command and show the valid list on error. |
| `bin/*` | `make build-all` to refresh pre-built binaries (as done in the previous feature). |

### Sketches

```go
// pkg/models/list.go
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
```

```go
// internal/commands/tasks_status.go (core of RunE)
task, err := client.GetTask(taskID, cfg.WorkspaceID)
list, err := client.GetList(task.List.ID)

target, ok := list.FindStatus(want)
if !ok {
	return fmt.Errorf("invalid status %q for list %q\nValid statuses: %s",
		want, list.Name, strings.Join(list.StatusNames(), ", "))
}
if strings.EqualFold(task.Status.Status, target.Status) {
	fmt.Printf("%s is already %q\n", task.GetDisplayID(), target.Status)
	return nil
}
updated, err := client.UpdateTaskStatus(taskID, cfg.WorkspaceID, target.Status)
fmt.Printf("%s: %s -> %s\n", task.GetDisplayID(), task.Status.Status, updated.Status.Status)
```

## Testing (TDD, `make check`)

- `pkg/models/list_test.go`: exact, case-insensitive, whitespace-padded matches; no match; `StatusNames` ordering by `orderindex`.
- `internal/api/*_test.go` with `httptest.Server` (client `baseURL` is already a field): `GetList` path and decoding; `UpdateTaskStatus` uses `PUT`, sends `{"status":...}` body, sets `custom_task_ids`/`team_id` for custom IDs only; `Get` still sends no body.
- `internal/commands/tasks_status_test.go`: run the command against an `httptest` ClickUp fake, assert (a) invalid status -> error with valid list and **no PUT**, (b) same status -> no PUT, (c) success -> one PUT with canonical casing, (d) `clickup tasks HGAI-1217` still routes to the detail view. Requires a small seam: make the API base URL overridable (e.g. `api.NewClient` option or package var set in tests).
- Manual E2E against a real workspace: valid move, wrong casing, typo, multi-word unquoted, subtask, custom ID and native ID.

## Risks and edge cases

- **Tasks in multiple lists**: `task.list` is the home list, whose statuses govern the task. Correct by design.
- **Race**: list statuses could change between GET and PUT. ClickUp rejects the PUT; surface its error as-is. Acceptable.
- **Extra API call**: 3 requests per change (task, list, update). Negligible for an interactive command; no caching.
- **Typo of subcommand** (`clickup tasks stauts X y`): falls through to the parent and fails with "accepts at most 1 arg(s), received 3". Pre-existing Cobra behaviour, but worth a friendlier message if cheap.
- **Debug output** goes to stdout (`client.go`), which pollutes `-o json`. Pre-existing; fix to stderr while touching `doRequest`.
- **`list.Access == false`**: `GET /list` may 401; surface as `failed to load statuses for list ...`.

## Decisions (approved)

1. Unquoted multi-word statuses are accepted (`... status X in progress`).
2. No "did you mean" suggestion for now; the full valid list is shown instead.
3. Success output is one line `ID: old -> new`; `-o json` prints the updated task.
