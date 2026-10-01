## Eval Prompt

/feature-dev:feature-dev plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I read the codebase directly instead of sending out explorer agents. It's about 2.6k lines of Go, and only five or six files matter here.

## What I found

**`main` doesn't build right now.** The merge commit `7411557` left two copies of `DetailFormatter.FormatComments` in `internal/output/table.go` (lines 191 and 238). Because of that, `go build ./...` fails, and so do `make check`, `make build` and the `internal/output` tests. The plan has to fix this first.

**How the code is laid out:**
- `internal/commands/tasks.go` - `tasksCmd` is `tasks [task_id]` with `MaximumNArgs(1)`. All of its flags are local, so a subcommand under it won't pick them up. In Cobra, `tasks status X Y` will go to a `status` subcommand, and `tasks HGAI-1217` keeps working as it does now. The only clash is a task whose ID is literally `status`, which is unlikely enough to ignore.
- `internal/api/client.go` - `doRequest` can only send GET requests with no body. Changing a task needs a `PUT /task/{id}` with a JSON body, so the client needs body support and a `Put` method.
- `internal/api/tasks.go` and `comments.go` - the `custom_task_ids` + `team_id` query logic is copied in two places. A third endpoint would be a third copy, so it's worth pulling into one helper.
- `pkg/models/task.go` - `Task.List` already has the list ID, and `models.Status` (status, color, type, orderindex) has the same shape as the entries in ClickUp's list `statuses` array, so it can be reused. There's no `List` model yet.
- Nothing tests the API layer over HTTP. The tests in `api` can set the unexported `baseURL` to point at an `httptest.Server`.
- `--debug` prints to stdout, so it would mix into `--output json`. It's minor and not caused by this change. I'd fix it while I'm in there.

**The command would make three calls:** `GET /task/{id}` to get the list ID and current status, then `GET /list/{list_id}` to get the list's statuses, then `PUT /task/{id}` with `{"status": ...}`.

## Questions before I design it

I've put my recommendation in brackets after each one.

