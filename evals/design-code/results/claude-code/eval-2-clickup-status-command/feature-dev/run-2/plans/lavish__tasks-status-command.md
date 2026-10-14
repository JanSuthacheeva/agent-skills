# Plan: `clickup tasks status <id> <status>`

## Goal

Change a task's status from the CLI. The status is checked against the statuses of the task's home list before writing. If it does not match, the command fails and lists the valid statuses.

## Decisions (confirmed)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Matching | Case-insensitive exact match, whitespace trimmed. No prefix matching. The list's own spelling is sent to the API. |
| 2 | Multi-word statuses | `cobra.ExactArgs(2)`, so multi-word statuses must be quoted: `"in progress"`. |
| 3 | Invalid status | Exit 1 with an error on stderr that lists valid statuses in list order (sorted by `orderindex`) and marks the current one with `(current)`. No color, no type. |
| 4 | Success output | One line: `HGAI-1217: to do -> in progress`. `--output json` prints the updated task returned by the PUT. |
| 5 | Same status | No PUT. Prints `HGAI-1217 is already "in progress"` and exits 0. With `--output json` it prints the task from the initial `GET /task` (there is no PUT response). Both cases print a `models.Task`, so the shape matches. The GET version also fills `subtasks` and `markdown_description`, because `GetTask` requests them. |
| 6 | Shell completion | Out of scope, possible follow-up. |
| 7 | Scope | Includes the build fix, sending `--debug` output to stderr, a shared custom-ID query helper, and updates to the README, `skills/SKILL.md` and root help. |
| 8 | Tests | `FindStatus` unit tests, `httptest` tests for the API layer, and command-level tests against a fake ClickUp server. |

## Current state

- **The build is broken on `main`.** Merge commit `7411557` left two copies of `DetailFormatter.FormatComments` in `internal/output/table.go` (lines 191 and 238). `go build ./...`, `make check` and the `internal/output` tests all fail.
- `tasksCmd` is `tasks [task_id]` with `MaximumNArgs(1)` and only local flags. A `status` subcommand gets the arguments when the first arg is `status`. `tasks HGAI-1217` keeps working. The only collision is a task whose ID is literally `status`.
- `api.Client.doRequest` only sends GET requests with no body. Debug output goes to stdout, which corrupts `--output json`.
- The `custom_task_ids` / `team_id` query logic is duplicated in `GetTask` and `GetTaskComments`.
- `models.Task.List` already holds the list ID. `models.Status` has the same shape as the entries of the `statuses` array in the list response. There is no `List` model yet.
- There are no HTTP-level tests. The `baseURL` field exists but is unexported.

## Flow

```
clickup tasks status HGAI-1217 "In Progress"
  1. GET /task/HGAI-1217?custom_task_ids=true&team_id=W   -> task.list.id, task.status
  2. GET /list/{list_id}                                   -> list.name, list.statuses
  3. list.FindStatus("In Progress")
       not found  -> error with valid statuses, exit 1 (no write)
       == current -> "already" message, exit 0 (no write)
  4. PUT /task/HGAI-1217?custom_task_ids=true&team_id=W  {"status":"in progress"}
  5. print "HGAI-1217: to do -> in progress" (or updated task JSON)
```

## Approach

I considered three shapes and chose B.

- **A - Inline in `commands/tasks.go`:** an ad-hoc `map[string]any` body and a raw GET of the list inside the command. Smallest diff, but the command would do API and domain work itself, the request would be an untyped bag, and nothing could be tested without the network.
- **B - Layered (chosen):** the API layer gets typed request and response methods, the model owns status lookup, and the command orchestrates and renders. This follows the repo's existing `api` / `models` / `commands` split. It is testable against `httptest` through the real HTTP code path.
- **C - Interface-based client:** a `TaskService` interface in `commands` with a mocked implementation in tests. It adds an abstraction with one implementation, and its tests would skip the real request encoding. That is not worth it at this size.

## Changes by file

### 1. `internal/output/table.go` - fix the build
Delete the second `DetailFormatter.FormatComments` (line 237 to the end of that function). The two copies are identical, so behavior does not change.

### 2. `internal/api/client.go`
- `doRequest(method, path string, query url.Values, payload any)`: if `payload != nil`, JSON-encode it into a `bytes.Reader` request body. Rename the response variable to `respBody`.
- `Put(path string, query url.Values, payload any) ([]byte, error)`.
- `Get` passes a `nil` payload.
- `SetBaseURL(url string)`, alongside `SetDebug`. Tests use it to point the client at `httptest`.
- All `[DEBUG]` output goes to `os.Stderr`.

### 3. `internal/api/tasks.go`
```go
// UpdateTaskRequest contains the fields to change on a task
type UpdateTaskRequest struct {
	Status string `json:"status,omitempty"`
}

// UpdateTask updates a task and returns the updated task
// teamID is required when using custom task IDs (e.g., HGAI-1217)
func (c *Client) UpdateTask(taskID, teamID string, req UpdateTaskRequest) (*models.Task, error)

// taskIDQuery returns the query needed to address a task by custom ID
func taskIDQuery(taskID, teamID string) url.Values
```
`GetTask`, `GetTaskComments` and `UpdateTask` all start from `taskIDQuery`. The request struct is typed and uses `omitempty`, so fields like name or assignees can be added later without touching callers.

