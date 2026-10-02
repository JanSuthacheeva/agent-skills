## Eval Prompt

/code-design plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've written the approaches page to `.lavish/tasks-status-approaches.html`. I haven't opened it, per your instructions. It uses DaisyUI with the `nord` theme, because this repo is a CLI and has no design system of its own.

**Before any approach: `main` doesn't compile.** `DetailFormatter.FormatComments` is declared twice, at `internal/output/table.go:191` and `:238`. The plan starts with a separate commit that deletes the older, non-wrapping copy at `:238`.

The three approaches differ in which layer runs the "fetch task, fetch its list, check the status, update" flow:

- **A - the command runs the flow (recommended).** A new `tasks status` subcommand fetches the task, then its list, and calls `List.FindStatus` for a case-insensitive match. On a match it calls `UpdateTaskStatus`; otherwise it returns an error listing the valid statuses. The API client gets two small methods (`GetList`, `UpdateTaskStatus`) plus a `Put`, because today it can only send GETs.
  - This is how `getTask` already works: the command makes the calls and the API layer just wraps endpoints (`internal/commands/tasks.go:100-124`).
  - The matching rule is a plain function on the model, so it can be unit tested without any HTTP.
  - The cost is three HTTP calls per change.
- **B - the API client runs the flow.** A single `SetTaskStatus` call does everything and returns a new `InvalidStatusError` that carries the valid statuses. Business rules would move into the API layer, which only wraps endpoints today. It also adds a second error type and has no second caller to justify it.
- **C - update first, explain on failure.** The command sends the update straight away and only fetches the valid statuses if ClickUp rejects it. That's one request when it works. But it depends on recognising ClickUp's undocumented error text for an unknown status, which I haven't verified.

**Which approach do you want: A, B, C, or a mix?**

Three questions don't change the approach, but they do change what users see. I'll put them on the implementation page unless you answer them now:

1. **Multi-word statuses:** should `clickup tasks status HGAI-1 in progress` work without quotes? I'd join everything after the ID into one status.
2. **Matching:** I'd use an exact match that ignores case and surrounding spaces, with no prefix or fuzzy matching, since this command changes data.
3. **Output on success:** I'd print one line, `HGAI-1217: open -> in progress`. With `-o json`, it would print the updated task instead.

## Simulated user turn 1

A, as recommended.

1. Yes, join everything after the ID into one status.
2. Exact match ignoring case, no prefix or fuzzy matching. Your surrounding-space trimming is fine.
3. One line plus `-o json` is fine, as you proposed.

Also, if the task already has that status, print a notice, change nothing and exit 0. List the valid statuses in the list's board order. No confirmation prompt before changing.

## Executor turn 2

I've written the full design for approach A, with all five of your decisions folded in, to `.lavish/tasks-status-implementation.html`. I haven't opened it. Every method in the call chains appears on a unit card with the same signature, and every unit appears in the overview diagram.

**What changes:**
- **New command** in `internal/commands/tasks_status.go`. It defines `status <task_id> <status>` with at least two args, joins everything after the ID into one status, and has its own `-o` flag. The command runs the whole flow:
  - `changeTaskStatus(w io.Writer, taskID, statusName string) error` does fetch task, fetch list, match, then either update, report "already in that status", or return the invalid-status error.
  - `invalidStatusError` builds the error that lists the valid statuses in board order.
  - `printStatusChange` and `printStatusUnchanged` handle the output.
- **API:**
  - New `GetList(listID)` in `internal/api/lists.go`.
  - New `UpdateTaskStatus(taskID, teamID, status)` in `internal/api/tasks.go`.
  - `Put` added to `client.go`, with `doRequest` taking an optional request body.
  - `SetBaseURL` added to the client so tests can point it at a fake server.
  - A small `addCustomTaskIDParams` helper replaces the custom-ID handling that `GetTask` and `GetTaskComments` each repeat.
- **Models:** a new `List` type with `FindStatus` and `OrderedStatuses`, and `Status.Matches`. `Matches` is the single matching rule: ignore case and surrounding spaces, no prefix match. Both the validation and the "already in that status" check use it.
- **Commit 0** fixes the build that's broken on `main`.

**Two places I depart from the codebase's habits:**
- `changeTaskStatus` writes to an `io.Writer` instead of `os.Stdout`, so the command can be tested with a fake ClickUp server.
- The status command gets its own `-o` variable, because the parent command's flags aren't inherited.

**Eight assumptions are listed on the page.** These two are the ones most worth checking:
- With `-o json`, the "already in that status" case prints the current task as JSON instead of the notice.
- The update sends the list's own spelling of the status, not what you typed.

No open questions are left. Do you approve the design, or what should change? Once you approve, I'll write the Markdown plan to `.lavish/tasks-status.md`.

## Simulated user turn 2

One inconsistency: the invalid-status example on the page shows the valid statuses with no indentation, but assumption 4 says they're indented two spaces. Please make them match.

Also, I asked for a notice when the status is already set. With `-o json` the design prints the task instead, so please keep the notice in that case, or tell me why it can't.

## Executor turn 3

**Indentation:** the page already matches, so I didn't change anything there. The two-space rule is assumption 5, not 4 (4 covers the `-o` fallback). In the example's source, each valid status is indented by two spaces inside a block that preserves whitespace (`white-space: pre-wrap`), so it should render indented. I haven't seen it rendered, because I'm not opening a browser. If it still looks flush left to you, tell me which line and I'll fix it.

**Notice with `-o json`:** you're right, the design dropped it. It's fixed now. Nothing stops the notice from showing in JSON mode; the only constraint is keeping stdout valid JSON for scripts, so the notice now always goes to stderr. That's also where the command already writes its warnings (`internal/commands/tasks.go:120,128`). The result:
- **Text mode:** you see the notice and nothing is written to stdout.
- **`-o json`:** you see the notice, and stdout still holds only the current task as JSON, so piping into `jq` keeps working.

To make that possible, `changeTaskStatus` now takes separate writers for normal output and for stderr, `(out, errOut io.Writer, taskID, statusName string)`. `printStatusUnchanged` became `(out, errOut io.Writer, task *models.Task)`, and `printStatusChange`'s writer is renamed to `out`. I updated every place on the page that mentions these. That covers:
- the unit card and its signatures
- both call-chain diagrams and their step lists
- the decision recap
- assumption 3
- the note on where the design departs from existing conventions
- the test cases, which now check stdout and stderr separately and add the "already set with `-o json`" case
- a new example showing that case

Do you approve the design now? Once you do, I'll write the Markdown plan to `.lavish/tasks-status.md`.

## Simulated user turn 3

APPROVED. The notice now shows in both output modes, so go ahead and write the Markdown plan.

## Executor turn 4

The design is finished and written out. The Markdown plan is at `.lavish/tasks-status.md`.

Plan files:
- **Implementation page:** `.lavish/tasks-status-implementation.html`, which the Markdown links to at the top.
- **Markdown plan:** `.lavish/tasks-status.md`. It's what a later session works from: the decision, the prerequisite fix, each piece of code with its signatures, the data types, the step-by-step call sequences including errors, the tests, the assumptions, and the decisions made during review.
- **Approaches page:** `.lavish/tasks-status-approaches.html`.

I didn't run `lavish-axi end`, since you asked me not to drive lavish. Nothing has been implemented.

Commit 0 deletes the duplicate `FormatComments` in `internal/output/table.go`, because `main` doesn't compile until it's removed.
