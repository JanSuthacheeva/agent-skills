# Plan: `clickup tasks status <id> [status]`

Status: approved (approach B).

## Goal

Change a task's status from the CLI, validated against the statuses of the task's list. With no status given, print the valid statuses.

```
$ clickup tasks status HGAI-1217 "in review"
HGAI-1217: to do -> in review

$ clickup tasks status HGAI-1217
to do (current)
in progress
in review
complete

$ clickup tasks status HGAI-1217 reveiw
Error: invalid status "reveiw" for list "Sprint 12". Valid statuses:
  to do (current)
  in progress
  in review
  complete

$ clickup tasks status HGAI-1217 "In Review"     # already in that status
HGAI-1217 is already "in review"

$ clickup tasks status HGAI-1217 -o json
[
  "to do",
  "in progress",
  "in review",
  "complete"
]
```

## Decisions (confirmed)

| Topic | Decision |
|---|---|
| Matching | Case-insensitive exact match (`strings.EqualFold`, trimmed). The list's spelling is sent to the API. No fuzzy or prefix matching. |
| Invalid status | Error on stderr, exit 1, statuses in board order (`orderindex`), names only, current one marked `(current)`. |
| No status argument | Print the valid statuses (same list format) to stdout, exit 0. With `-o json`, print a JSON array of the names in board order: `["to do", "in progress", "in review", "complete"]`. |
| Already in the target status | Print the notice, skip the `PUT`, exit 0. |
| Success output | `HGAI-1217: to do -> in review`. With `-o json`, print the updated task returned by the `PUT`. |
| Side fixes | Compile fix and shared custom-ID query helper as separate commits. `--debug` is out of scope. |
| Docs and binaries | Update README, `skills/SKILL.md` and help text, then run `make build-all`. |

## Current state (verified)

- `main` does not compile: `DetailFormatter.FormatComments` is declared twice in `internal/output/table.go` (lines 191 and 238). It's left over from merge `7411557`. The second copy is the old one without word wrapping.
- `tasksCmd` is `tasks [task_id]` with `cobra.MaximumNArgs(1)` (`internal/commands/tasks.go:24`). A `status` subcommand is matched before parent arguments, so `tasks <id>` keeps working, and the `task`/`t` aliases still apply.
- `api.Client.doRequest` (`internal/api/client.go:42`) always sends a nil body. Only `Get` exists.
- The custom-ID query (`custom_task_ids` + `team_id`) is duplicated in `GetTask` and `GetTaskComments`.
- `models.Task.List.ID` is already returned by `GetTask`. `models.Status` exists; there's no list model with statuses.
- ClickUp API (checked against developer.clickup.com):
  - `GET /list/{list_id}` returns `statuses[]` with `status`, `orderindex`, `color`, `type` (no `id`).
  - `PUT /task/{task_id}` with body `{"status": "..."}` takes the same `custom_task_ids`/`team_id` query and returns the full updated task.

## Flow

1. `GetTask(id, workspace)`: current status and `list.id`.
2. `GetList(list.id)`: the list's effective statuses, sorted by `orderindex`.
3. No status argument: print the list and stop.
4. `FindStatus(arg)`: no match is an error that includes the list. If it's the current status, print the notice and stop.
5. `UpdateTask(id, workspace, {Status: canonical})`: print `from -> to`, or the JSON task.

That's 3 API calls on the change path and 2 on the list and no-op paths.

## Approaches considered

- **A. Minimal**: everything in the command file (an inline `map[string]string` body, string-built list, a `strings.EqualFold` loop). Fewest files, but the logic can't be tested without the CLI, and output formatting ends up in `commands`.
- **B. Layered, following existing packages (chosen)**: API methods in `api`, status lookup and ordering on a `models.List`, list rendering in `output`, and a thin command. Every piece can be tested on its own, and it fits the package structure described in CLAUDE.md.
- **C. Status service with a cache**: cache list statuses in config to save a call. That's premature: staleness bugs for one saved request.

## Commits

### 1. `fix(output): remove duplicated FormatComments from merge`
- Delete the stale second `DetailFormatter.FormatComments` (`internal/output/table.go:237-281`). Keep the word-wrapping version.
- Run `make check` to confirm build, vet and existing tests are green.

### 2. `refactor(api): share custom task ID query params`
- Add `func taskQuery(taskID, teamID string) url.Values` to `internal/api/tasks.go`. It returns `custom_task_ids=true&team_id=...` when `isCustomTaskID(taskID) && teamID != ""`, otherwise empty `url.Values{}`.
- `GetTask` starts from `taskQuery(...)` and adds `include_subtasks` and `include_markdown_description`. `GetTaskComments` uses it directly.
- New `internal/api/tasks_test.go` with a table test: native ID, custom ID with team, and custom ID without team.

