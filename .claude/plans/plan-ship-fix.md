# Plan: ship-fix and diagnose-bug

Implementation page: https://claude.ai/artifact/4S4FCS3TUBBMNY4iWwuy6j
(approaches: https://claude.ai/artifact/3ALFHc5QhsQLL4YAo4aB3n)

## Decision

A fix flow for saaio's coming kinds of flows (feature, fix, research). Two new skills:

- `diagnose-bug` (step): reproduces a bug end to end the way a user hits it, proves its
  root cause by experiment and writes a fix plan whose first task is the regression test
  plus the fix and whose last is the end-to-end check. Changes no code, commits nothing.
- `ship-fix` (orchestrator): `ship-feature` with `diagnose-bug` in place of `design-code`,
  then `implement-plan`, `review-changes` (fresh agent) and `write-merge-request`
  unchanged. Holds no method of its own.

Decided in review:

- Task 1 of a fix plan is "add the regression test (fails today with X), then fix the
  cause", one green commit. The test is written first and seen failing in the build.
- `ship-fix` always stops for approval of the fix plan.
- Order: `diagnose-bug` is built, passes the authoring checks, and its eval is run
  against `superpowers:systematic-debugging` (7.0.0) and no skill and published, before
  `ship-fix` is built.
- Both skills follow Anthropic's skill authoring guidance, the skill-creator conventions
  and this repo's conventions (see Authoring rules), checked before any eval runs.

## Units

### `skills/diagnose-bug/SKILL.md` (new)

```
---
name: diagnose-bug
description: >-
  Reproduces a reported bug end to end the way a user hits it, traces it
  to its root cause and proves the cause with an experiment, then writes a
  fix plan whose first task is a failing regression test and whose last is
  the end-to-end check - without changing any code. Use when the user asks
  to diagnose, reproduce or find the cause of a bug, says "why does X
  happen", "look into SHOP-311" or hands over a bug report or ticket.
  Not for building the fix (implement-plan, ship-fix) or for features
  (design-code).
metadata:
    author: Jan Suthacheeva
    version: "0.1"
---
## 1. Read the report      expected vs actual, steps, environment; ticket via a tool
                           if one can read it; unclear expected behaviour -> ask
## 2. Reproduce            the real command, request or page, with the reported
                           input; record exact steps and observed output
                           (detail: references/reproduce.md)
## 3. Find the root cause  trace back to where the state first goes wrong; test
                           each hypothesis by experiment; explain every symptom
                           and when it was introduced (git log -S / blame)
## 4. Decide the fix       fix where it first goes wrong, not where it shows;
                           siblings with the same mistake; data already damaged;
                           sort choices into assume / ask (cost to reverse)
## 5. Write the plan       project's plan location, else
                           docs/plans/<YYYY-MM-DD>-fix-<slug>.md, in the format of
                           references/fix-plan-format.md
## 6. Hand over            root cause in two sentences, evidence, plan path,
                           open questions; leave the tree as found but the plan
```

Stops: not reproducible (no plan; what was tried, what would help), expected behaviour
unclear, open questions in the plan. The description wording is a starting point; the
trigger eval may change it.

### `skills/diagnose-bug/references/` (new)

```
reproduce.md   read in step 2: reproducing by kind of surface - command line, HTTP
               API, browser page, background job or queue, data-dependent,
               intermittent (repeat counts, timing, seeds); recording a
               reproduction someone else can rerun
fix-plan-format.md  read in step 5: the fix plan template (see Data) with one short
               filled-in example
```

### `skills/ship-fix/SKILL.md` (new)

```
---
name: ship-fix
description: >-
  Takes a bug from report or ticket to an open merge request by running
  diagnose-bug, implement-plan, review-changes and write-merge-request in
  order - the build in this conversation after a compaction, the review in
  a fresh agent - stopping only where a decision belongs to the user, and
  resuming from what the repository shows after an interruption. Use when
  the user asks to fix a bug or ticket all the way through, says "fix
  SHOP-311", "ship this fix" or "continue fixing". Not for features
  (ship-feature) or a single step on its own.
metadata:
    author: Jan Suthacheeva
    version: "0.1"
---
## 1. Find where it stands  ship-feature's table; "No fix plan" -> Diagnose;
                            "fix plan not committed on a fix branch" -> approval
## 2. Diagnose              diagnose-bug here; stops: not reproducible, unclear
                            expected behaviour, open questions, plan approval;
                            then a fix branch + commit the plan; ask for /compact
                            and "continue fixing"
## 3. Build                 = ship-feature 3, plus: a regression test that passes or
                            fails for another reason stops the build (diagnose again)
## 4. Review                = ship-feature 4
## 5. Merge request         = ship-feature 5
## Stops                    report unclear or not reproducible, plan approval and
                            the compaction, a test that disproves the diagnosis,
                            blocked build or red base, open review items, push
```

Sections 3 to 5 and the stops are copied from `skills/ship-feature/SKILL.md` with the
wording adapted, not referenced, so the skill stands alone. No references directory.

### `evals/shared/forge_stubs.sh` (new)

```
forge_stubs <dest> <tickets.json>   # bin/ stubs for clickup-axi, glab, gh logging to
                                    # <dest>/calls.jsonl; clickup-axi answers
                                    # `tasks <id>` from tickets.json, else exits 1
forge_remote <dest>                 # bare <dest>/origin.git as pushurl of a
                                    # GitLab-looking origin, run inside the repo
```

Sourced, not executed. `evals/write-merge-request/setup_fixture.sh` replaces its
`stubs()` and `remote()` with these, its SHOP-217 ticket in a tickets file; graded
behaviour unchanged.

### `evals/diagnose-bug/` (new)

```
evals.json           tags-lost, not-reproducible, tags-spread
fixture/src/*.ts     tags app, correct except BookmarkStore.save() writes through
                     toRecord(), a field list from before tags (tags dropped on add)
fixture/test/*.ts    green suite that misses the bug
tickets.json         SHOP-311, SHOP-312, SHOP-313 as the clickup-axi stub returns them
trigger-queries.json the 20 trigger queries for run_eval.py
setup_fixture.sh     <eval-name> <dest>: repo on main, stubs
run_trial.sh         <eval> <prompt> <config> <run-dir> <fixture-root>
                     config: with_skill | systematic_debugging | without_skill
run_iteration.sh     every eval x config x N trials
grade.py             <iteration-dir>: diagnosis and contract checks
report.md            source of results/claude-code/README.md
```

### `evals/ship-fix/` (new)

```
evals.json           new-bug, approved-plan
fixture/plan.md      the approved fix plan for SHOP-311
setup_fixture.sh     on ../diagnose-bug/setup_fixture.sh + forge_remote; approved-plan
                     commits plan.md on fix/SHOP-311-tags-lost
run_trial.sh, run_iteration.sh, grade.py, report.md   as ship-feature's
                     configs: with_skill (4 step skills + commit + ship-fix) |
                     without_skill (same without ship-fix)
```

### `README.md` (modified)

Table rows for `diagnose-bug` and `ship-fix` with eval results, install lines in
alphabetical order, flow paragraph names the fix flow
(`diagnose-bug` -> `implement-plan` -> `review-changes` -> `write-merge-request`, run by
`ship-fix`).

## Data: the fix plan (references/fix-plan-format.md)

```
# Fix: <what the user sees, one line>

Report: <ticket id and title, or the report quoted>

## Report          expected, actual, the reporter's steps and environment
## Reproduction    exact commands / requests / clicks, input data, observed output,
                   before any change; how often it fails
## Root cause      file:line where it first goes wrong, the mechanism, the
                   experiment that proves it, the commit that introduced it
## Fix             what changes in which unit and why there; changed signatures
## Also affected   same mistake elsewhere; data already written wrong
## Assumptions
## Open questions  numbered, each with a recommendation
## Tasks
- [ ] Add <test> in <file> (fails today with <message>), then fix <unit>
- [ ] ... further tasks only if the fix needs them
- [ ] End-to-end: run the reproduction again and see <expected>
```

Checkboxes only under `## Tasks`.

## Call chains

A. "Fix SHOP-311" (new report)

1. User -> ship-fix: "fix SHOP-311"
2. ship-fix -> repo: plan, branch, MR? none -> Diagnose; read the ticket if a tool can
3. ship-fix -> diagnose-bug(report), in this conversation
4. diagnose-bug -> app: reproduce end to end; observed output recorded
5. diagnose-bug -> app/tests: experiments until every symptom is explained
6. diagnose-bug -> plan file: write; working tree otherwise as found
7. ship-fix -> User: stop for approval with root cause, evidence, open questions
8. ship-fix -> git: branch named after the ticket, commit the plan (commit skill)
9. ship-fix -> User: /compact, then "continue fixing"

Errors: not reproducible at 4 -> no plan, no branch, report what was tried and what would
help, ask. Expected behaviour unclear at 3/4 -> ask before any plan. Fix expensive to
reverse (stored data, public surface, user-visible change beyond the expected behaviour,
repair of damaged data) -> open question in the plan, answered at the approval stop.

B. "Continue fixing" (after approval)

1. ship-fix -> repo: plan with open boxes -> Build
2. ship-fix -> implement-plan(plan): task 1 writes the regression test, sees it fail for
   the reason the plan names, fixes the cause, commits
3. implement-plan -> app: last task reruns the reproduction, shows the expected output
4. ship-fix -> fresh agent(review-changes, branch, target, plan path, green commit)
5. ship-fix -> plan ## Review: Open empty -> go on; else stop for decisions, write them as
   tasks, build again
6. ship-fix -> write-merge-request: show title and description; push only on the user's
   word

Errors: the test does not fail as the plan says, or passes before the fix -> diagnosis is
wrong; implement-plan blocks; ship-fix puts it to the user, recommending a new diagnosis.
Blocked build, red base, open review items: as ship-feature.

C. diagnose-bug alone: steps 1 to 6 of A, then root cause, evidence, plan path and open
questions to the user; no branch, no commit, no fix unless asked.

## Authoring rules

- Frontmatter: `name` lowercase with hyphens, <= 64 chars, equals the folder;
  `description` <= 1024 chars, third person, what + when with users' phrases, slightly
  pushy, "Not for ..." naming neighbours; `metadata.author`, quoted `version`.
- Body: concise, imperative, gives the why; assumes a capable model; one term per
  concept; no time-sensitive facts; agent-agnostic. Well under 500 lines, target 100-170.
- Progressive disclosure: detail used in one step goes to `references/`, one level deep,
  linked with when to read it. `ship-fix` has none.
- Checks before any eval: skill-creator `scripts/quick_validate.py`; component review by
  a fresh reviewer (`component-reviewer-clara`), findings fixed or answered; trigger eval
  with skill-creator `scripts/run_eval.py`, 20 queries (10 should trigger, 10 near misses:
  ship-feature, implement-plan, review-changes, "make this failing test pass", "add a
  feature"), `scripts/run_loop.py` if any query misfires.

## Test seams

- diagnose-bug `tags-lost`, prompt "Look into SHOP-311."; ticket: "Tags disappear: I
  tagged bookmarks, added a new one, and `bm list --tag work` shows nothing. I think
  list --tag is broken."
  - Diagnosis (all conditions): reproduced through the CLI (transcript); cause named is
    `save`/`toRecord` in `src/store.ts`; any code change is there, not in `add` or
    `listTagged`; a regression test is named or written that fails on today's code; tags
    already lost are named.
  - Contract (diagnose-bug only): `src/` and `test/` unchanged, nothing committed; plan
    in the fix-plan format, first task the regression test, last the end-to-end check.
- diagnose-bug `tags-spread` (added in the build, when the two scenarios above hit a
  ceiling for every condition in the smoke run), prompt "Look into SHOP-313."; ticket:
  tagging one bookmark tags all of them since an update. Cause: `fromRecord()` gives every
  record without `tags` one shared `noTags` array and `tag()` pushes into it, so only a
  file written before tags shows it. Diagnosis: reproduced through the CLI with such a
  file; the shared array named; any source change in `fromRecord` and stops the spread;
  regression test; wrongly tagged bookmarks named. Contract as for `tags-lost`.
- diagnose-bug `not-reproducible`, prompt "Look into SHOP-312."; ticket: titles with
  quotes break the file (they do not).
  - Diagnosis: tried through the CLI; no code changed; reply says it did not reproduce
    and asks for details. Contract: no plan written.
- ship-fix `new-bug`, "Fix SHOP-311 all the way to a merge request.": fix plan with the
  right cause; no code changed; nothing committed to main; nothing pushed; reply asks to
  approve the plan.
- ship-fix `approved-plan`, plan committed on the fix branch, "Continue fixing
  SHOP-311.": build in the session; regression test fails on the pre-fix source and
  passes after; tags survive `bm add` via the CLI; review in a fresh agent without a
  build report; `## Review` in the plan; `npm test` green; nothing pushed, no MR; reply
  drafts the MR or puts open items.
- Runs: Opus 5.5 and Sonnet 5.5, medium effort. diagnose-bug 3 conditions x 2 scenarios
  x 3 trials, 3 scenarios (54, about 22 USD); ship-fix 2 x 2 x 2 (16, about 10 USD).
  write-merge-request's suite once after the stub extraction.

## Assumptions

- diagnose-bug never commits or branches and removes its debug output and scratch tests;
  ship-fix commits the plan after approval.
- Fix plan file `<YYYY-MM-DD>-fix-<slug>.md` in the project's plan location, else
  `docs/plans/`.
- Not reproducible means no plan and no branch.
- Damaged data is always listed; repairing it is an open question.
- Branch named after the ticket id when there is one, or the repo's convention; saaio
  workers keep their `flow/<name>` branch.
- Both skills start at `0.1`.
- saaio's fix kind (phases diagnose, implement, review, merge-request; first prompt
  `/ship-fix {request}`) is configured in saaio, not here.
- Linking the skills into `~/.claude/skills` happens after the merge, outside the branch.

## Decided in the build

- The fix plan reference is `references/fix-plan-format.md`: the plan path hook refuses
  `*-plan.md` outside `.claude/plans/`.
- Trigger eval (Opus 5.5, 3 runs per query): 19 of 20. The miss, "fix SHOP-311 all the way
  to a merge request", triggers diagnose-bug because ship-fix does not exist yet; it is
  re-tested in ship-fix's trigger eval. `run_eval.py` must run with `--num-workers 1`: its
  parallel workers share one commands directory, so each run sees all workers' copies.
- Trigger evals with the sibling installed as a competitor (Opus 5.5, 3 runs per query):
  ship-fix 20 of 20 with diagnose-bug present, diagnose-bug 20 of 20 with ship-fix present,
  after the ship-fix review added "only diagnosing (diagnose-bug)" to its exclusions.
- ship-fix component review applied: resume finds an unapproved fix plan and the fix
  branch, a disproved diagnosis goes back through diagnose-bug (which rewrites the plan in
  place) and approval, and review tasks go before the end-to-end task, which is unticked.
- write-merge-request after the stub extraction (Opus, one trial each): 10 of 12 cells match
  the published grades; ticket-title without the skill guessed `clickup-axi task` instead
  of `tasks` (refused by old and new stub alike) and review-guide with the skill wrote a
  10-line review section. Run-to-run variation, not the stubs.
- `export_results.py` reports a grader's parts (diagnosis, contract) separately and knows
  the `systematic_debugging` condition.

## Tasks

### diagnose-bug

- [x] Write `skills/diagnose-bug/SKILL.md`, `references/reproduce.md` and `references/fix-plan-format.md` per Units and Data
- [x] Authoring checks on diagnose-bug: `quick_validate.py`, component review in a fresh agent, findings fixed or answered
- [x] Trigger eval of diagnose-bug's description (20 queries) with `run_eval.py`, improved with `run_loop.py` if any misfires
- [x] Extract `evals/shared/forge_stubs.sh` (`forge_stubs`, `forge_remote`) and use it in `evals/write-merge-request/setup_fixture.sh`; prove every write-merge-request fixture builds the same repo and stub answers as before
- [x] Build `evals/diagnose-bug/` fixture and `setup_fixture.sh`: suite green, bug reproduced through the CLI, `not-reproducible` report does not reproduce
- [x] Write `evals.json`, `run_trial.sh` (three configs), `run_iteration.sh` and `grade.py` (diagnosis and contract checks); smoke one trial per config and grade it
- [x] Run the diagnose-bug eval on Opus and Sonnet, export results, write `results/claude-code/README.md`; README table row and install line
- [x] Re-run the write-merge-request eval once after the stub extraction and confirm the same grades

### ship-fix

- [x] Write `skills/ship-fix/SKILL.md` per Units
- [x] Authoring checks and trigger eval on ship-fix, as for diagnose-bug
- [x] Build `evals/ship-fix/` (fixture plan, `setup_fixture.sh`, runner, `grade.py`); smoke one trial per config
- [ ] Run the ship-fix eval on Opus and Sonnet, export results, write its README; README row, install line and flow paragraph
- [ ] End-to-end: in a scratch copy of the diagnose-bug fixture with both skills installed, run `/ship-fix SHOP-311` as saaio would start it, through the approval stop, then "continue fixing" to the MR draft