1. **Matching the status name.** Should a match ignore case but otherwise be exact, or also accept a unique prefix (`prog` meaning `in progress`)? [Ignore case, exact only. This command changes data, so it should be predictable. Send the list's own spelling to the API.]
2. **Statuses with spaces.** Should the user have to quote them (`"in progress"`, exactly 2 args), or should extra args be joined (`clickup tasks status X in progress`)? [Require quotes. Joining args hides typos and is ambiguous.]
3. **Output when the status is wrong.** I'd return an error, exit with 1, and list the valid statuses in the list's order, with the current one marked:
   ```
   Error: invalid status "done" for list "Sprint 12". Valid statuses:
     to do
     in progress  (current)
     review
     complete
   ```
   Should the list also show each status's type (open/custom/closed) or color? [Names plus the current marker, no color.]
4. **Output when it succeeds.** [One line: `HGAI-1217: to do -> in progress`. Support `--output json` to print the updated task the PUT returns, so scripts and the Claude skill can use it.]
5. **Task already has that status.** [Skip the PUT, print `HGAI-1217 is already "in progress"`, exit 0.]
6. **Shell completion.** Should we add tab-completion of the list's statuses for the second argument (`ValidArgsFunction`)? It's cheap to add, but each tab press makes API calls. [Leave it out for now, as a follow-up.]
7. **Scope beyond the command.** Should the plan also cover the build fix, the `--debug` stdout fix, the shared custom-ID query helper, and updates to the README, `skills/SKILL.md` (including its trigger phrases) and the root help text? [Yes to all.]
8. **Tests.** The plan would test status matching as a pure function, plus `httptest` tests for `GetList` and the status update (checking the request body and the custom-ID query). Should it also have a command-level test that runs the whole flow against a fake server? [Yes. It means the command needs a way to swap in its API client for tests, and I'd keep that small.]

Once you've answered (or said "go with your recommendations"), I'll compare a couple of designs, then write the plan to `.lavish/clickup-tasks-status.md` and as an HTML page under `.lavish/`.

## Simulated user turn 1

Go with your recommendations on all eight.

## Executor turn 2

I wrote the plan for `clickup tasks status <id> <status>` using all eight of your recommendations. No code has been written yet.

- HTML: `.lavish/tasks-status-command.html`
- Markdown: `.lavish/tasks-status-command.md`

**First problem: `main` doesn't build.** The merge commit `7411557` left two identical copies of `DetailFormatter.FormatComments` in `internal/output/table.go` (lines 191 and 238). Until that's fixed, `go build`, `make check` and the output tests all fail, so the plan fixes it as commit 1.

**How the command works.** It makes three API calls:
1. Fetch the task, which gives its list ID and current status.
2. Fetch that list, which gives its name and allowed statuses.
3. If the status matches (ignoring case), send the update using the list's own spelling.

Both checks happen before the update, so nothing is written when the status is wrong or already set.

**How the code is split** (I went with a layered approach):
- **API layer:** gains the ability to send a request body, plus `UpdateTask` (with a typed `UpdateTaskRequest`) and `GetList`. A single `taskIDQuery` helper replaces the custom-ID query logic that is currently duplicated.
- **Model:** a new `models.List` owns the status lookup (`FindStatus`).
- **Command:** a new `internal/commands/tasks_status.go` registers the subcommand under `tasksCmd`, runs the steps above and prints the result. The existing `tasks <id>` routing is unchanged.

I rejected two alternatives:
- **Everything inline in `tasks.go`:** the request body would be an untyped map and nothing could be tested without the network.
- **A mocked client interface:** it adds an abstraction with only one implementation, and the tests would skip the real request encoding.

**Tests.** Unit tests for `FindStatus`, tests for the API layer against a local fake server (`httptest`), and command-level tests against a fake ClickUp server. The command tests check that no update is sent when the status is invalid or already set.

**Seven small commits**, with `make check` passing after each one: build fix, debug output to stderr, the query helper, the API additions, the command, docs and skill, then rebuilt prebuilt binaries.

**Main risk.** I expect fetching a list to return the statuses it inherits from its folder or space, but I haven't confirmed that. The plan checks it against the real API, and if it's wrong it falls back to the folder's or space's statuses. That fix would stay within the API layer and the new command file.

**One thing I'll need from you.** The end-to-end check changes a real task's status in ClickUp. When we get there I'll ask you for a throwaway task ID.

I designed this myself rather than sending out the architect agents, because the codebase is small. The page uses the default Tailwind/DaisyUI `nord` look, since a CLI repo has no design system to match.

Should I start implementing?

Sources:
- [ClickUp Get List API guide](https://consultevo.com/clickup-get-list-api-guide/)
- [clickupython lists docs](https://clickupython.readthedocs.io/en/latest/lists.html)

## Simulated user turn 2

One unclear point: decision 5 in the .md says the "already" case prints the task JSON with `--output json`. The HTML doesn't mention this, and there's no PUT response in that case. Please state which task it prints (presumably the one from the initial GET) and add it to the HTML and the tests.

Otherwise the plan is fine. Don't start implementing, I only wanted the plan.

## Executor turn 3

You were right: in the "already" case, `--output json` prints the task from the initial `GET /task`, since there is no PUT and so no PUT response. The code sketch already does this; only the plan text left it unclear. I've now written it into both files:

- **`.md`:** decision 5 states which task is printed. The command tests table has a new case: same status with `--output json` sends no PUT and prints the task from the GET as JSON.
- **`.html`:** row 5 of the decisions table says the same. The terminal example shows the "already" JSON case next to the normal success case. The tests table has the same new case.

The plan also notes one small difference between the two JSON outputs. Both are a `models.Task`, so the structure is the same. The GET version also fills in `subtasks` and `markdown_description`, because `GetTask` asks for them.

I haven't started implementing anything.

## Simulated user turn 3

APPROVED
The "already" JSON case is now stated consistently in both the .md and the HTML.

## Executor turn 4

The plan is approved and both final files are saved:

- `.lavish/tasks-status-command.md`
- `.lavish/tasks-status-command.html`

I haven't changed any code, and `main` still doesn't build because of the duplicate `FormatComments` in `internal/output/table.go`; the plan fixes that as its first commit.
