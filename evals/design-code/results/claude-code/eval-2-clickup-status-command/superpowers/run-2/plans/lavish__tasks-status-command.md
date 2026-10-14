# Design: `clickup tasks status <id> <status>`

Path: bounded. Status: approved (2026-10-01), including the debug-to-stderr commit.

## Goal

Change a task's status from the CLI. Validate the requested status against the statuses of the task's own list. On a mismatch, show the valid statuses and change nothing.

## Agreed decisions

- Matching: exact, case-insensitive (surrounding whitespace trimmed). No prefix or fuzzy matching.
- Invalid status: exit non-zero, no update call, list the valid statuses in list order.
- Send ClickUp's canonical status name, not the user's spelling.
- Already in the target status: no update call, print a note, exit 0.
- Success prints one line: `HGAI-1217: in progress -> review`.
- README and `skills/SKILL.md` document the new command.

## Flow

1. `GET /task/{id}` (with `custom_task_ids` + `team_id` for custom IDs) - current status and `list.id`.
2. `GET /list/{list_id}` - the list's effective statuses (includes inherited folder/space statuses).
3. Match locally. Invalid -> error with valid statuses. Same as current -> note.
4. `PUT /task/{id}` with body `{"status": "<canonical>"}` (same custom ID query params).

## Changes

| File | Change |
|---|---|
| `internal/api/client.go` | `doRequest` takes an optional `payload any`, JSON-marshalled into the request body. `Get` passes nil. New `Put(path, query, payload)`. |
| `internal/api/tasks.go` | Extract `taskIDQuery(taskID, teamID)` for the custom-ID params, reused by `GetTask`, `GetTaskComments`, new `UpdateTaskStatus`. Add `UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)`. |
| `internal/api/comments.go` | Use `taskIDQuery`. |
| `internal/api/lists.go` (new) | `GetList(listID string) (*models.List, error)`. |
| `pkg/models/list.go` (new) | `List{ID, Name, Statuses []Status}`, `FindStatus(name) (Status, bool)`, `StatusNames() []string` (sorted by `Orderindex`). |
| `internal/commands/tasks_status.go` (new) | `tasksStatusCmd` (`status <task_id> <status>`, `cobra.ExactArgs(2)`), registered on `tasksCmd`. `invalidStatusError(name, list)` builds the error text. |
| `internal/commands/tasks.go`, `root.go` | Add the command to help examples. |
| `README.md`, `skills/SKILL.md` | Document the command; add "change status" triggers to the skill description. |

### Command logic

```go
func runTasksStatus(cmd *cobra.Command, args []string) error {
	taskID, name := args[0], args[1]
	// getAPIClient, getConfig
	task, err := client.GetTask(taskID, cfg.WorkspaceID)   // "failed to get task: %w"
	list, err := client.GetList(task.List.ID)              // "failed to get list: %w"
	target, ok := list.FindStatus(name)
	if !ok {
		return invalidStatusError(name, list)
	}
	id := task.GetDisplayID()
	if strings.EqualFold(task.Status.Status, target.Status) {
		fmt.Printf("%s is already %s\n", id, target.Status)
		return nil
	}
	// UpdateTaskStatus(taskID, cfg.WorkspaceID, target.Status)  // "failed to update status: %w"
	fmt.Printf("%s: %s -> %s\n", id, task.Status.Status, target.Status)
	return nil
}
```

### Output

```
$ clickup tasks status HGAI-1217 Review
HGAI-1217: in progress -> review

$ clickup tasks status HGAI-1217 review
HGAI-1217 is already review

$ clickup tasks status HGAI-1217 rev
Error: invalid status "rev" for list "Sprint 12"
Valid statuses:
  to do
  in progress
  review
  complete
```

Multi-word statuses must be quoted (`"in progress"`). With `ExactArgs(2)`, unquoted input fails with Cobra's arg-count error, never a wrong match.

## Error handling

| Case | Behavior |
|---|---|
| Wrong arg count | Cobra usage error, exit 1 |
| Task not found / no access | `failed to get task: API error (status 404) ...` |
| List fetch fails | `failed to get list: ...` - no update attempted |
| Unknown status | Error with valid statuses, no update |
| Already in status | Note, exit 0, no update |
| PUT fails | `failed to update status: ...` |

## Testing (TDD)

- `pkg/models/list_test.go`: `FindStatus` matches case-insensitively, trims whitespace, returns canonical name, rejects prefixes; `StatusNames` sorts by `Orderindex`.
- `internal/api/tasks_test.go` and `lists_test.go` (`httptest` server, set unexported `baseURL` in-package): `UpdateTaskStatus` sends `PUT /task/{id}`, JSON body `{"status":"review"}`, `Content-Type: application/json`, custom-ID query params for `HGAI-1217` and none for `86a3xyzw`; `GetList` parses statuses; 4xx returns `*APIError`.
- `internal/commands/tasks_status_test.go`: `invalidStatusError` text.
- `make check` green.
- E2E with `make build` against a real workspace: valid change (wrong case), invalid name, same status, custom ID and native ID; confirm in the ClickUp UI.

## Adjacent fix (separate commit, approved)

`--debug` writes to stdout via `fmt.Printf` (`internal/api/client.go:49,72,74`), which corrupts `--output json` and would mix with the new success line. Move debug output to stderr.

## Commit sequence

1. `api`: request body support, `Put`, `taskIDQuery` refactor.
2. `models`: `List`, `FindStatus`, `StatusNames`.
3. `api`: `GetList`, `UpdateTaskStatus`.
4. `commands`: `tasks status` subcommand.
5. Docs: README, SKILL.md.
6. `api`: debug output to stderr.

## Risks

- A task ID literally named `status` can no longer be viewed via `clickup tasks status` - not a realistic ID.
- `tasks --status` (filter flag) and `tasks status` (subcommand) are similar names; help text examples make the distinction clear.