### 4. `internal/api/lists.go` (new)
`GetList(listID string) (*models.List, error)` calls `GET /list/{id}`.

### 5. `pkg/models/list.go` (new)
```go
// List represents a ClickUp list
type List struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Statuses []Status `json:"statuses"`
}

// FindStatus returns the status matching name, ignoring case and surrounding whitespace
func (l *List) FindStatus(name string) (Status, bool)
```

### 6. `internal/commands/tasks_status.go` (new)
- `tasksStatusCmd`: `Use: "status <task_id> <status>"`, `Args: cobra.ExactArgs(2)`, help text with examples, and a local `--output/-o` flag (`json` only; any other value returns an error).
- Registered with `tasksCmd.AddCommand(tasksStatusCmd)` in `init()`.
- `runTasksStatus` follows the flow above. Errors are wrapped like the existing ones (`failed to get task: %w`, `failed to get list: %w`, `failed to update task: %w`).
- Two more errors: an empty `task.List.ID` gives "task has no list". A list with no statuses goes through the invalid-status path, which prints nothing under "Valid statuses:".
- `invalidStatusError(input, list, current)` builds the multi-line error, sorting a clone of the statuses by `Orderindex`.
- Writes to `cmd.OutOrStdout()` instead of `os.Stdout`, so tests can capture output. The existing commands are not changed.

Error output (printed by `Execute` as `Error: ...` on stderr):
```
Error: invalid status "done" for list "Sprint 12". Valid statuses:
  to do
  in progress  (current)
  review
  complete
```

### 7. Help and docs
- `rootCmd.Long`: add `clickup tasks status <ID> <status>   Change task status`.
- `tasksCmd.Long`: add an example line.
- `README.md` Commands > Tasks: add the command and a note about quoting.
- `skills/SKILL.md`: add a "Change Task Status" section. Add trigger phrases to the description ("set status", "move task to", "mark task as"). Add a guideline: if the status is rejected, show the valid statuses and ask the user which one they meant instead of guessing.

### 8. `bin/` - prebuilt binaries
Run `make build-all` so the fallback binaries include the command (the last feature did the same).

## Tests

| File | Cases |
|------|-------|
| `pkg/models/list_test.go` | exact match; case-insensitive (`IN PROGRESS`); surrounding whitespace; not found; empty list |
| `internal/api/tasks_test.go` | `UpdateTask` sends PUT with body `{"status":"in progress"}`, the auth header and JSON content type; custom ID adds `custom_task_ids=true&team_id=W`; native ID sends no query; parses the returned task; a 400 response returns `*APIError` |
| `internal/api/lists_test.go` | `GetList` hits `/list/{id}` and parses name and statuses |
| `internal/commands/tasks_status_test.go` | fake server for GET task / GET list / PUT task. Cases: success line; `--output json` prints the updated task; mixed-case input sends the canonical name; invalid status returns an error listing every status in order with `(current)` and sends **no PUT**; same status sends **no PUT** and prints the "already" message; same status with `--output json` sends **no PUT** and prints the task from the initial GET as JSON; unsupported `--output` value is rejected |

The command tests set the package globals `cfg` and `apiClient` (using `SetBaseURL`), run through `rootCmd.SetArgs`, and reset the globals and `statusOutput` in `t.Cleanup`.

## Commit sequence

1. `fix(output): remove duplicate DetailFormatter.FormatComments` - restores the build
2. `fix(api): write debug output to stderr`
3. `refactor(api): extract custom task ID query helper`
4. `feat(api): add PUT support, UpdateTask and GetList` - includes `models.List`, `FindStatus` and tests
5. `feat(commands): add tasks status subcommand` - includes command tests
6. `docs: document tasks status in README, skill and help`
7. `chore: rebuild prebuilt binaries`

`make check` must pass at every commit from 1 onward.

## Verification

1. `make check` is green.
2. Run against the real API with `make run ARGS="tasks status <id> bogus --debug"`. Confirm the valid statuses match the list in the ClickUp UI and are in UI order.
3. Use a list that **inherits** statuses from its folder or space (`override_statuses: false`). Confirm `GET /list` still returns the effective statuses. If it does not, fall back to the folder's statuses, then the space's (see risks).
4. Set a valid status with different casing, check it in the ClickUp UI, and set it back. **This changes real data, so I will ask you for a throwaway task ID first.**
5. Run once with a custom ID (`HGAI-...`) and once with a native ID.

## Risks

- **Inherited statuses:** ClickUp's docs list `statuses` and `override_statuses` on Get List. I expect `statuses` to be the effective set for inheriting lists, but that needs to be confirmed in verification step 3. If it is wrong, `GetList` gets a fallback to the folder's or space's statuses. That change stays inside `commands/tasks_status.go` and `api`.
- **`orderindex` type:** the model assumes a number, which works for task responses today. Verify that list responses use a number too.
- **Custom ID detection** still uses the existing "contains a hyphen" check, so the new command has the same limits as `tasks <id>`.
- **Statuses change between GET and PUT:** the API rejects the PUT and the wrapped error is shown. That is acceptable.
- **Tasks in multiple lists:** a task's status comes from its home list, which is what `task.list` returns, so validation uses the right list.
- **Three requests per change:** about 3x the latency of a single call, which is fine for an interactive command.

## Out of scope / follow-ups

- Tab-completion of statuses (`ValidArgsFunction`).
- Moving the existing commands to `cmd.OutOrStdout()` for testability.
