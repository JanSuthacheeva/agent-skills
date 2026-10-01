## Eval Prompt

/code-design plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've looked through the codebase and written up three possible structures. Before I design one in detail, I need you to pick.

**Comparison page:** `.lavish/tasks-status-approaches.html` (I didn't open it in a browser, as instructed). There's no design system to match in a Go CLI, so it uses Lavish's default styling (Tailwind and DaisyUI).

**First, the main branch doesn't build.** `DetailFormatter.FormatComments` is defined twice, at `internal/output/table.go:191` and again at `:238`. The second one is an older copy left over from a merge, so `make check` fails. Whichever approach you pick, the first step is deleting that stale copy.

**The approaches:**

- **A. The command does the work and checks first (recommended).** The new `tasks status` command fetches the task, then the statuses of its list, checks your status against them, and only then saves it. This is the same pattern `getTask` uses today (`internal/commands/tasks.go:111-124`). The status check is a small helper on a new `models.List`, so it can be tested without network calls.
  - **Costs:** it makes three requests to ClickUp, and the list's statuses could change between the check and the save. If that happens, ClickUp rejects the save and we show its error.
- **B. Save first, explain only if ClickUp rejects it.** The command sends the new status straight away. Only if ClickUp refuses it do we fetch the list and print the valid statuses.
  - **Benefit:** one request when the status is valid.
  - **Costs:** spotting an "invalid status" rejection depends on an undocumented ClickUp error code, which could change without notice. We also can't fix casing to the exact name ClickUp expects, and can't tell when the task already has that status.
- **C. Put the whole flow in the API client.** Same checks as A, but packaged as one `Client.SetTaskStatus` method that returns a typed error listing the valid statuses. Every existing client method maps to exactly one ClickUp endpoint, so this mixes the status rules into the HTTP layer. It's also more reuse than we need, since nothing else would call it today.

**Where do you want to go: A, B, C, or a mix?** Once you pick, I'll write the detailed design page (every file, function signature and step by step flow), plus the Markdown plan at `.lavish/tasks-status.md`. Smaller choices, like what success looks like, what happens if the task already has that status, how the valid statuses are listed, and `-o json` support, will be on that page as assumptions you can confirm or change.

## Simulated user turn 1

A. It matches the existing getTask pattern. The stale FormatComments copy can be deleted as the first step.

## Executor turn 2

I've written the full design for approach A: `.lavish/tasks-status-implementation.html`. It covers every file, function signature and step-by-step flow, including the error paths. As instructed, I didn't open it in a browser, so I also haven't checked how it renders. I'll write the Markdown plan to `.lavish/tasks-status.md` once you approve the design.

**The design:**
- **Step 0:** delete the stale copy of `FormatComments` at `internal/output/table.go:237-281`.
- **New `models.List`** (`pkg/models/list.go`) with `FindStatus(name) (Status, bool)` and `StatusNames() []string`. These are pure functions, so they can be tested without network calls.
- **API client:**
  - `doRequest` gains a parameter for the request body, and there's a new `Put`.
  - New `api/lists.go` with `GetList(listID)`.
  - `api/tasks.go` gets `UpdateTask(taskID, teamID, *UpdateTaskRequest)`.
  - The code that handles custom task IDs is already duplicated in two places and would be needed a third time, so it moves into one helper, `taskIDQuery`.
- **Command:** new `internal/commands/tasks_status.go`, registered under `tasksCmd`. `runTasksStatus` calls `setTaskStatus(w, taskID, status)`, which gets the task, then its list, checks the status, then saves it. It follows the same shape as `getTask`.

**Behaviours I decided for you (all listed on the page so you can overturn them):**
- Matching ignores case and extra spaces, and the list's exact spelling is what gets sent.
- `clickup tasks status X in progress` works without quotes.
- On success it prints one line: `HGAI-1217: to do -> in progress`.
- If the task already has that status, it says so and changes nothing.
- On a wrong status, nothing is saved. You get `Error: invalid status "x" for list "Sprint 12". Valid statuses:` followed by one status per line, and the command exits with code 1.
- There's no `-o json` option and no "did you mean" suggestion.

**One thing to check before building:** the design relies on ClickUp's list endpoint (`GET /list/{id}`) returning all the statuses a task can use. That includes statuses the list inherits from its folder or space. I believe it does, but I haven't confirmed it. The plan checks this first against a real workspace with `--debug`.

**Two open questions:**
1. **Should the API client get a `SetBaseURL` method?** It would let the command's own tests run against a fake server. I recommend yes, mirroring `SetDebug`. Without it, the command is only covered by manual testing against a real workspace.
2. **Should the update method be general or status-only?** I recommend the general `UpdateTask` with an `UpdateTaskRequest` struct: it's named after the ClickUp endpoint, and fields like assignees or priority can be added later without new methods. The alternative is a narrower `UpdateTaskStatus(taskID, teamID, status)`.

Do you approve the design, and how do you answer the two questions?

## Simulated user turn 2

APPROVED
Q1: yes, add SetBaseURL. Q2: generic UpdateTask.

## Executor turn 3

I've written the final plan; no code was changed.

- **Plan for the implementation session:** `.lavish/tasks-status.md`. It has the decision, ordered steps, every unit with its signatures, the data types, both step-by-step flows with error paths, tests, assumptions and your review decisions.
- **Design page:** `.lavish/tasks-status-implementation.html`. I removed the open questions and worked your answers into it: `SetBaseURL` is added and the command gets its own tests, and the update method is the generic `UpdateTask`.
- **Earlier comparison page:** `.lavish/tasks-status-approaches.html`, kept for reference.

I put the plan under `.lavish/` as your instructions specified, not in the repo's usual `docs/plans/` folder. As instructed, I didn't open any page in a browser.

Two things for whoever implements it:
- **Fix the build first.** It starts by deleting the stale `FormatComments` copy, because main doesn't build right now.
- **Check the list endpoint before building on it.** Confirm with `--debug` against a real workspace that ClickUp's list endpoint returns statuses inherited from the folder or space. The whole status check depends on it.
