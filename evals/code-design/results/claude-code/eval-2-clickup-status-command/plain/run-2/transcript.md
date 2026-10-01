## Eval Prompt

plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've written the plan as `.lavish/tasks-status-command.html` with a Markdown copy at `.lavish/tasks-status-command.md`. I haven't opened it in a browser, and no code is written yet.

**How it works.** `status` becomes a subcommand of `tasks`, so `clickup tasks <id>` and the `t`/`task` aliases keep working as they do now. Each run makes these calls:

1. **Get the task:** uses the existing `GetTask`, which already handles custom IDs like `HGAI-1217`. It gives the current status and the task's list ID.
2. **Get the list:** a new `GET /list/{id}` call returns that list's statuses.
3. **Check the status:** case-insensitive exact match, so `In Progress` works. No fuzzy matching, since this changes data.
   - **No match:** it prints the valid statuses in board order and exits 1 without changing anything.
   - **Already set:** if the task already has that status, it says so and changes nothing.
4. **Update the task:** `PUT /task/{id}` using the task's internal ID from step 1, then it prints `HGAI-1217: to do -> in progress`.

**Code changes:**
- **`internal/api/client.go`:** requests can now carry a JSON body, and there's a new `Put`. Today the client can only send GETs.
- **New files:** a `List` model with a `FindStatus` lookup (`pkg/models/list.go`), `GetList` (`internal/api/lists.go`), and the command itself (`internal/commands/tasks_status.go`). `UpdateTask` goes into the existing `internal/api/tasks.go`. It takes a general update struct rather than being status-only, so other fields can be added later.
- **Docs:** README, the command help text, and `skills/SKILL.md`. The skill gets a rule to confirm the task and target status with the user first. Then `make build-all` to refresh the binaries in `bin/`.
- **Tests:** unit tests for the status lookup and error message, plus the first `internal/api` tests (against a local fake server), then a checklist of 8 runs against a real workspace.

**Main risk:** I'm assuming `GET /list/{id}` also returns statuses the list inherits from its folder or space. The real-workspace runs check this. If it comes back empty, the fallback is to read the space's statuses.

**Styling:** this is a CLI with no web design system to match, so the page uses the Lavish fallback (Tailwind + DaisyUI, `nord` theme).

**Decisions for you:**
1. **Multi-word statuses:** I recommend joining the remaining words, so `clickup tasks status X in progress` works without quotes. The alternative is to always require quotes, which is stricter.
2. **Test task:** which task in your workspace can I safely change back and forth for the real-workspace runs?

## Simulated user turn 1

APPROVED
1. Join the args (recommended).
2. No specific task yet. I'll point you at a throwaway one when we get to the E2E runs.

## Executor turn 2

I've updated both plan files with your answers, and no code has been written:
- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

- **Multi-word statuses:** the command joins the words after the task ID, so `clickup tasks status X in progress` works without quotes.
- **Test task:** the real-workspace test runs are set to use the throwaway task you'll give me when we get there.

The open-questions section, including its input forms, is now a "Resolved decisions" list, so nothing in the plan is left open.
