# Plan: `clickup tasks status <id> <status>`

## Goal

Change a task's status from the CLI. The given status is validated against the statuses of the task's list. If it is not valid, the command fails and prints the valid statuses in workflow order.

## Current state (verified)

- `internal/commands/tasks.go` - `tasks [task_id]` with `cobra.MaximumNArgs(1)`. It has no subcommands.
- `internal/api/client.go` - `doRequest(method, path, query)` sends no body. Only `Get` exists. The CLI is read-only today.
- `internal/api/tasks.go` - `GetTask` returns `models.Task` with `Status` and `List{ID, Name}`. There is no list endpoint.
- `pkg/models/task.go` - `Status{ID, Status, Color, Type, Orderindex}` already exists and can be reused for list statuses.
- No API-level tests (no httptest setup). Tests cover models, output, and config.
- Cobra routing (checked with a scratch binary on cobra v1.10.2): adding a `status` subcommand under `tasks` keeps `tasks`, `tasks <id>`, `tasks --status x` and `tasks <id> --status x` working as they do now. A typo such as `tasks stauts` falls through to `tasks <id>` and fails as an unknown task, which is the same as today.

## Behavior

```
$ clickup tasks status HGAI-1217 review
HGAI-1217: in progress -> review

$ clickup tasks status HGAI-1217 In Progress      # unquoted multi-word works, case-insensitive
HGAI-1217: review -> in progress

$ clickup tasks status HGAI-1217 done
Error: invalid status "done" for list "Sprint 12"
Valid statuses:
  to do
  in progress
  review
  complete
(exit 1)

$ clickup tasks status HGAI-1217 review           # already in that status
HGAI-1217 is already in "review"
(exit 0, no PUT sent)
```

## Flow

1. `GET /task/{id}` (existing `GetTask`, handles custom IDs) -> current status, `list.id`, native `id`.
2. `GET /list/{list_id}` (new `GetList`) -> the list's effective statuses. This includes statuses inherited from the folder or space.
3. `list.FindStatus(input)` - trim the input and match it case-insensitively against the names.
   - No match: return `InvalidStatusError` (lists the valid names in `orderindex` order). Nothing is written.
   - Same as current: print a message and exit 0.
4. `PUT /task/{native_id}` with `{"status": "<canonical name>"}`. Using the native ID means the write path needs no `custom_task_ids` handling.
5. Print the one-line confirmation.

## Changes by layer

### `pkg/models/list.go` (new)
- `List{ID, Name, Statuses []Status}`.
- `(l *List) FindStatus(name string) (Status, bool)` - pure function, trim plus `strings.EqualFold`.
- `(l *List) StatusNames() []string` - names sorted by `Orderindex`.
- `pkg/models/list_test.go`: exact match, case and whitespace, not found, ordering.

### `internal/api/client.go`
- `doRequest(method, path string, query url.Values, body any)`: JSON-marshal `body` when it is non-nil and pass it as the request body. Print it in `--debug` mode.
- `Get` passes `nil`. Add `Put(path, query, body)`.

### `internal/api/lists.go` (new)
- `GetList(listID string) (*models.List, error)` -> `GET /list/{id}`.

### `internal/api/tasks.go`
- `UpdateTaskStatus(taskID, status string) error` -> `PUT /task/{id}` with body `{"status": status}`. This takes a native ID only.
- Tests in `internal/api/*_test.go` using `httptest.Server` (same package, so they can set `baseURL`): method, path, JSON body, auth header, and error mapping to `APIError`.

### `internal/commands/tasks_status.go` (new)
- `tasksStatusCmd`: `Use: "status <task_id> <status>"`, `Args: cobra.MinimumNArgs(2)`, status is `strings.Join(args[1:], " ")`, registered in `init()` via `tasksCmd.AddCommand`.
- `runTasksStatus`: the orchestration from the Flow section. It stays thin and the matching rules live in models.
- `InvalidStatusError{Given, ListName string; Valid []string}` with an `Error()` that renders the multi-line message. Root's `Error: %v` prints it unchanged.
- `tasks_status_test.go`: error message rendering and status resolution, built from a `models.List` fixture.

### Docs and distribution
- `tasks.go` Long examples, root `Long` "Get started" block, `README.md` Tasks section.
- `skills/SKILL.md`: add a "Change Status" section and add "change status", "move task to" to the description triggers.
- `make check`, then `make build-all` to refresh the pre-built binaries in `bin/` (repo convention).

## Verification

- `make check` passes (fmt, vet, all tests).
- E2E against a real ClickUp workspace, on a throwaway task, using the built binary:
  valid change (custom ID and native ID), case and unquoted multi-word input, invalid status shows the list and exits 1 with no change in the ClickUp UI, already-in-status sends no PUT (check with `--debug`), a task in a list that inherits space statuses, unknown task ID.

## Risks / edge cases

- Tasks in multiple lists: `task.list` is the home list, and its statuses control the task's status, so this is correct.
- There is a race if list statuses change between the GET and the PUT. ClickUp rejects the PUT and we show the API error. This is acceptable.
- A task whose ID is literally `status` would be shadowed by the subcommand. Not realistic.
- This is the first write operation. `doRequest` gets a body parameter, and all existing callers change only via `Get`.

## Decisions (approved)

1. Unquoted multi-word status: `args[1:]` is joined with spaces, so `clickup tasks status X in progress` works without quotes. Quoted input still works.
2. Success output: only the one-line confirmation `<id>: <old> -> <new>`. The command gets no `-o` flag.
