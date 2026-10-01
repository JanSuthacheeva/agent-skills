## Eval Prompt

/feature-dev:feature-dev plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've read the relevant code: `commands/tasks.go`, `commands/root.go`, `api/client.go`, `api/tasks.go`, `api/comments.go`, `api/errors.go`, `models/task.go`, `output/*`, `skills/SKILL.md`, and the earlier plan in `docs/plans/`. The codebase is about 2.5k lines, so I read it directly instead of sending explorer agents.

## What I found

**`main` doesn't build right now.** `internal/output/table.go:238` declares `DetailFormatter.FormatComments` a second time; the first is at line 191. This came in with the merge commit `7411557`. The fix is to delete the second copy and keep the word-wrapping version from #3. `go vet` and `go test` both fail until that's done, so it will be step 0 of the plan.

**Things the feature depends on:**
- **No way to send a request body.** `api.Client.doRequest` always sends a nil body and only `Get` exists, so the client needs a body-capable request and a `Put`.
- **The task already tells us its list.** `models.Task.List.ID` holds the task's home list. ClickUp's `GET /list/{id}` returns the list's statuses, and `PUT /task/{id}` with `{"status": "..."}` changes the status.
- **Custom IDs only matter on the first call.** `GetTask` already handles IDs like `HGAI-1217`. If the PUT uses the native ID that `GetTask` returns (`task.ID`), it doesn't need the custom-ID query params.
- **The subcommand fits under `tasks` without conflicts.** `tasks` takes an optional `[task_id]`, but its `Args` is set to at most one argument, so Cobra sends `tasks status ...` to the subcommand and `tasks HGAI-1217` still works. Flags like `--status open` on `tasks` stay local and keep working.
- **No command or API tests exist yet.** The only tests are model and output tests in plain `testing` style. The status matching should be a pure function so it can be tested properly, and the API methods can be tested against `httptest` (the client's `baseURL` field is reachable from tests in the same package).
- **The skill doc needs updating.** `skills/SKILL.md` lists the commands, and Claude only knows about this one if it's added there.

## Questions before I design

1. **Matching.** ClickUp statuses are usually lowercase (`in progress`). Should input match case-insensitively (`"In Progress"` works) and exactly otherwise? Or should unique prefixes also work (`clickup tasks status X prog`)?
   *Recommendation: case-insensitive exact match only. Prefixes make a write command less predictable.*
2. **Invalid status output.** I'm thinking of this, printed to stderr with exit code 1:
   ```
   Error: "doing" is not a valid status for list "Sprint 42". Valid statuses:
     to do
     in progress  (current)
     review
     complete
   ```
   Should the statuses be in ClickUp's board order (`orderindex`), with the current one marked? Should they be colored with the status color?
   *Recommendation: board order, mark the current one, no color.*
3. **Already in that status.** Should it skip the API call and print `HGAI-1217 is already "in progress"` with exit code 0, or send the update anyway?
   *Recommendation: skip and exit 0.*
4. **Success output.** Should it be one line like `HGAI-1217: to do -> in progress`, or the full detail view? And should `--output json` print the updated task?
   *Recommendation: the one line by default, and support `-o json`.*
5. **Multi-word statuses.** Should `clickup tasks status X in progress` work without quotes (joining the remaining arguments), or must quotes be used (exactly 2 arguments)?
   *Recommendation: exactly 2 arguments. It's explicit and matches how `--status "in progress"` already works.*
6. **Scope.** Is anything beyond the command in scope, e.g. a `clickup tasks statuses <id>` command that just lists the valid statuses? Should I regenerate the pre-built binaries in `bin/` with `make build-all`, as the last feature did?
   *Recommendation: no extra command, since the error message already lists the statuses. Yes to `build-all`.*

You can answer each one or just say "go with your recommendations". After that I'll draft 2-3 architecture options and write the final plan to `.lavish/` as HTML and Markdown.

## Simulated user turn 1

1. Case-insensitive exact match, no prefixes.
2. Board order, mark the current one, no color.
3. Skip and exit 0, with a notice.
4. Go with your recommendation.
5. Go with your recommendation, exactly 2 args.
6. Go with your recommendation. No extra command, and yes to `build-all`.

No confirmation prompt before changing the status.

## Executor turn 2

I've written the plan to `.lavish/tasks-status-command.html`, with a Markdown copy at `.lavish/tasks-status-command.md`. No code has been changed.

**Recommended approach (option B, layered):**
- **Matching** lives on a new `models.List` type, as `FindStatus` (ignores case, no prefixes) and `SortedStatuses` (board order). Both are pure functions with unit tests.
- **API client:** `doRequest` gains JSON request bodies, plus a new `Put` and two thin methods, `GetList` and `UpdateTaskStatus`. While touching the client, I'd also:
  - pull the custom-ID query into one `taskIDQuery` helper, since it would otherwise be copied a third time;
  - add `SetBaseURL` so the command can be tested against a fake server;
  - send debug logs to stderr, since they currently break `--debug -o json`.
- **Command:** new file `commands/tasks_status.go`. It fetches the task, then the list, validates, and only then sends the update. The update uses the list's own spelling of the status and the task's native ID. When the status is already set, it makes no API call.
- **Output flag:** `--output` becomes a persistent flag on `tasks` so `status` inherits `-o`.

**Alternatives I rejected:**
- **A (everything inline in the command):** smaller diff, but the matching can't be tested without HTTP and the custom-ID duplication grows.
- **C (one `SetTaskStatus` method on the API client):** puts business rules in what is today a thin HTTP layer, for a single caller.

**Other points:**
- **Step 0 is fixing the broken build.** The duplicate `FormatComments` in `table.go:238` means `go vet` and `go test` fail on `main` right now. It gets its own commit.
- **One thing to check against a real workspace:** whether ClickUp's `GET /list/{id}` returns statuses that a list inherits from its folder or space. I expect it does. The plan includes a guard for an empty status list and an end-to-end check for this case. If the check fails, it falls back to looking up the folder and then the space.
- **Testing** covers model, API (against a fake server) and command-level tests, a manual check against a real workspace, and six small commits ending with `make build-all`.

The repo has no design system (it's a CLI), so the HTML page uses the Lavish fallback styling (DaisyUI, nord theme).

Should I go with option B, or would you like changes to the plan first?

## Simulated user turn 2

Option B is fine. One inconsistency in the examples: the invalid-status one marks `to do (current)`, but the "already" example uses the same task HGAI-1217 as being in `in progress`. Please make the examples consistent, so the same task shows the same current status in each.

## Executor turn 3

The examples are consistent now. Every one starts with HGAI-1217 in `to do` on list "Sprint 42", and there's a line above them in both files saying so.

- **Success:** `to do -> in progress` (no change).
- **Invalid status:** marks `to do (current)` (no change).
- **Already in status:** now runs `clickup tasks status HGAI-1217 "To Do"` and prints `HGAI-1217 is already "to do"`. The mixed-case input also shows that the notice uses the list's own spelling of the status.
- **JSON:** moves to `review` (no change).

I made the same edits in `.lavish/tasks-status-command.html` and `.lavish/tasks-status-command.md`, and nothing else in the plan changed.

Option B is locked in. Shall I start implementing, beginning with step 0 (the build fix)?

## Simulated user turn 3

APPROVED

The examples are consistent now and the plan matches my answers.

## Executor turn 4

The final plan is written in two files:

- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

My only edit since your review: both files now show option B as chosen and approved instead of recommended.

I haven't implemented anything. When work starts, the first step is the separate commit that fixes the build: removing the duplicate `FormatComments` in `internal/output/table.go:238`.
