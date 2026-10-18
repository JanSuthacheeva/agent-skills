# Plan: rename setup-flow to setup-saaio

Approaches page: https://claude.ai/artifact/T3j2J2iKcVqGS8DzAVNLJZ. Source of the
names: `~/projects/saaio/docs/repository.md` (saaio PR #39).

## Decision

flow is now saaio. Approach B: rename the skill and its eval suite, then re-run
the eval so the published results describe the shipped skill. "A flow" stays the
word for a unit of work; only the product name changes. Records of earlier runs
(ship-feature results and reports, `docs/flow-handover.md`,
`.claude/plans/plan-skills-flow-reporting.md`) stay as written.

Also decided:

- The skill no longer asks for a `.gitignore` entry: saaio adds `.saaio/worktrees/`
  to `.git/info/exclude` itself. The eval check for it goes too.
- After the merge, `~/.claude/skills/setup-flow` is replaced by a
  `~/.claude/skills/setup-saaio` link (outside the repo, not part of the branch).

## Name map

| flow | saaio |
| --- | --- |
| `flow` (binary, product) | `saaio` |
| `github.com/JanSuthacheeva/flow` | `github.com/JanSuthacheeva/saaio` |
| `.flow/setup`, `.flow/teardown`, `.flow/config.toml` | `.saaio/setup`, `.saaio/teardown`, `.saaio/config.toml` |
| `.flow/worktrees/<name>` | `.saaio/worktrees/<name>` |
| `FLOW_SLOT`, `FLOW_WORKTREE`, `FLOW_REPO` | `SAAIO_SLOT`, `SAAIO_WORKTREE`, `SAAIO_REPO` |
| `FLOW_NAME`, `FLOW_ID` | `SAAIO_FLOW_NAME`, `SAAIO_FLOW_ID` |
| `flow start`, `flow clear`, `flow remove`, `flow status --all` | `saaio start`, `saaio clear`, `saaio remove`, `saaio status --all` |
| skill `setup-flow`, scratch `setup-flow-check` | `setup-saaio`, `setup-saaio-check` |

Kept: "flows", "a flow's name", "unfinished flows", "real flows" (units of work)
and the default branch `flow/<name>`, which saaio still uses.

## Units

- `skills/setup-saaio/SKILL.md` (moved from `skills/setup-flow/`): name,
  description and triggers ("set up saaio", "get this repo ready for saaio",
  "the saaio setup/teardown hooks", "Not for installing saaio itself or for
  starting a flow"), section "What saaio gives the hooks", every path, variable
  and command per the map, version `0.1` to `0.2`. Step 6 becomes "Make them
  executable": `chmod +x` both scripts, and a note that saaio keeps
  `.saaio/worktrees/` out of git itself (`.git/info/exclude`), so no
  `.gitignore` change is needed. Hand-over step 9 then names only the compose
  change as taking effect once committed.
- `evals/setup-saaio/` (moved from `evals/setup-flow/`):
  - `evals.json`: `skill_name`, prompts ("get this repo ready for saaio", "two
    saaio workers", "set up saaio for this sail project"), expected outputs and
    assertions per the map; the assertion ".gitignore ignores .flow/worktrees"
    is removed.
  - `run_trials.sh`: comment, skill path, and the context line both conditions
    get: "saaio runs .saaio/setup and .saaio/teardown in each worker's git
    worktree (.saaio/worktrees/<name>) with SAAIO_SLOT (1-20), SAAIO_WORKTREE,
    SAAIO_REPO, SAAIO_FLOW_NAME and SAAIO_FLOW_ID set."
  - `grade.py`: docstring, hook paths, worktree path, the env dict
    (`SAAIO_SLOT="7"`, `SAAIO_WORKTREE`, `SAAIO_REPO`,
    `SAAIO_FLOW_NAME="grade-check"`, `SAAIO_FLOW_ID="grade-check"`), the
    dry-run regex (`setup-saaio-check`), assertion prefixes; the `.gitignore`
    branch is removed. "Play flow" becomes "play saaio".
    Found while building: the dry-run check matched only the skill's words
    ("dry run", "scratch worktree") and failed baselines that reported a test
    as "tested" or "simulated workers"; it now accepts those, and the new run
    was re-tallied for that check.
  - `setup_fixture.sh`: comment.
  - `results/claude-code/`: replaced by the new run (README written in the
    shape of the old one, `summary.json`, per-trial outputs).
- `README.md`: setup row (link, name, `.saaio/setup`, `.saaio/teardown`,
  `SAAIO_SLOT`, new numbers), install line, the paragraph under the table
  ("[saaio](https://github.com/JanSuthacheeva/saaio) follows them through
  Claude Code's own hooks ... `setup-saaio` gets a repo ready for saaio's
  parallel workers"), and the ship-feature row: it "reports its stop to
  saaio (then called `flow`)" and the closing clause names saaio.

## Call chains

1. `run_iteration.sh <it> <fixtures> 2` -> `run_trials.sh` per eval, config and
   trial -> `setup_fixture.sh` builds the repo -> `claude -p` with the prompt
   and the saaio context line -> `grade.py` plays saaio on slot 7 with the
   `SAAIO_*` env -> `<run>/grading.json`.
2. Error path: Docker not running -> the dry run and grader's containers fail;
   start it with `open -a Docker` and wait for `docker info` before running.

## Test seams

- Skill and suite: a grep for `FLOW_`, `.flow`, `setup-flow` and
  `JanSuthacheeva/flow` over live files returns nothing outside the kept
  records.
- `grade.py`: grades a hand-written correct solution 8 of 8 (9 minus the
  dropped check) and the untouched repo low, as before.
- The eval run itself is the end-to-end check.

## Assumptions

- Version 0.2 for setup-saaio; no other skill changes, so no other bumps.
- The new results README keeps the old one's structure and notes that v0.1 was
  measured as setup-flow (link to the git history).
- `report-without-flow.md` and `claude-code-without-flow/` keep their names:
  they are records, and the README links them as such.

## Tasks

- [x] Move `skills/setup-flow` to `skills/setup-saaio` and rewrite SKILL.md per the name map, step 6 without `.gitignore`, version 0.2
- [x] Move `evals/setup-flow` to `evals/setup-saaio` and rename `evals.json`, `run_trials.sh`, `grade.py`, `setup_fixture.sh`; drop the `.gitignore` assertion and its grader branch; check `grade.py` on a hand-written solution
- [x] Update `README.md`: setup-saaio row and install line, the saaio paragraph, the ship-feature row
- [x] Re-run the setup-saaio eval with Docker (`run_iteration.sh`, 2 trials) and replace `results/claude-code/` and the README numbers
- [x] End-to-end: grep the live files for old names, install the skill from the branch with `npx skills add` into a scratch dir and read its frontmatter
- [x] Tighten the commit check in `grade.py` and `evals.json` (committed, or the reply says workers get it once committed), drop the unused "Nothing was committed" branch, re-tally and re-export the results

## Review

Reviewed in an isolated agent against `~/projects/saaio/docs/repository.md`
and `~/projects/saaio/src` (main at 763453d).

**Fixed**

- The skill said a failing setup blocks the flow with "its last output
  line". saaio reports the last stderr line and reads stdout only when
  stderr is empty (`src/workspace.rs` `last_line`; the docs say "last
  error line"), so a failure echoed to stdout after `docker compose`
  wrote progress to stderr would show compose's line. Step text now says
  to end failures on stderr. fe671e3. Text-only, after the eval run;
  reviewed by the same agent, not independently.

**Open**

- The check "The response says the compose change reaches flows once
  committed" is `re.search("commit", response)`. Every trial in this run
  committed, so any "committed" passes it; it no longer measures the
  hand-over. Recommendation: match the claim itself (committed + reach /
  worktrees / flows) in a later eval iteration.
- `summary.json` metadata says `runs_per_configuration: 3` with 2 trials
  per scenario (also on main; it counts scenarios). Cosmetic.
- `grade.py` keeps a "Nothing was committed" branch no assertion uses
  (also on main). Harmless.

**Where to look**

1. `skills/setup-saaio/SKILL.md` "What saaio gives the hooks" and step 6:
   every name checked against saaio's docs and source (`SAAIO_*` from
   `launch/worktree.rs` `hook_env`, the executable check and
   `.git/info/exclude` in `workspace.rs`, `saaio status --all`). Correct.
2. `README.md` setup-saaio row: 42/42 both ways, baseline edits
   `.gitignore` 5/6, README 4/6, `.env.example` 2/6, 0.28 vs 0.20 USD -
   verified against the local `workspace/iteration-2` runs.
3. `grade.py` dry-run regex widening: re-tally makes the baseline 42/42
   (36/42 under the old pattern), so the check no longer separates the
   conditions either.

Routine, skim: the `evals/` renames, `run_trials.sh`, `setup_fixture.sh`,
`evals.json` (all mechanical per the name map).

**Checks**

No test suite or lint. `py_compile` on `grade.py` and `bash -n` on the
eval scripts pass at fe671e3; the eval last ran at 9d55e03 (only the
plan and one skill sentence changed since). A grep of live files for
`FLOW_`, `.flow/`, `setup-flow` and `JanSuthacheeva/flow` finds only the
kept records.

**Decided after review**

- The commit check is tightened now, not later: it grades only the reply
  and the repo, which the run kept, so it can be re-tallied without a new
  run.
- The unused "Nothing was committed" branch goes.
- `runs_per_configuration` stays: skill-creator's `aggregate_benchmark.py`
  writes it.

## Review 2

Isolated agent, commits after aef8a11 (3cf4318) against the last task and
"Decided after review".

**Fixed**

- The new fallback (reply says workers get it once committed) matched any
  sentence naming commit and a worktree, worker or flow: "Nothing was
  committed; review the worktree diff first." passed. It also split
  sentences at every dot, so "Commit compose.yaml so new worktrees get
  it." failed. A sentence now needs commit, a worker/worktree/flow and an
  effect verb (reach, pick, get, see, start, use), split at sentence ends.
  Shown and checked on hand-written sentences. 46a4197. Reviewed by the
  same agent in a second pass, not independently.

**Open**

- The fallback is still a word heuristic: "use" also matches "user", and
  a negated hand-over ("I did not commit, so flows will not see it")
  passes, which is arguably right. The v0.2 run never reaches it - all
  four compose trials committed - so it is untested by real replies.
  Recommendation: accept for now; an LLM grader is the real fix if it
  starts to matter.

**Where to look**

1. `evals/setup-saaio/grade.py` `compose_committed` and the commit
   verdict: committed means the compose file differs from the base at
   HEAD and has no uncommitted edits. Correct.
2. `results/claude-code/README.md` new sentence on the compose replies:
   verified against `workspace/iteration-2` - both skill replies give the
   reason ("committed as 602d2a6, so new flows will pick it up"; "start
   from the latest commit"), neither baseline reply matches. Score
   unchanged (all four trials pass on the committed branch), matching
   `summary.json`, which equals `workspace/iteration-2/summary.json`.

Routine, skim: `evals.json` assertion text, the removed "Nothing was
committed" branch (no assertion uses it).

**Checks**

No test suite or lint. `py_compile` on `grade.py` passes at 46a4197.
The eval was not re-run; the fix does not change any v0.2 verdict.
