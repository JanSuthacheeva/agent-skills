## Eval Prompt

plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've written the plan in two formats: `.lavish/tasks-status-command.html` and `.lavish/tasks-status-command.md`. The HTML uses DaisyUI `nord`, since this is a CLI repo with no design system of its own. I haven't opened it in a browser.

**How it works**
1. Load the task (this handles custom IDs like `HGAI-1217`) to get its current status and `list.id`.
2. Fetch that list's statuses with `GET /list/{id}`. ClickUp returns the statuses the list actually uses, including ones inherited from the folder or space.
3. Match the input against them, ignoring case and extra spaces.
   - No match: the command fails with `invalid status "revew" for list "Sprint 42"` and lists the valid statuses in workflow order. Nothing is written.
   - The task already has that status: it says so and exits without writing.
   - Match: it sends `PUT /task/{id}` using the list's exact spelling, then prints `HGAI-1217: in progress -> review`.

**Design decisions**
- **`status` is a subcommand of `tasks`.** Cobra checks subcommand names first, and `tasks` already declares how many arguments it accepts, so `clickup tasks HGAI-1217` still works. The flags on `tasks` only apply to `tasks`, so they won't show up on `status`.
- **API client changes:**
  - `doRequest` gets a JSON body parameter, and a new `Put` uses it.
  - The custom-ID query logic, currently copied in `GetTask` and `GetTaskComments`, moves into one shared helper, `taskIDQuery`.
  - New: `GetList`, `UpdateTaskStatus`, and `models.List` with `FindStatus`/`StatusNames`.
- **Tests come first.** None exist yet for `internal/api` or `internal/commands`, so the plan adds:
  - unit tests for the status matching;
  - `httptest` tests for the API methods;
  - command tests against a fake ClickUp, checking that an invalid status never sends a write.

  The command tests need one small change: the API base URL must be overridable. After that, a manual end-to-end pass on a real workspace.
- **Other updates:**
  - README and `skills/SKILL.md`, including new trigger phrases so the Claude skill picks up "set status" requests.
  - The help text.
  - `make build-all` to refresh the pre-built binaries.
  - Moving `--debug` output to stderr, because right now it corrupts `-o json` output.

**Decisions for you**
1. **Unquoted multi-word statuses:** should `clickup tasks status X in progress` work without quotes? I'd say yes. The ID is always the first argument, so the rest can only be the status.
2. **Typo suggestions:** should a near-miss get "did you mean"? I'd skip it for now, since the full list is short and already shown.
3. **Success output:** one line like `ID: old -> new`, and the updated task as JSON with `-o json`? I'd say yes.

## Simulated user turn 1

APPROVED
Going with your recommendations on all three: yes to unquoted multi-word statuses, no "did you mean" for now, and yes to the one-line output plus `-o json`.

## Executor turn 2

The plan is final. Both files now list your three choices as approved decisions, and I've taken out the open questions:

- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

I haven't implemented anything.
