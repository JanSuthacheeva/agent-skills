## Eval Prompt

plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

The plan is written. I haven't written any code yet.

- `.lavish/tasks-status-command.html` - the visual version.
- `.lavish/tasks-status-command.md` - the same plan as Markdown.

**How the command works**
1. **Read the task:** `GetTask` already handles custom IDs like `HGAI-1217` and returns the task's current status and its list.
2. **Read the list:** a new `GetList` fetches the list's statuses, including ones inherited from the folder or space.
3. **Match the status:** trim the input and compare it without regard to case.
   - **No match:** fail with exit code 1 and print the valid statuses in workflow order. Nothing is written.
   - **Same as the current status:** print a note, exit 0 and send no update.
4. **Write:** send the update with the list's own spelling of the status, using the task's internal ID so the custom-ID handling isn't needed.

**Where the code goes**
- **Matching logic:** pure functions in a new `pkg/models/list.go`, so it can be tested without the API.
- **API client:** today it only reads. It gets the ability to send a request body, a `Put` method, `GetList` and `UpdateTaskStatus`. These get the first HTTP-level tests in the repo, using a fake local server.
- **Command:** a new `internal/commands/tasks_status.go` that only wires the steps together. Its error type produces the multi-line "valid statuses" message.
- **Docs:** the help text, README and `skills/SKILL.md` get the new command. The pre-built binaries in `bin/` get rebuilt with `make build-all`.

I built a small throwaway program on the same Cobra version to check that adding a `status` subcommand under `tasks` doesn't break `tasks`, `tasks <id>` or `--status` filtering. It doesn't. A typo like `tasks stauts` is treated as a task ID and fails as unknown, which is what happens today.

The design tool told me to match the project's own look, but a CLI has none, so the HTML uses the tool's default styling.

**Decisions for you**
1. **Status names with spaces:** should `clickup tasks status X in progress` work without quotes? I recommend yes, by joining the words. Requiring exactly two arguments would force quotes and fail with a confusing "accepts 2 arg(s), received 3" error.
2. **Success output:** I recommend just the one-line confirmation (`HGAI-1217: in progress -> review`). The alternative is to also support `-o json` and print the updated task, which would help scripts and the Claude skill.

## Simulated user turn 1

APPROVED
Go with both recommendations: join the args so quotes aren't needed, and print only the one-line confirmation.

## Executor turn 2

I've updated both plan files with your two decisions, and that finishes the plan. I haven't implemented anything.

- **Multi-word statuses:** everything after the task ID is joined with spaces, so `clickup tasks status X in progress` works without quotes. Quoted input still works.
- **Success output:** only the one-line confirmation, like `HGAI-1217: in progress -> review`. The command gets no `-o` flag.

The open-questions section in both files is now an approved-decisions section.

Files are in `.lavish/`:
- tasks-status-command.html
- tasks-status-command.md
