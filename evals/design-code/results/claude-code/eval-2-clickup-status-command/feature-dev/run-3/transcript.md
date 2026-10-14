## Eval Prompt

/feature-dev:feature-dev plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I read the codebase (about 2.6k lines of Go) and stopped at the clarifying-questions phase, as the feature-dev process requires. I haven't written the plan files yet. I'll write the HTML plan and the `.md` copy under `.lavish/` once you've answered the questions below.

## What I found

**Current `main` doesn't compile.** `go build ./...` fails because `DetailFormatter.FormatComments` is defined twice in `internal/output/table.go` (lines 191 and 238). It's left over from the merge commit `7411557`. The copy at line 238 is the old one without word wrapping and should be deleted. This has to be fixed first, as its own commit, before anything else can be tested.

**How the command fits in:**
- `tasksCmd` is `tasks [task_id]` with `MaximumNArgs(1)` (`internal/commands/tasks.go:24`). Adding `status` as a Cobra subcommand of `tasksCmd` works cleanly:
  - Cobra checks for a subcommand name before it checks the parent's arguments, so `tasks HGAI-1217` still works.
  - No real task ID can be the word `status`.
  - The `task` and `t` aliases also give you `clickup t status ...` for free.
- The parent's flags (`--status`, `-o`) are local to `tasksCmd`, so they don't leak into the new subcommand. It will need its own `-o`.

**Changes needed in the API client:**
- `doRequest` (`internal/api/client.go:42`) always sends a nil body and there is only a `Get` method. It needs a request body and a new `Put`.
- Two new endpoints:
  - `GET /list/{list_id}`: returns the list's effective `statuses` (including any inherited from the folder or space).
  - `PUT /task/{task_id}` with `{"status": "..."}`: returns the updated task.
- Both need the same `custom_task_ids` / `team_id` handling that `GetTask` and `GetTaskComments` already copy between them. That's worth pulling into a shared helper.
- `task.List.ID` is already available from `GetTask`. `models.Status` already exists; there's no `List` model with statuses yet.

**Smaller issues nearby:**
- `--debug` prints to stdout, which corrupts `-o json` output.
- `query != nil && len(query) > 0` is a redundant check.
- There are no API tests; the existing tests cover config, models and output formatting.

**Proposed flow:** fetch the task, then fetch its list's statuses, match the input, `PUT` the change, and print the result. That's 3 API calls.

## Questions

1. **Matching the status name.** I'd match case-insensitively on the exact name and send the list's spelling to the API. No fuzzy or prefix matching, so `review` would not match `in review`. Is that OK?
2. **When the status is wrong.** I'd return an error (exit code 1, on stderr) listing the list's statuses in workflow order, with the task's current status marked:
   ```
   Error: invalid status "reveiw" for list "Sprint 12". Valid statuses:
     to do (current)
     in progress
     in review
     complete
   ```
   Should each status also show its type (open, custom, done, closed)?
3. **Listing statuses without changing anything.** Should `clickup tasks status <id>`, with no status given, just print the valid statuses? It costs almost nothing and avoids having to make a deliberately wrong guess to see the list. I recommend yes.
4. **Already in that status.** I'd skip the `PUT`, print `HGAI-1217 is already "in review"`, and exit 0. Is that OK, or should it be an error?
5. **Output on success.** I'd print one line: `HGAI-1217: to do -> in review`. With `-o json`, it would print the updated task returned by the `PUT`. Is that OK?
6. **Fixes outside the feature.** Can I include these as separate small commits?
   - The compile fix (required).
   - Moving `--debug` output to stderr.
   - The shared custom-ID query helper.
7. **Docs and binaries.** I'd update the README, `skills/SKILL.md` (including its trigger description) and the `tasks` help examples. Should I also run `make build-all` to refresh the pre-built binaries in `bin/`, like the last feature plan did?

## Simulated user turn 1

1. Yes, case-insensitive exact match is fine.
2. List them in the list's board order. No types, just the names with the current one marked.
3. Yes, print the valid statuses when no status is given.
4. Yes, print the notice, change nothing and exit 0.
5. Yes, that output is fine.
6. Do the compile fix and the shared helper as separate commits. Skip the `--debug` change.
7. Yes, update the docs and run `make build-all` like last time.

