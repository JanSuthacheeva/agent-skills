## Eval Prompt

/superpowers:brainstorming plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

Here's what I found and what I took from your request.

**What's already there**
- `tasksCmd` in `internal/commands/tasks.go:24` takes an optional `[task_id]` positional. If we add a `status` subcommand under it, Cobra resolves the subcommand name first, so `clickup tasks status <id> <status>` and `clickup tasks <id>` can both work.
- The API client can only send GETs. `doRequest` in `internal/api/client.go:42` always passes a `nil` body. To change a status we need `PUT /task/{id}` with a JSON body, so the client needs body support.
- `models.Task` already carries `List.ID` (`pkg/models/task.go:26`), so we can find the task's list with one `GET /list/{id}`. That call returns the list's statuses, including ones it inherits.
- The custom-ID query handling (`custom_task_ids` + `team_id`) is copied in `GetTask` and `GetTaskComments`. A third copy is a good reason to pull it into a shared helper.
- The `api` and `commands` packages have no tests.

**My understanding**
- What you asked for: `clickup tasks status <id> <status>` changes a task's status. Before writing anything, it checks the status against the statuses of the task's own list. If the status isn't valid, it fails and lists the valid ones.
- What I'm assuming:
  - The command exits non-zero on an invalid status.
  - On success it prints a one-line confirmation (e.g. `HGAI-1217: open -> in progress`).
  - If the task already has that status, it says so and skips the write.
  - It accepts both custom IDs (`HGAI-1217`) and native IDs, like the existing commands.
  - The README, root help text and `skills/SKILL.md` get updated so agents can find the command.

Correct me on any of that. The one question that most affects the design is:

**How strict should matching `<status>` be?**
- **A) Exact match, ignoring case** (my recommendation). `In Progress` matches `in progress`, and we send ClickUp the list's own spelling. It's predictable and never surprises you.
- **B) A plus unique prefix.** `prog` resolves to `in progress` if no other status matches. Faster to type, but a status added to the list later can make an old prefix ambiguous.
- **C) Exact, case-sensitive.** Strictest, but annoying since ClickUp itself treats status names as case-insensitive.

Once you answer, I'll write up the design as the lavish plan plus a Markdown copy under `.lavish/` for your approval.

## Simulated user turn 1

Option A, exact match ignoring case. Your assumptions are fine, including exit 0 with a notice when the task already has that status. Go ahead and write the plan.

## Executor turn 2

I've written the plan, and it's ready for your review. I haven't written any code.

- **Visual plan:** `.lavish/clickup-tasks-status.html`
- **Markdown copy:** `.lavish/clickup-tasks-status.md`

**The design in short**
- **What the command does:** it makes three API calls. First it fetches the task, then the task's list (`GET /list/{list.id}`, which includes statuses the list inherits). It matches your status against that list, ignoring case, and then sends the list's own spelling with `PUT /task/{id}`.
  - Unknown status: it lists the valid ones in list order and exits 1.
  - Task already has that status: it prints a notice and exits 0.
  - Changed: it prints `HGAI-1217: open -> in progress`.
- **Changes in the API client (`internal/api/client.go`):**
  - `doRequest` gets JSON body support and a new `Put`.
  - The duplicated custom-ID query code becomes one shared `taskIDQuery` helper.
  - Debug output moves from stdout to stderr, since it currently mixes into `-o json` output.
- **New code:**
  - `models.List` with `FindStatus`, a pure function that can be tested without HTTP.
  - `GetList` and `UpdateTaskStatus` in the API client.
  - A new `internal/commands/tasks_status.go`. Its logic depends on a small interface, so it can be tested with a fake client.
- **Two small additions you didn't ask for:**
  - If someone forgets to quote a multi-word status, they get a hint about quoting instead of Cobra's `accepts 2 arg(s), received 3`.
  - If a list comes back with no statuses, the command says so clearly instead of rejecting every status as invalid.
- **Testing:** written test-first for the model, the API client (against a local test server) and the command (with the fake client). Then eight end-to-end checks against a throwaway task in a real workspace, and `make check`.
  - One thing I couldn't confirm from the code: that `GET /list` returns statuses the list inherits from its folder or space. End-to-end check 6 covers that.
- **Docs:** help text, README, `skills/SKILL.md` (the agent should only change a status when explicitly asked), and rebuilt binaries in `bin/`.
- **Commits:** six small ones, listed in the plan.

The page uses the Lavish fallback style (Tailwind + DaisyUI, `nord` theme), because this is a CLI project with no visual design system of its own to match.

Shall I go ahead and implement it as written?

## Simulated user turn 2

APPROVED. The plan covers what I asked for; I only wanted the plan, so no implementation yet.

## Executor turn 3

The plan is approved and finished, and nothing has been implemented. Both files are already written and up to date:

- `.lavish/clickup-tasks-status.html` (visual plan)
- `.lavish/clickup-tasks-status.md` (Markdown copy)

When you want it built, say so and I'll follow the commit sequence in the plan.