### 3. `feat(api): add GetList and UpdateTask`
- `client.go`:
  - `doRequest(method, path string, query url.Values, payload any)`: when `payload != nil`, `json.Marshal` it into a `bytes.Reader`.
  - `Get` passes `nil`.
  - Add `Put(path, query, payload)`.
  - Add `SetBaseURL(url string)` (next to `SetDebug`) as a test seam.
- New `pkg/models/list.go`:
  ```go
  type List struct {
      ID       string   `json:"id"`
      Name     string   `json:"name"`
      Statuses []Status `json:"statuses"`
  }
  func (l *List) OrderedStatuses() []Status         // sorted copy by Orderindex
  func (l *List) FindStatus(name string) (Status, bool) // EqualFold on trimmed name
  ```
- New `internal/api/lists.go`: `GetList(listID string) (*models.List, error)`.
- `internal/api/tasks.go`:
  ```go
  type TaskUpdate struct {
      Status string `json:"status,omitempty"`
  }
  func (c *Client) UpdateTask(taskID, teamID string, update *TaskUpdate) (*models.Task, error)
  ```
  This mirrors `ListTasksOptions`, and later fields (name, priority, assignees) slot in without changing the signature.
- Tests:
  - `pkg/models/list_test.go`: ordering and case-insensitive matching.
  - `internal/api/client_test.go` with `httptest.Server`: method, path, query, JSON body and auth header for `PUT /task/...` and `GET /list/...`, plus `APIError` on a 4xx response.

### 4. `feat(commands): add tasks status subcommand`
- `internal/output/json.go`: export `WriteJSON(w io.Writer, data interface{}) error`. `JSONFormatter`'s private `writeJSON` is replaced by it, so the indentation stays the same everywhere.
- New `internal/output/statuses.go`:
  - `WriteStatusList(w io.Writer, statuses []models.Status, current string, indent string)` writes one name per line and marks the current one with ` (current)` (case-insensitive compare).
  - It's used by the stdout listing (no indent) and inside the error message (two-space indent).
- New `internal/commands/tasks_status.go`:
  - `Use: "status <task_id> [status]"`, `Args: cobra.RangeArgs(1, 2)`, registered with `tasksCmd.AddCommand(tasksStatusCmd)` in its own `init()`.
  - Own flag `-o/--output` (table, json).
  - Multi-word statuses must be quoted, the same as `--status "in progress"`.
  - Writes to `cmd.OutOrStdout()` so it can be tested.
  - Errors are wrapped like existing code: `failed to get task: %w`, `failed to get list: %w`, `failed to update status: %w`.
  - A list with zero statuses is an error: `list "X" has no statuses`.
  - No-op with `-o json`: print the unchanged task JSON on stdout and the notice on stderr, so JSON consumers always get a task object.
  - Listing with `-o json`: `output.WriteJSON` with the ordered names (`[]string`), so `-o json` always means JSON. There's no current marker; the current status is in the task JSON.
- `internal/commands/tasks_status_test.go`: a fake ClickUp `httptest.Server`, with `apiClient` and `cfg` injected through the package globals and the command run via `rootCmd.SetArgs`. Cases:
  - change succeeds (asserts the canonical name was sent in the `PUT`)
  - case-insensitive input
  - invalid status (error text includes the ordered list with the current one marked)
  - no status argument
  - no status argument with `-o json` (asserts a JSON array of names in board order)
  - already in that status (asserts no `PUT`)
  - `-o json`
  - custom ID query propagated

### 5. `docs: document tasks status command`
- `tasksCmd.Long` examples and `rootCmd.Long` "Get started" list.
- `README.md` usage block.
- `skills/SKILL.md`: add "Change Task Status" section, extend the `description` triggers ("change task status", "move task to", "mark as done"), and tell Claude to run `clickup tasks status <id>` first when unsure of the valid names.

### 6. `build: update pre-built binaries`
- `make check`, then `make build-all` (5 binaries in `bin/`).

## Verification

- `make check` green after every commit.
- E2E against the real API with the built binary on a throwaway task you designate:
  - list the statuses, plain and with `-o json`
  - invalid status
  - valid change, with mixed case
  - no-op
  - `-o json`
  - both a custom ID (`HGAI-...`) and a native ID
- Confirm in the ClickUp UI that the status changed.

## Risks

- **Inherited statuses**: lists that don't override statuses inherit them from the folder or space. The docs show `GET /list` returns the effective set; the E2E run should include such a list.
- **Tasks in multiple lists**: `task.list` is the home list, and its statuses are the ones that govern the task. That's acceptable.
- **Race**: a status deleted between the `GET` and the `PUT` surfaces as an API error. That's fine.
- **Test isolation**: Cobra flag values persist on the package-level `rootCmd` between tests, so each test resets the flags it sets.