## Executor turn 2

The plan is written, using your answers, and is ready for you to approve. I haven't written any code.

- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

**Recommended approach (B).** Each part goes in the package that already handles that kind of thing:
- **API (`api`):** add `GetList`, plus `UpdateTask` taking a `TaskUpdate` struct so more fields (name, priority) can be added later.
- **Status lookup (`models.List`):** sort statuses into board order and match the name case-insensitively.
- **Rendering (`output`):** one `WriteStatusList` helper, used both for the plain listing and inside the error message.
- **Command:** a thin `tasks status` subcommand that writes through `cmd.OutOrStdout()` so tests can capture its output.

I compared it with two alternatives in the plan:
- **A, everything in the command file:** fewest files, but the logic can't be tested without running the CLI.
- **C, caching list statuses in config:** saves one API call, but the cache goes stale when statuses change in ClickUp.

The codebase is small and your answers settled most of the design, so I wrote these myself rather than running separate architect agents.

**Commits, in order:**
1. Fix the build: remove the duplicate `FormatComments` in `internal/output/table.go` left by the merge.
2. Add the shared helper for the custom task ID query parameters.
3. API and model work: request bodies, `Put`, `GetList`, `UpdateTask`, `models.List`, with `httptest` and model tests.
4. The command and its tests, run against a fake ClickUp server.
5. Docs: README, `skills/SKILL.md` and the help text.
6. `make build-all`.

**Things I decided that you didn't specify:**
- **Multi-word statuses:** they must be quoted (`"in progress"`), the same as `--status` today.
- **JSON no-op:** if the task is already in that status and `-o json` is set, the unchanged task JSON goes to stdout and the notice to stderr, so scripts always get a task object.
- **Listing with JSON:** listing the statuses with `-o json` prints just the names, the same as the plain listing.
- **Real-API test:** the final check runs against the real ClickUp API and needs a throwaway task. I'll ask you for its ID before changing anything in your workspace.

The ClickUp API details are confirmed from developer.clickup.com: `GET /list` returns the list's statuses with their order, and `PUT /task` returns the updated task.

The HTML page uses the DaisyUI `nord` theme because this is a CLI project with no design system of its own to match.

Do you approve approach B, or do you want changes to any of the decisions above?

## Simulated user turn 2

One point on the plan as written: what does `-o json` do when listing statuses (no status argument)? Your message says it prints just the names, the same as the plain listing. That reads as inconsistent, since `-o json` otherwise always means JSON, and the plan pages don't mention this case at all. Please state the behavior in the plan. A JSON array of names would match the rest of the flag.

Everything else looks fine.

## Executor turn 3

You're right, that was inconsistent. I've updated both plan files so that `clickup tasks status <id> -o json` prints a JSON array of the status names in board order:

```
$ clickup tasks status HGAI-1217 -o json
[
  "to do",
  "in progress",
  "in review",
  "complete"
]
```

The JSON has no `(current)` marker, since the task's own JSON already includes its current status.

**What changed in the plan:**
- **Example and decision:** the "What the user sees" examples and the confirmed-decisions table now show this case.
- **Commit 4:**
  - `internal/output/json.go` exports a `WriteJSON(w, data)` helper. It replaces `JSONFormatter`'s private `writeJSON`, so all JSON output keeps the same indentation.
  - The command uses it to print the list of names.
- **Tests:** a new command test case checks for a JSON array of names in board order.
- **Real-API check:** listing statuses with and without `-o json` is now one of the steps.

In the HTML page, the changed blocks are marked as Round 1 revisions.

With this settled and the rest approved, should I start on commit 1, the build fix?

## Simulated user turn 3

APPROVED

The plan covers the JSON listing case now and is fine as written.

## Executor turn 4

The final plan is written in both files, and both now mark approach B as approved:

- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

Both files say that `-o json` with no status prints a JSON array of status names in board order. They also lay out the six commits, starting with the build fix: `main` doesn't compile right now because of a duplicate method in `internal/output/table.go`.

I haven't implemented anything, as you asked.
