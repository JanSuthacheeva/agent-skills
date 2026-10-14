## Eval Prompt

/superpowers:brainstorming plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I'm treating this as **bounded**: it adds one subcommand to the existing `tasks` command and one write method to the API client, so I'll put a short design in chat and skip the full spec. Tell me if you'd rather go the heavier route.

**What I found in the code**
- `tasks [task_id]` takes one positional argument (`internal/commands/tasks.go:38`). A `status` subcommand can sit alongside it because Cobra checks for subcommand names first. `tasks HGAI-1217` keeps working, but no task ID could ever be the literal word `status`.
- `tasks` already has a `--status/-s` filter flag. It's local to `tasks`, so it won't clash with the subcommand, though the two names are close.
- The API client only sends GET requests. `doRequest` always sends an empty body (`internal/api/client.go:51`), so it needs to accept a JSON body before we can PUT.
- The task response already includes `list.id`. `GET /list/{id}` returns the statuses that list actually uses, including ones inherited from its folder or space. So the check costs three calls: get the task, get its list, then PUT the update.
- Custom IDs like `HGAI-1217` need `custom_task_ids` and `team_id` query params. `GetTask` already handles that, and the PUT needs the same.

**My understanding of what you want**
- **You said:** a `clickup tasks status <id> <status>` command that changes the status. It checks the name against the statuses of the task's own list. If the name isn't valid, it shows the valid ones.
- **I'm assuming:**
  - On a bad name it exits with an error and lists the valid statuses in the list's order. It doesn't call the API to update anything.
  - On success it prints one line, e.g. `HGAI-1217: in progress -> review`.
  - It sends ClickUp's own spelling of the status, not what you typed.
  - Setting a task to the status it already has does nothing and says so.
  - `README.md` and `skills/SKILL.md` get the new command documented.

**One question before I write the design:** how loose should matching be?

- **A. Exact, ignoring case** (my recommendation). `review` matches `Review`, but `rev` is rejected and you get the list. It's predictable, and it never moves a task to a status you didn't mean.
- **B. A plus unique prefixes.** `prog` resolves to `in progress` if nothing else starts with `prog`. If several statuses match, it's rejected and the matches are shown. Faster to type, but a typo can land on the wrong status.

## Simulated user turn 1

Option A: exact, ignoring case. Your assumptions look fine, and bounded with a short design in chat works for me.

## Executor turn 2

The design is ready for your review. I haven't written any code yet.

- **HTML:** `.lavish/tasks-status-command.html`. This repo has no design system of its own, so it uses Lavish's fallback (Tailwind and DaisyUI, `nord` theme).
- **Markdown:** `.lavish/tasks-status-command.md`

**How it works**

`clickup tasks status <id> <status>` is a new subcommand on `tasks`, in a new file `internal/commands/tasks_status.go`. It takes exactly two arguments, so multi-word statuses need quotes. It makes three API calls:

1. `GET /task/{id}` gets the current status and the task's list ID.
2. `GET /list/{list_id}` gets the statuses that list uses, including inherited ones.
3. If the name matches, `PUT /task/{id}` sets the status using ClickUp's spelling.

The name is checked between calls 2 and 3. If it doesn't match (exact, ignoring case), the command exits with an error listing the valid statuses in list order, and nothing is updated. If the task already has that status, it prints a note and exits 0. On success it prints `HGAI-1217: in progress -> review`.

**Changes**
- **`internal/api/client.go`:** requests can now carry a JSON body, and there's a new `Put` method. This is the only change to existing request code.
- **`internal/api/tasks.go`:**
  - Adds `UpdateTaskStatus`.
  - The custom-ID query params move into a shared `taskIDQuery` helper. `GetTask` and `GetTaskComments` each have their own copy today; both switch to the helper.
- **New `internal/api/lists.go`:** `GetList`.
- **New `pkg/models/list.go`:** a `List` model with `FindStatus` and `StatusNames`. The matching lives here as a plain function, so it's easy to test.
- **Docs:** help examples, `README.md`, and `skills/SKILL.md`.

**Testing (tests first)**
- Unit tests for the matching.
- API tests against a fake local server (`httptest`), covering the PUT method, path and body, and the custom-ID params.
- A test for the exact error text.
- Then `make check`, and a run of the built binary against a real workspace, confirming the result in the ClickUp UI.

**One unrelated fix I'd like to include:** `--debug` prints to stdout (`internal/api/client.go:49`), which breaks `--output json` and would mix into the new success line. I'd move it to stderr as a separate commit.

Should I go ahead with this design, including the debug fix?

## Simulated user turn 2

APPROVED. Go ahead with the design, including the separate debug-to-stderr commit.

## Executor turn 3

I've marked both plan files as approved, with the stdout-to-stderr fix for `--debug` included:

- `.lavish/tasks-status-command.md`
- `.lavish/tasks-status-command.html`

The plan lays out six commits, in this order:
1. **API:** requests can carry a JSON body, a new `Put` method, and a shared `taskIDQuery` helper.
2. **Models:** a `List` model with `FindStatus` and `StatusNames`.
3. **API:** `GetList` and `UpdateTaskStatus`.
4. **Command:** the `tasks status` subcommand.
5. **Docs:** `README.md` and `skills/SKILL.md`.
6. **Debug output:** `--debug` moves from stdout to stderr.

I've stopped there as you asked, so there's no implementation code and nothing committed.
