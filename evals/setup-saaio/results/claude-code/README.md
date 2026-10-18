# Evaluation of the `setup-flow` skill v0.1 in Claude Code

Claude Code 2.1.300, `claude-opus-5-5` at medium effort, 3 scenarios, 2 trials per scenario and
condition, 15 October 2026. A first look, not a statistical claim: 6 trials per condition.

## Setup

Each scenario is a throwaway repository: a compose project with hard-coded ports and a fixed
`container_name`, a plain Node dev server on 5173, and a Sail-style project whose compose file
already reads `APP_PORT` and `FORWARD_REDIS_PORT`. Both conditions are told how flow runs
`.flow/setup` and `.flow/teardown` and which variables it sets; only the skill condition has the
skill.

The grader does not trust the run's report. It plays flow: a fresh worktree on slot 7 with the
run's uncommitted changes applied (as a commit would bring them), `.flow/setup`, a request to the
service (or `npm run dev`), `.flow/teardown`, and a look for containers, worktrees and branches the
run left behind. A hand-written correct solution scores 9 of 9; the untouched repository 1 of 9.

## Results

| | with skill | without skill |
| --- | --- | --- |
| checks passed | 44 of 45 (98%) | 38 of 50 (76%) |
| time per trial | 54 s | 51 s |
| tokens per trial (excluding cache reads) | 29.9k | 21.0k |

Both conditions made compose read its ports from variables with today's ports as defaults,
removed the fixed `container_name`, ignored `.flow/worktrees` and made the dev server read its
port from `.env`; every setup they wrote served on the slot port in the grader's worktree. The
difference is the proof: every skill trial ran setup and teardown in a scratch worktree and
reported what answered where, and none of the baseline trials did.

The one failed skill check, and every baseline trial, committed without being asked. The
sessions read the author's global instructions ("commit as you go"), so a commit there follows a
standing rule; the skill now counts such a rule as asking, and the check is dropped from later
runs. `summary.json` is this iteration's benchmark, which still includes it.

Reproduce: `./run_iteration.sh workspace/iteration-N workspace/fixtures 2` (Docker running; trials
run one at a time, as their dry runs would share ports).
