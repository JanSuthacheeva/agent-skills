## Eval Prompt

/code-design plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've written the approaches page at `.lavish/tasks-status-approaches.html`. I didn't open it in a browser, as instructed. It uses Tailwind + DaisyUI (nord theme) because the repo is a CLI with no design system to match. I need you to pick a structure before I write the implementation page.

**Something you should know first:** the repo doesn't build on main right now. `DetailFormatter.FormatComments` is declared twice (`internal/output/table.go:191` and `:238`), so `go build ./...` and `make check` both fail. Whichever approach you pick, the plan's first step will be deleting the older copy at `:237-279`, which doesn't wrap text.

**What I found in the code:**
- `tasks` is one Cobra command that takes at most one argument (`internal/commands/tasks.go:24-39`). We can add `status` as a subcommand of it and `clickup tasks HGAI-1217` will keep working.
- The API client can only do GETs and never sends a request body (`internal/api/client.go:42-52`). Changing a status needs it to send a body and gain a `Put` method.
- Task data only carries the list's id and name, not its statuses (`pkg/models/task.go:80-84`). We'll need a new `GET /list/{id}` call to get them.

**The three approaches:**
- **A. Check first, in the command (my recommendation).** The command fetches the task, then its list, and checks the status with a small `models.List.FindStatus` helper. It ignores upper/lower case and sends ClickUp's exact name. Only then does it send the PUT. This mirrors how `getTask` already fetches a task and then its parent. The cost is 3 HTTP calls instead of 1.
- **B. Send the change first, explain on failure.** The PUT goes out straight away. Only if ClickUp rejects it do we fetch the list to show the valid statuses. It's 1 call when the status is right, but it depends on an undocumented ClickUp error code, and we can't ignore case without the list.
- **C. Put the check in the API client.** A `Client.SetTaskStatus` method does all three calls and returns a typed `InvalidStatusError`. Today every client method maps to exactly one endpoint, and C would break that pattern to allow reuse that nothing needs yet.

Which one do you want: A, B, C, or a mix? Answer here or use the form on the page. Once you choose, I'll build the implementation page.

## Simulated user turn 1

A. Validate up front in the command. It's fine to delete the older duplicate `FormatComments` as the first step.

## Executor turn 2

I've written the implementation page at `.lavish/tasks-status-implementation.html`. I didn't open it in a browser, as instructed, and there's no Markdown plan yet. I'll write `.lavish/tasks-status.md` once you approve.

**The design:**
- **Step 0:** delete the second `DetailFormatter.FormatComments` (`internal/output/table.go:237-279`, the copy that doesn't wrap text) so the repo builds again.
- **`internal/commands/tasks_status.go` (new):**
  - `tasksStatusCmd` registers itself on `tasksCmd` in `init()`.
  - `runTasksStatus(cmd, args)` calls `setTaskStatus(w io.Writer, taskID, statusName string) error`, which does GetTask, then GetList, then FindStatus, then UpdateTaskStatus.
  - `invalidStatusError(statusName, task, list) error` builds the error that lists the valid statuses.
- **`internal/api/lists.go` (new):** `GetList(listID string) (*models.List, error)` calls `GET /list/{id}`.
- **`internal/api/tasks.go`:**
  - `UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)` sends a PUT with an `updateTaskRequest{Status}` body.
  - A new `addCustomTaskIDParams` helper replaces the custom-ID query code that `GetTask` and `GetTaskComments` each repeat today.
- **`internal/api/client.go`:** `doRequest` takes a `payload interface{}` and sends it as JSON. A new `Put` method uses it.
- **`pkg/models/list.go` (new):** `List{ID, Name, Statuses []Status}` with two helpers:
  - `FindStatus(name) (Status, bool)` matches ignoring case and spaces at either end.
  - `StatusNames() []string` returns the names in workflow order.
- **Docs:** the help text for `tasks` and the root command, `README.md`, `skills/SKILL.md`, and a `make build-all` to refresh the pre-built binaries in `bin/`.

**I depart from existing code in two places:**
- `setTaskStatus` takes an `io.Writer` instead of writing straight to `os.Stdout`, so tests can check its output.
- I pulled the custom-ID query code into a helper rather than copying it a third time.

**Behaviours I decided for you (all listed on the page):**
- Matching ignores case.
- If the task is already in that status, it prints a note, sends nothing to ClickUp and exits 0.
- An invalid status exits 1 and lists the valid statuses one per line, marking the current one with `(current)`.
- I'm assuming `GET /list/{id}` returns statuses the list inherits from its folder or space. That's unverified; the end-to-end test against a real workspace will check it.

**Two open questions (there's a form for each on the page):**
1. **Multi-word statuses:** should the words after the task ID be joined, so `clickup tasks status HGAI-1217 in progress` works without quotes? I recommend joining. The alternative is to require exactly two arguments, so the status has to be quoted.
2. **`--output json`:** should the command print the updated task as JSON? I recommend not adding it and printing just one confirmation line, like `HGAI-1217: to do -> in progress`.

Answer those, and tell me about any other changes or that the design is approved, and I'll write the Markdown plan.

## Simulated user turn 2

APPROVED. Q1: join trailing args. Q2: confirmation line only, no `--output json`.

## Executor turn 3

The plan is written. Nothing has been implemented, no lavish session was opened or ended, and no commits were made.

- **Review page:** `.lavish/tasks-status-implementation.html`. I replaced the open questions with a "Decisions made during review" section and marked the page approved.
- **Markdown plan:** `.lavish/tasks-status.md`. It's written for a later session to implement from, and links to the review page.

It records both of your answers:
- **Multi-word statuses:** the words after the task ID are joined, so `clickup tasks status HGAI-1217 in progress` works without quotes.
- **Output:** the command prints one confirmation line, with no `--output json` option.

The plan starts by deleting the second copy of `FormatComments`, the one that doesn't wrap text, so the repo builds again. One thing is still unverified: that ClickUp returns statuses a list inherits from its folder or space. The plan's end-to-end test against a real workspace checks that before anything ships.
