# Plan: the skills report into flow

Design page: `.lavish/skills-flow-reporting-implementation.html` (approaches:
`.lavish/skills-flow-reporting-approaches.html`). Source: part 1 of
`docs/flow-handover.md`.

## Decision

Every skill states once, in a reporting note near its top, that it reports
to `flow` if the command is available, and names each report inline at the
step where it happens. The skills must work exactly the same without
`flow`: no binary, no flow id (`skipped: no flow id`) or a failing report
all mean "go on".

Decided in review:

- `decision` in guided mode: only implement-plan's cheap deviations.
  design-code's assumptions are approved on its page; its decisions come
  with auto mode (part 2).
- Beyond the handover's list, the skills also report `tasks` (implement-plan)
  and `merge-request <url>` (write-merge-request). Not `delegated`.
- Evals: `flow` stub and grader checks, then rerun the ship-feature suite
  with `FLOW=stub` and `FLOW=absent` on Opus and Sonnet, and publish.
- The Claude Code adapter overwriting the skill's question at turn end
  (`claude-code-mods/flows/hooks/reporter.ts:30`) is a separate follow-up
  in claude-code-mods, not part of this plan.

## Units

### The reporting note (all five skills)

`<phase>` is `design`, `implement`, `review` or `merge-request`:

```
If a `flow` command is available, report this skill's progress to it with
`flow report`: `phase <phase>` now, `waiting "<the question>"` before every
question you put to the user and `working` once it is answered, and the
reports the steps below name. Otherwise, or when a report fails, go on -
the skill works the same without them.
```

### skills/design-code/SKILL.md - 0.7 -> 0.8

- Note with `phase design`, after the phase checklist block, before `## 1. Investigate`.
- Phase 2, replace "Open it with `npx -y lavish-axi <file>`, poll for the decision, and answer follow-up annotations until the user has chosen. The chosen approach may be a mix - take what they say literally." with:

```
Open it with `npx -y lavish-axi <file>`, report `waiting "Pick an approach
on the page"` before each poll for the decision, and answer follow-up
annotations until the user has chosen. The chosen approach may be a mix -
take what they say literally.
```

- Phase 3, replace "Open it, poll, and iterate on the user's annotations." with:

```
Open it, report `waiting "Review the implementation page"` before each
poll, and iterate on the user's annotations.
```

### skills/implement-plan/SKILL.md - 0.1 -> 0.2

- Note with `phase implement`, after the intro, before `## 1. Load`.
- Step 5:

```
5. Tick it, report `tasks <done> <total>`, and commit it as one commit,
   with the project's commit convention or skill. Plan updates from this
   task go in the same commit.
```

- "Make it" bullet, append: ``Report `decision "<the change and why, in one line>"`.``
- "Stop and ask" bullet, its last sentences become:

```
Mark the task blocked if you can, report `blocked "<what you found, in one line>"`,
explain what you found, and give your recommendation. Do not build a
workaround in the meantime.
```

### skills/review-changes/SKILL.md - 0.4 -> 0.5

- Note with `phase review`, after the intro, before `## 1. Isolate`.
- In `## 6. Summary`, before "Do not push or open a merge request unless asked.":

```
Report `review --fixed <n> --open <n>`, counting the Fixed and Open lines.
```

### skills/write-merge-request/SKILL.md - 0.7 -> 0.8

- `allowed-tools`: add `Bash(flow report:*)` before `Read`.
- Note with `phase merge-request`, after the intro, before `## Workflow`.
- Step 4:

```
4. Write the title and description (below), show them and report
   `waiting "Push and open the merge request?"`. Stop there.
```

- Step 5: "..., and give the URL." becomes ``..., give the URL and report `merge-request <url>`.``

### skills/ship-feature/SKILL.md - 0.2 -> 0.3

- Note after the intro, before `## 1. Find where it stands`:

