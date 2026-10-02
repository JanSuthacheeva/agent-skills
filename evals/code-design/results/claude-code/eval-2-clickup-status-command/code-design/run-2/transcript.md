## Eval Prompt

/code-design plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

Phase 2 is ready for your decision. The comparison page is at `.lavish/tasks-status-approaches.html`. I haven't opened it in a browser or checked how it renders, as instructed.

**What I found in the code:**
- `tasks` is a single command, `tasks [task_id]`, with no subcommands (`internal/commands/tasks.go:24-39`). Adding a `status` subcommand under it won't break `clickup tasks HGAI-1217`.
- The API client is read-only right now. `doRequest` can't send a request body and `Get` is the only method exposed (`internal/api/client.go:42-96`). So every approach needs a `Put`, plus `GET /list/{id}` and `PUT /task/{id}`.
- `models.Task` already includes `List.ID` and `Status`. There is no model for a list or its statuses yet.

**The three approaches:**
- **A - The command orchestrates and the model validates (recommended).** The new subcommand fetches the task, then its list, then calls a check on a new `models.List` that just compares names (no network calls), then sends the change.
  - This copies how `getTask` already chains several client calls (`tasks.go:111-124`), and the API client keeps one method per endpoint.
  - The cost is three round trips per status change.
- **B - The API client owns the whole operation.** A single `Client.SetTaskStatus` does every step and returns a typed `InvalidStatusError`.
  - It gives the thinnest command.
  - But it puts business rules into what is currently a plain HTTP layer, and testing it would need a fake HTTP server, which the repo doesn't have.
- **C - Send the change first and explain only if it fails.** The happy path is one call.
  - But it depends on ClickUp's undocumented "status not found" error code.
  - It also can't fix the case of the input or skip a change that does nothing before sending.

**Decision needed:** which approach should I design in full: A, B, C, or a mix? You can answer here or use the form at the bottom of the page.

I'll raise these questions on the next page, each with my recommended answer:
- What the command prints on success: I'd print one line like `HGAI-1217: open -> in progress`.
- Whether it supports `-o json`.
- How the status name is matched: I'd match the full name, ignoring case.

The page uses the DaisyUI `nord` fallback theme, because this is a CLI project with no design system to match.

## Simulated user turn 1

Approach A. It matches how getTask already chains calls, and the pure validation on the model is easy to test.

## Executor turn 2

I've built the implementation design for approach A at `.lavish/tasks-status-implementation.html`. I haven't opened it in a browser or checked how it renders, as instructed. I'll write the Markdown plan only after you approve the design.

**New and changed units:**
- **New `internal/commands/tasks_status.go`:**
  - `tasksStatusCmd` takes exactly two arguments and registers itself on `tasksCmd` in `init()`.
  - `runTasksStatus` hands the arguments to `changeTaskStatus(taskID, statusName string) error`, the same way `runTasks` hands off to `getTask`.
  - `invalidStatusError(statusName string, list *models.List) error` builds the error message.
- **Changed `api/client.go`:** `doRequest(method, path string, query url.Values, body interface{})` can now send a JSON body. There's also a new `Put(path string, query url.Values, body interface{}) ([]byte, error)`.
- **New `api/lists.go`:** `GetList(listID string) (*models.List, error)`.
- **Changed `api/tasks.go`:**
  - New `UpdateTaskStatus(taskID, teamID, status string) (*models.Task, error)`, sending an unexported `updateTaskRequest{Status}`.
  - A small cleanup beyond the feature: the custom task ID handling currently duplicated in `GetTask` and `GetTaskComments` moves into one shared `addCustomTaskIDQuery` helper. Without it there would be a third copy.
- **New `pkg/models/list.go`:** `List{ID, Name, Statuses []Status}` with `FindStatus(name string) (Status, bool)` and `StatusNames() []string`. It reuses the existing `models.Status`.
- **Docs:** the help text for `tasks` and `root`, `README.md` and `skills/SKILL.md` all get the new command.

**How a status change runs:** load config, then `GetTask`, then `GetList(task.List.ID)`, then `FindStatus`. If the task is already in that status, it prints a message and stops without sending anything. Otherwise it calls `UpdateTaskStatus` and prints `HGAI-1217: open -> in progress`.

When the status is wrong, nothing is sent and it exits with code 1 and this message:
```
Error: status "doing" not found in list "Sprint 12"
Valid statuses: "open", "in progress", "review", "complete"
```

**Questions for you (each has a form on the page):**
1. **What a successful change prints.** I recommend one line and no `-o` flag for now; a flag can be added later without breaking anything. The alternatives are adding `-o json`, or showing the full task details.
2. **Task already in the requested status.** I recommend not sending the change, printing a message and exiting 0, so it's safe to run twice. The alternatives are exiting with an error, or sending the change anyway.
3. **Prefix matching (`prog` for "in progress").** I recommend accepting only the full name, ignoring case. Once people rely on prefixes they're hard to take away.

**Assumption to confirm first:** I'm assuming `GET /list/{id}` returns the list's statuses even when they're inherited from the folder or space. The first implementation step would be checking that against a real workspace.

The page also covers which existing patterns it copies (with line references), the test plan (first API tests using `httptest`, unit tests for `models.List`) and eight assumptions. It uses the DaisyUI `nord` fallback theme, the same as the approaches page.

Please answer the three questions and send any corrections. Once you approve, I'll write the plan to `.lavish/tasks-status.md`.

## Simulated user turn 2

1. One line, no `-o` flag.
2. Skip the PUT, print the message, exit 0.
3. Full name only, case-insensitive.

No corrections to the design, so go ahead and write the plan.

## Executor turn 3

The plan is written, and I didn't write any code.

- **Design page:** `.lavish/tasks-status-implementation.html`. I replaced the three open questions with a "Decisions made in review" section holding your answers. I haven't opened it in a browser or checked how it renders.
- **Markdown plan:** `.lavish/tasks-status.md`. It's what a later implementation session would work from: the decision, every unit with its file path and signatures, the data types, the call chain including errors, the test plan and the assumptions. It links back to the design page and leaves out the diagrams and reasoning.

Your three answers are in both files:
- A successful change prints one line, and there's no `-o` flag.
- If the task is already in that status, it prints a message, sends nothing and exits 0.
- Status names must match in full, ignoring case.

The first step when implementing is to check against a real workspace that `GET /list/{id}` returns statuses inherited from the folder or space. The validation depends on that.

The plan lives in `.lavish/` as you asked, not in `docs/plans/` where the repo's earlier plan is. As instructed, I haven't ended the lavish session.

## Simulated user turn 3

APPROVED
The plan matches my three answers and I have no further points.

## Executor turn 4

Planning is finished and both plan files are written:

- **Design page:** `.lavish/tasks-status-implementation.html`, now showing your three answers as decisions.
- **Markdown plan:** `.lavish/tasks-status.md`, for a later session to implement from.

The earlier comparison page is still at `.lavish/tasks-status-approaches.html`. I haven't implemented anything.
