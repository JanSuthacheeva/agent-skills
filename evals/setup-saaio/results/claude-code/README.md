# Evaluation of the `setup-saaio` skill v0.2 in Claude Code

Claude Code 2.1.302, `claude-opus-5-5` at medium effort, 3 scenarios, 2 trials per scenario and
condition, 18 October 2026. A first look, not a statistical claim: 6 trials per condition.

## Setup

Each scenario is a throwaway repository: a compose project with hard-coded ports and a fixed
`container_name`, a plain Node dev server on 5173, and a Sail-style project whose compose file
already reads `APP_PORT` and `FORWARD_REDIS_PORT`. Both conditions are told how saaio runs
`.saaio/setup` and `.saaio/teardown` and which variables it sets; only the skill condition has the
skill.

The grader does not trust the run's report. It plays saaio: a fresh worktree on slot 7 with the
run's uncommitted changes applied (as a commit would bring them), `.saaio/setup`, a request to the
service (or `npm run dev`), `.saaio/teardown`, and a look for containers, worktrees and branches the
run left behind. A hand-written correct solution scores 8 of 8; the untouched repository 1 of 8.

## Results

| | with skill | without skill |
| --- | --- | --- |
| checks passed | 42 of 42 | 42 of 42 |
| time per trial | 49 s | 47 s |
| tokens per trial (excluding cache reads) | 23.1k | 14.9k |
| cost per trial | 0.28 USD | 0.20 USD |

The checks no longer separate the conditions. Every trial in both made the ports configurable
with today's ports as defaults, wrote hooks that served on the slot port in the grader's
worktree, tested them next to each other and reported what answered where.

The difference is in what else changed. The skill trials touched only the hooks, the compose
file and, for the dev server, `package.json` (nothing read `.env` before). The baseline trials
added `.saaio/worktrees/` to `.gitignore` in 5 of 6 (saaio already excludes it), edited the
README in 4 and `.env.example` in 2, and one moved `main` onto a test commit during its test and
had to put it back. Both skill replies in the compose scenario said why new workers get the
change (it is committed, and worktrees start from the last commit); neither baseline reply did.
The skill costs about 0.08 USD more per trial.

Every trial in both conditions committed. The sessions read the author's global instructions
("commit as you go"), which the skill counts as asking.

## Changes since v0.1

- Renamed from `setup-flow` with the tool (flow is now saaio): `.saaio/`, `SAAIO_*`. The v0.1
  results, 44 of 45 checks with the skill and 38 of 50 without, are in this folder's git history.
- The skill no longer asks for a `.gitignore` entry, and the check for it is gone.
- The dry-run check read only the skill's own words ("dry run", "scratch worktree"), so it failed
  baseline replies that reported a test as "tested" or "simulated workers". It now accepts those;
  this run was re-tallied for that one check. Under the old pattern the baseline scored 36 of 42.
- The commit check passed any reply with the word "commit" in it. It now passes when the compose
  change is committed, or when the reply says workers get it only once it is; this run was
  re-tallied for it with no change in score.

Reproduce: `./run_iteration.sh workspace/iteration-N workspace/fixtures 2` (Docker running; trials
run one at a time, as their dry runs would share ports).
