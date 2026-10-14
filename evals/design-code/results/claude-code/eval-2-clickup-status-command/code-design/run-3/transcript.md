## Eval Prompt

/code-design plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I've written the approaches page: `.lavish/tasks-status-command-approaches.html`. As instructed, I didn't open it in a browser, so it hasn't been checked visually. It uses the Tailwind + DaisyUI `nord` fallback styling, because this is a CLI project with no design system of its own.

**The build is broken on `main` right now.** `DetailFormatter.FormatComments` is declared twice (`internal/output/table.go:191` and `:238`), so `go build`, `go vet` and `make test` all fail. Whichever approach you pick, the first step will be deleting the duplicate at `:238`, which is the one without word wrapping.

What the code looks like today:
- Commands do all the coordination themselves; there's no service layer (`internal/commands/tasks.go:100-159`).
- The API client can only read. `doRequest` never sends a body, so a write needs body support and a `Put` (`internal/api/client.go:42-96`).
- `Task.List` only holds an ID and a name, so the list has to be fetched to get its statuses. `models.Status` already has the right fields (`pkg/models/task.go:55-84`).
- `status` can be a cobra subcommand of `tasks` and `clickup tasks <id>` keeps working.

**Approaches:**

| | Idea | Main cost |
|---|---|---|
| **A** (recommended) | A new `tasks_status.go` command fetches the task, then its list, checks the name, then writes, the same way `getTask` works. The name check is a pure `models.List.FindStatus` method. | 3 API calls when it succeeds. The command's own flow stays untested, as `getTask` is today. |
| **B** | A new `internal/service` with `TaskService.ChangeStatus` behind a `TaskAPI` interface, returning a typed `InvalidStatusError`. | Introduces a layer no other command uses, so the code has two patterns until `listTasks`/`getTask` are moved over too. |
| **C** | Send the update straight away and let ClickUp check it. Only if it's rejected, fetch the list and show the valid statuses. | Depends on recognising ClickUp's undocumented error codes. It also checks after the write rather than validating first as you asked. |

I recommend **A**. It matches how the code already works, and the only real logic ends up in a pure, tested method. B is the better structure once there are several commands that change tasks, but I'd do that as its own refactor that also moves the existing commands, rather than for this one command.

**Which approach do you want: A, B, C or a mix?** After that I'll build the implementation page, which will also ask:
- What the command prints on success.
- Whether `--output json` is supported.
- What happens if the task already has that status.

## Simulated user turn 1

Approach A. It matches how getTask works and keeps the logic in a pure model method.

## Executor turn 2

I've written the implementation design: `.lavish/tasks-status-command-implementation.html`. As instructed, I didn't open it or poll for annotations, so it hasn't been checked in a browser.

**The design (Approach A):**
- **New `internal/commands/tasks_status.go`:** a subcommand `status <task_id> <status>` that takes exactly 2 arguments and adds itself to `tasksCmd`. `runTasksStatus` runs the flow, and `invalidStatusError(name, task, list)` builds the error message listing the valid statuses.
- **New `pkg/models/list.go`:** a `List{ID, Name, Statuses []Status}` type with:
  - `FindStatus(name) (*Status, bool)`, which ignores case and surrounding whitespace and returns the list's own spelling of the name.
  - `StatusNames()`, which returns the names in board order.
- **New `internal/api/lists.go`:** `GetList(listID) (*models.List, error)`.
- **Changed `internal/api/tasks.go`:**
  - `UpdateTaskStatus(taskID, teamID, status) (*models.Task, error)`.
  - A `setCustomTaskIDParams` helper that pulls out the custom-ID query code currently repeated in `GetTask` and `GetTaskComments`.
- **Changed `internal/api/client.go`:** `doRequest` gets a `body` parameter, and there's a new `Put`.
- **Help text and docs:** `tasks.go`, `root.go`, `README.md` and `skills/SKILL.md` each get a usage line.
- **Step 0:** delete the duplicate `FormatComments` at `internal/output/table.go:237-279` so the code compiles again.

**Flow:** `getAPIClient` and `getConfig`, then `GetTask`, then `GetList(task.List.ID)`, then `FindStatus`, then `UpdateTaskStatus`, then print one line. If the name isn't in the list, nothing is written. The error is sent to stderr with exit 1 and lists the valid statuses in board order, marking the current one. Any API error is wrapped in a `failed to ...: %w` error, the same pattern the other commands use.

**Assumptions I made for you (all cheap to change):**
- No prefix or fuzzy matching on the status name.
- Validation uses the task's home list.
- Closed statuses such as `complete` are allowed like any other.
- There's no `--output` flag on `status`.
- `--debug` also logs the request body.

**Three questions before I write the Markdown plan:**
1. **Output on success:** one line like `HGAI-1217: to do -> in progress` (my recommendation), the full detail view, or nothing?
2. **Task already has that status:** skip the update, say so and exit 0 (my recommendation), send it anyway, or treat it as an error?
3. **Multi-word statuses:** require quotes, as in `"in progress"` (my recommendation, and it matches the documented `--status "in progress"`), or also accept `in progress` unquoted by joining the remaining arguments?

If you're happy with my recommendations, say "approved" and I'll write `.lavish/tasks-status-command.md`.

## Simulated user turn 2

1. One line: `HGAI-1217: to do -> in progress`.
2. Skip the PUT, print the notice, and exit 0.
3. Require quotes, with `ExactArgs(2)`.

Go ahead and write the plan.

## Executor turn 3

The plan is written, using your three answers. No code has been changed yet.

**Files:**
- **Plan:** `.lavish/tasks-status-command.md`. It's self-contained for an implementation session: the decision, each file's function signatures, the data types, the call chain step by step including error paths, test seams, assumptions and your review decisions.
- **Review page:** `.lavish/tasks-status-command-implementation.html`. I replaced its open questions with your three decisions. As instructed, I didn't open it or end a lavish session.

**What's settled:**
- The command takes exactly 2 arguments, so multi-word statuses must be quoted.
- It gets the task, then the task's list, checks the name against the list's statuses (ignoring case), and then sends the update.
- A successful change prints `HGAI-1217: to do -> in progress`.
- If the task already has that status, it skips the update, says so and exits 0.
- If the name isn't valid, nothing is written; the error lists the valid statuses in board order with the current one marked, and exits 1.

**Before the feature:** the plan starts by deleting the duplicate `DetailFormatter.FormatComments` at `internal/output/table.go:237-279`. Until that's done, `go build`, `go vet` and `make test` all fail on `main`.

Tell me when you want me to implement it.

## Simulated user turn 3

APPROVED
The plan matches my three answers.

## Executor turn 4

The final plan files are written and both include your review decisions:

- **Markdown plan:** `.lavish/tasks-status-command.md`
- **Implementation page:** `.lavish/tasks-status-command-implementation.html`
- **Approaches page:** `.lavish/tasks-status-command-approaches.html`

The build on `main` is still broken because of the duplicate `FormatComments` in `internal/output/table.go`. Fixing that is the plan's first step, before the feature itself.

Planning is finished and I haven't implemented anything.