```
If a `flow` command is available, report the flow's progress to it with
`flow report`: `phase design`, `phase implement`, `phase review` or
`phase merge-request` as each step starts, `waiting "<the question>"`
before every question you put to the user and `working` once it is
answered, and the stops below. Otherwise, or when a report fails, go on -
the flow works the same without them.
```

The phases are named, not `<the step's phase>` as first drafted: the
steps are called Design, Build, Review and Merge request, so the agent
could not derive `implement` from them.

- `## Stops`, replace from "At a stop, say in a few lines..." to "...otherwise ask the user directly." with:

```
At a stop, report it - a blocked build, a red base or open review items as
`blocked "<one line>"`, the other stops as `waiting "<the question>"` - then
say in a few lines what was found, the options and your recommendation, and
ask the user directly.
```

### evals/write-merge-request/setup_fixture.sh - `stubs()`

```
bin/flow    # appends its argv as one JSON array per line to $dest/flow.jsonl,
            # like the forge stubs; prints "flow: stub", exits 0
```

ship-feature fixtures inherit it (its setup calls this one).

### evals/ship-feature/run_trial.sh, evals/write-merge-request/run_trial.sh

Both source `evals/shared/flow_mode.sh` once the fixture is built:

```
FLOW=stub     # default: FLOW_ID=eval-trial, the stub logs every report
FLOW=absent   # removes bin/flow, unsets FLOW_ID and replaces every PATH
              # entry holding a `flow` with a directory linking the rest of
              # it, so the tools next to it stay reachable
```

### evals/{commit,implement-plan,review-changes}/run_trial.sh, evals/design-code/run_trial.py

Unset `FLOW_ID` for the trial's `claude` process, so a trial started from a
flow worker never reports into the real flow.

### evals/ship-feature/grade.py

```python
def flow_reports(fx: Path) -> list[list[str]] | None
    # flow.jsonl as argument lists in order; None when the trial ran with FLOW=absent

def review_counts(plan: str) -> tuple[int, int]
    # outermost list items under Fixed and Open in the plan's ## Review, not
    # "none"; a label is a heading, a bold label or an unindented line, and a
    # list item only when it holds nothing else, so `- Fixed duplicate tags: ...`
    # and an indented continuation line starting with "open" stay findings

def flow_check(t: str, reports: list[list[str]], plan: str) -> tuple[bool, str]
    # grades one report expectation, like check() does the others
```

