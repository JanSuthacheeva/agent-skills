## Eval Prompt

/superpowers:brainstorming plan how we'd add a `clickup tasks status <id> <status>` command that changes a task's status. It should validate against the statuses of the task's list and show the valid ones if it's wrong.

## Executor turn 1

I'm treating this as **bounded**: it's a new subcommand on the existing `tasks` command plus a small addition to the API client. If you'd rather have a full spec, tell me and I'll switch to that.

**What I took from the codebase**
- `tasks` takes an optional `[task_id]` argument (`internal/commands/tasks.go:24`). A `status` subcommand can sit beside that without breaking `clickup tasks <ID>`. The only cost is that a task whose ID is literally `status` couldn't be viewed, which doesn't matter in practice.
- The API client can only send GETs right now. `doRequest` has no request body (`internal/api/client.go:42`), so the client will need a `Put` that sends JSON.
- `GetTask` already handles custom IDs like `HGAI-1217` and returns `task.List.ID`. That gives us the flow: read the task, read its list's statuses, check the requested status, then update.
- There are no API-layer tests yet. Because `baseURL` is a field on the client, tests can point it at a local fake server.

**My understanding** (what you said vs. what I assumed)
- You said: `clickup tasks status <id> <status>` changes a task's status. It checks the status against the task's list, and if the status is invalid it shows the valid ones.
- I assumed: success means the status is changed in one command, with no browser and no guessing at names. An invalid status fails with exit code 1 and makes no change. The skill doc and README get the new command too.

Correct anything that's off. The first question that shapes the design:

**How loosely should the status name match?**
- **A (recommended):** Ignore case, but otherwise match exactly. `"In Progress"` matches `in progress`, and we send the list's own spelling to the API. ClickUp itself treats statuses this way.
- **B:** Exact match only, case included.
- **C:** Like A, but a prefix that fits only one status also counts (`prog` becomes `in progress`). If the prefix fits more than one, it fails and lists the candidates. This is faster to type, but there's a small risk of changing to a status you didn't mean.

## Simulated user turn 1

Option A. Case-insensitive, otherwise exact, and send the list's own spelling to the API.

## Executor turn 2

Got it, option A.

**What should a successful change print?**
- **A (recommended):** One line by default, such as `HGAI-1217: to do -> in progress`. With `--output json`, it prints the updated task (the PUT response) as JSON, the same way other commands support scripting and the Claude skill.
- **B:** Only the one-line confirmation, with no `--output` support.
- **C:** The full task detail view, the same as `clickup tasks <ID>`.

Also: if the task is already in the requested status, I'd make the command a no-op. It would print `HGAI-1217 is already "in progress"`, exit 0, and skip the PUT. Does that sound right?

## Simulated user turn 2

Option A for the output. And yes, the already-in-that-status no-op is right: print the notice, skip the PUT, exit 0.

## Executor turn 3

I've written the design as a plan in `.lavish/tasks-status-command.html`, with a Markdown copy in `.lavish/tasks-status-command.md`. No code is written yet.

**How it works**
1. `GetTask(id)` fetches the task, its list ID and its current status.
2. If the task is already in the requested status (ignoring case), it prints the notice and exits 0, with no further calls.
3. Otherwise `GetList(task.List.ID)` gets the list's statuses and checks your input against them, ignoring case.
4. If there's no match, it prints `Error: invalid status "done" for list "Sprint 12". Valid statuses:` followed by the statuses in board order, and exits 1.
5. If there's a match, it sends the change using the list's spelling and the task's internal ID. It then prints `HGAI-1217: to do -> in progress`, or the updated task as JSON with `--output json`.

**Files**
- **New:** `pkg/models/list.go` (the list type and the name matching), `internal/api/lists.go` and `internal/commands/tasks_status.go`.
- **Changed:**
  - `internal/api/client.go`: the client can't send a request body yet, so this adds that and a `Put` method.
  - `internal/api/tasks.go`: adds the status update call. It also pulls the custom-ID query handling, currently copied in `GetTask` and `GetTaskComments`, into one helper.
  - `tasks.go`: `--output` currently belongs only to `tasks`, so it changes to a flag the new subcommand inherits.
  - Help text, README, `skills/SKILL.md` and the pre-built binaries.

**A fix included along the way:** debug output currently goes to stdout (`internal/api/client.go:49`), so `--debug --output json` produces invalid JSON. I'll send it to stderr while I'm changing that function.

**Testing:** I'll write tests first for the name matching, the client against a local fake server, and the command logic with a fake client. Then `make check`, and a real-workspace run on a throwaway task covering:
- custom and native IDs
- wrong case
- an invalid status (checking the exit code)
- the no-op
- JSON output
- a list that inherits its statuses from its folder or space

Decision for you: with `--output json`, when the task is already in the requested status, I plan to send the notice to stderr and print the task as JSON to stdout, so scripts always get a task back. Is that OK, and is the design approved?

## Simulated user turn 3

APPROVED. The JSON no-op handling (notice to stderr, task JSON to stdout) is fine.

## Executor turn 4

The plan is final and marked approved in both files. As you asked, I've stopped at planning; no code has been written.

- `.lavish/tasks-status-command.html`
- `.lavish/tasks-status-command.md`

**What changed since your approval:** I added your answer on JSON output to the decisions. When the task is already in the requested status and `--output json` is set, the notice goes to stderr and the task JSON goes to stdout. I also removed that question from both files, since it's now settled.

**Styling:** the HTML page uses the fallback Tailwind and DaisyUI look with the `nord` theme. This is a command-line project with no design system of its own to match.

**Order of work:**
1. Name matching and the list type
2. Request bodies, `Put`, and debug output moved to stderr
3. The list fetch and status update calls, plus the shared custom-ID helper
4. The `tasks status` subcommand
5. Help text, README and the Claude skill doc
6. Rebuilt binaries

Each step gets tests written first and its own commit. A run against a real workspace comes last.