New expectations, as `flow_expectations` in `evals.json` (copied to
`flow_assertions` in each eval's metadata), graded only when `flow_reports`
is not None:

- Reported the phases implement (mid-build only) and review, then
  merge-request only after a review with nothing open
- Reported `tasks 5 5` (mid-build)
- Reported `review --fixed F --open O` matching `review_counts` of the plan
- Reported the final stop: `blocked` after the review report when items are
  open (assumption 3), else `waiting` with a question ending in "?" after
  the merge-request phase

### Published results

- `FLOW=stub` runs: `evals/ship-feature/results/claude-code/`, rendered
  from `report.md`.
- `FLOW=absent` runs: `evals/ship-feature/results/claude-code-without-flow/`,
  rendered from `report-without-flow.md`.
- `evals/shared/export_results.py export ... --template <file>` picks the
  report template; `summary.json` records it so `render` reuses it.

### README.md

One sentence after the flow paragraph: with
[flow](https://github.com/JanSuthacheeva/flow) installed, the skills report
their progress to it; without it they work the same.

## Data

Nothing new is stored. Events the existing `flow report` CLI accepts:

| Event | Reported by |
|---|---|
| `phase <design\|implement\|review\|merge-request>` | each step skill at its start; ship-feature as each step starts |
| `waiting "<question>"` / `working` | every skill at its questions; design-code before each poll; write-merge-request before the push |
| `decision "<text>"` | implement-plan, per cheap deviation |
| `blocked "<reason>"` | implement-plan's expensive deviation; ship-feature's blocked build, red base, open review items |
| `tasks <done> <total>` | implement-plan per task |
| `review --fixed <n> --open <n>` | review-changes at the end |
| `merge-request <url>` | write-merge-request after creating it |

`flow.jsonl` (eval stub): one JSON array per call, the stub's argv; read by
`grade.py`, whose final-stop check takes only a `waiting` or `blocked` with
exactly one argument, so an unquoted multi-word report fails.

## Call chains

### a. design-code waits for the approach in the browser

1. design-code -> lavish-axi open(.lavish/<slug>-approaches.html): session url
2. design-code -> flow report waiting("Pick an approach on the page"): state waiting
3. design-code -> lavish-axi poll(file): blocks until feedback
4. user -> page submit(approach): queued prompt
5. lavish-axi -> design-code: feedback
6. design-code -> flow report working: state working. A follow-up round repeats 2-6.
7. Error: `flow` missing, `skipped: no flow id` or a non-zero exit -> design-code goes on; the user sees nothing.

The implementation page repeats this chain with "Review the implementation page".

### b. ship-feature: a build agent stops on an expensive deviation

1. ship-feature -> flow report phase(implement)
2. ship-feature -> build agent(implement-plan, plan path, branch)
3. implement-plan -> flow report phase(implement): same phase, folded
4. implement-plan -> flow report tasks(n, 5) after each tick
5. implement-plan -> flow report blocked("<what it found>"), returns its finding
6. ship-feature checks commits and boxes -> flow report blocked("Build blocked: <one line>") -> asks the user
7. user answers -> ship-feature -> flow report working; writes the decision into the plan, commits
8. ship-feature -> flow report phase(implement) -> new build agent (back to 2)
9. Red base: implement-plan reports failing tests in its summary as today; ship-feature makes it a stop with blocked("Red base: <failing tests>").

### c. review to merge request

1. ship-feature -> flow report phase(review) -> review agent(review-changes, branch, target, plan)
2. review-changes -> flow report phase(review); writes ## Review, commits
3. review-changes -> flow report review(--fixed F, --open O)
4. ship-feature reads ## Review; O > 0 -> flow report blocked("O open review items") -> asks; answers become tasks, back to build
5. O = 0 -> ship-feature -> flow report phase(merge-request) -> write-merge-request
6. write-merge-request -> flow report phase(merge-request); shows title and description -> flow report waiting("Push and open the merge request?")
7. user: "push" -> flow report working -> git push, glab mr create / gh pr create: url
8. write-merge-request -> flow report merge-request(url): state done
9. Error: no glab/gh or no login -> stops after 6 with the paste-ready text; the flow stays waiting.

## Test seams

- implement-plan, review-changes, write-merge-request, ship-feature: the ship-feature evals with the stub run all three steps in fresh agents, so one suite checks every report but design-code's.
- Works without flow: the same evals with `FLOW=absent`, against today's expectations and published results.
- design-code: its eval forbids `lavish-axi poll`, so only the end-to-end run covers it.
- grade.py: run against one stub and one absent trial before the full rerun.

## Assumptions

1. A failing `flow report` (unknown flow, non-zero exit) is ignored like a missing binary - reporting never stops a skill.
2. ship-feature reports the phase of each step itself, in addition to the step skill (duplicates fold).
3. Open review items are a `blocked` stop; approach, plan and push are `waiting`.
4. implement-plan reports a red base only in its summary, as today; the stop and its `blocked` are ship-feature's.
5. review-changes reports counts even without a plan; Open counts findings and open questions alike.
6. Versions bump in each skill's own commit, no separate release commits.
7. The real-flow end-to-end check uses a throwaway `flow new` flow, removed afterwards.

## Tasks

- [x] Unset `FLOW_ID` in the commit, design-code, implement-plan and review-changes trial runners; check a trial started with `FLOW_ID` set reports nothing into it
- [x] Add the `flow` stub to `evals/write-merge-request/setup_fixture.sh` `stubs()` and `FLOW=stub|absent` to the write-merge-request and ship-feature `run_trial.sh`; check both modes with one trial each
- [x] Add `flow_reports`, `review_counts` and the report expectations to `evals/ship-feature/grade.py`; check them against the stub and absent trials
- [x] design-code: reporting note, waiting before both polls, version 0.8
- [x] implement-plan: reporting note, `tasks`, `decision`, `blocked`, version 0.2
- [x] review-changes: reporting note, `review` counts, version 0.5
- [x] write-merge-request: `allowed-tools`, reporting note, push question, `merge-request <url>`, version 0.8
- [x] ship-feature: reporting note with the phase per step, stops, version 0.3
- [x] README: the sentence on reporting to flow
- [x] Rerun the ship-feature evals with `FLOW=stub` and `FLOW=absent` on Opus and Sonnet, and publish the results and report
- [x] End-to-end: a throwaway `flow new` flow, a mid-build ship-feature trial reporting into it with the real CLI, and `flow status` showing phases implement, review and merge-request, 5/5 tasks, the review counts and the push question; then remove the flow

### After review (decided by the user)

- [x] `flow` stub logs each call's argv as one JSON array per line, like the forge stubs, and `flow_reports` parses it, so an unquoted multi-word report no longer passes as quoted; regrade the published trials' workspace copies to show the results are unchanged (no paid rerun)
- [x] Harden `review_counts` in `evals/ship-feature/grade.py` so a finding line shaped like a label (`- Fixed duplicate tags: ...`) is counted as a finding, with checks for that case, `- None.` and labels with a note before the colon; regrade to show the published counts are unchanged

### After the second review (decided by the user)

- [x] `review_counts` treats a whole-line "nothing" item under a label (`- No open items.`, `- No findings.`, `- Nothing open.`) like `- None.`, while an item naming a thing (`- No test for X`) stays a finding; tests for both
- [ ] `flow_reports` fails loudly when a fixture holds the old `flow.log` and no `flow.jsonl`, naming the file and the conversion needed, instead of grading the trial as run without flow; test for it

## Review

Reviewed in isolation against `main` and this plan, including the two
follow-ups. The five skill edits, versions, `allowed-tools` and README
sentence match the plan, and every `flow report` argument matches the
real CLI's `--help`. Regrading copies of the local workspace, with the old
`flow.log` text converted to argv, reproduced every published
`grading.json` (only `npm test` timings differ), before and after the fix
below; the README numbers match the gradings. `FLOW=absent` checked with a
PATH holding `flow` next to another tool. No paid suites were rerun.

**Fixed**

- `review_counts` missed bold labels with the colon inside: a review
  written with `**Fixed:**` and `**Open:**` counted (0, 0), and
  `- **Open:** none` counted as a finding. Shown with two new tests;
  published results unchanged - 5dae6bf.

**Open**

- `review_counts` still counts `- No open items.` as one open finding,
  where an agent would report `--open 0`. No published trial wrote it.
  Recommendation: leave it; widening "none" to "no ..." would drop real
  findings like `- No test for X`.
- The local workspace fixtures hold the old `flow.log`, so regrading them
  as they are now grades stub trials as if run without flow, silently.
  Only the gitignored workspace is affected. Recommendation: leave it.

**Where to look**

1. `evals/ship-feature/grade.py` `REVIEW_LABEL` and `flow_check()`: the
   label heuristic and the four report checks behind the published
   numbers.
2. `skills/ship-feature/SKILL.md` reporting note and `## Stops`: which
   stops are `blocked` and which `waiting`.
3. `evals/shared/flow_mode.sh`: the absent mode the "works without flow"
   results rely on.

Routine, skim: the `env -u FLOW_ID` runners, `--template` in
`export_results.py`, the result files.
