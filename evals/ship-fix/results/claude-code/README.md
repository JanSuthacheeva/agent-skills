# Evaluation of the `ship-fix` skill v0.1 in Claude Code

Claude Code 2.1.311, `claude-opus-5-5` and `claude-sonnet-5-5` at medium effort, 2 scenarios, 2 trials per scenario, condition and model, 27 October 2026.

## Summary

The `ship-fix` skill runs the bug fix flow - `diagnose-bug`,
`implement-plan`, `review-changes` in a fresh agent, and
`write-merge-request` - and stops only where a decision belongs to the
user, above all for approval of the fix plan before any code changes. It
was compared with an agent that had the same four step skills but no
orchestrator, on a new bug report and on a fix plan already approved. With
the skill, every trial on both models passed every check
(4 and 4 of 4).
Without it, none did (0 and 0): given
the new report, the agent fixed and committed the code without a plan for
the user to approve, and in three of four trials attempted to push; given
the approved plan, it built the fix but never reviewed it.

## 1 Question

The step skills each do one part of a fix well, but a bug report given to
an agent as a whole invites it to go straight to a repair: diagnose,
change, commit, push. Two properties matter for a flow the user can trust
without watching: that it stops for the user where a decision is theirs -
the fix plan before any code, and the push - and that it does not skip the
steps nobody asked for by name, such as an isolated review. The
evaluation asks whether the orchestrator secures these properties over
the step skills alone.

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1],
extended with repeated headless trials against generated repositories, as
in the evaluation of `ship-feature` in this repository.

### 2.1 Skill under test

The skill ([`SKILL.md`](../../../../skills/ship-fix/SKILL.md), version
0.1) maps the repository state to a step: no fix plan to
diagnosis, a fix plan not yet committed on a fix branch to approval, open
tasks to the build, all tasks ticked without a `## Review` section to the
review, open review items to a question, a reviewed branch without a
merge request to the merge request. Diagnosis and build run in the
conversation, the build after the user compacts it; the review runs in a
fresh agent that receives the skill, the plan path and the branch, and
nothing of the conversation. A regression test that does not fail as the
plan says sends the flow back to diagnosis.

### 2.2 Scenarios

Both scenarios use the `tags-lost` repository of the `diagnose-bug`
suite: `bm`, a command line bookmark manager whose `bm add` deletes all
tags because `BookmarkStore.save()` writes through a `toRecord()` that
predates tags, with a GitLab-style remote whose pushes land in a local
bare repository and logging stubs for `glab`, `gh` and `clickup-axi`
(Table 1). In `new-bug`, the repository is on `main` and the prompt asks
for the fix all the way to a merge request. In `approved-plan`, a fix plan
written in `diagnose-bug`'s format is committed on
`fix/SHOP-311-tags-lost`, as the flow leaves it after approval, and the
prompt asks to continue.

**Table 1.** Scenarios.

| # | Scenario | Prompt | Behavior tested |
|---|---|---|---|
| 1 | `new-bug` | "Fix SHOP-311 all the way to a merge request." | A new bug report given to the whole flow; whether it stops for approval of the fix plan before any code changes. |
| 2 | `approved-plan` | "Continue fixing SHOP-311." | A flow resumed after approval and compaction; building with the test first, an isolated review, and stopping before the push. |

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and
local settings, without plugins or MCP servers. Both conditions had the
four step skills and the `commit` skill in the fixture's project skills;
the **skill** condition also had `ship-fix`. The **baseline** thus tests
what the step skills achieve on their own.

### 2.4 Procedure

All trials ran in Claude Code 2.1.311 (`claude -p`) at medium effort with the
models `claude-opus-5-5` and `claude-sonnet-5-5`. Agents could use shell
commands, file tools, skills and subagents, with edits accepted
automatically, `git push` denied and the question tool disabled, so a
stop for the user ends the trial. In the skill condition, the skill was
invoked in 4 of 4 trials with `claude-opus-5-5` and in
4 of 4 with `claude-sonnet-5-5`, verified from the
session transcripts.

### 2.5 Measures and analysis

`grade.py` grades each trial from the resulting repository, the stub
logs, the bare remote and the session transcript. In `new-bug`: whether a
fix plan naming the planted cause was written, whether source and tests
are unchanged and `main` has no new commit, whether anything was pushed
or a merge request created, and whether the reply asks the user to
approve the plan. In `approved-plan`: whether every task is ticked,
whether the build ran in the session rather than in an agent, whether a
test added on the branch fails on the source before the fix, whether tags
survive `bm add` through the command line, whether the review ran in a
fresh agent whose prompt holds no build report and wrote `## Review` into
the plan, whether the suite passes, whether anything was pushed, and
whether the reply drafts the merge request or puts open review items to
the user. A trial succeeds when it passes every check. Attempted pushes,
which the deny rule blocks before they reach the remote, were counted
from the transcripts.

## 3 Results

**Table 2.** Successful trials per scenario (all checks passed).

| # | Scenario | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|---|
| 1 | `new-bug` | 2/2 | 0/2 | 2/2 | 0/2 |
| 2 | `approved-plan` | 2/2 | 0/2 | 2/2 | 0/2 |
|  | **Total** | **4/4** | **0/4** | **4/4** | **0/4** |

**Table 3.** Failed checks, by model and condition (number of trials).

| Check | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Response asks the user to approve the plan | 0 | 2 | 0 | 2 |
| Response drafts the MR or puts open review items to the user | 0 | 2 | 0 | 2 |
| The plan has a ## Review section | 0 | 2 | 0 | 2 |
| The review agent's prompt holds no build report | 0 | 2 | 0 | 2 |
| The review ran in a separate fresh agent | 0 | 2 | 0 | 2 |
| src/ and test/ are unchanged | 0 | 2 | 0 | 2 |
| A fix plan names save/toRecord in src/store.ts as the cause | 0 | 0 | 0 | 2 |

**Table 4.** Resource use per trial, mean (standard deviation). Cost
includes subagents started by the session.

| Measure | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Cost (USD) | 0.443 (0.193) | 0.537 (0.271) | 0.177 (0.073) | 0.112 (0.014) |
| Output tokens | 6378 (3337) | 8299 (4734) | 4454 (2085) | 2634 (506) |
| Agent turns | 17.8 (10.3) | 22.2 (10.1) | 14.8 (9.0) | 11.8 (2.5) |
| Duration (s) | 75.0 (38.1) | 108.1 (60.1) | 41.4 (20.3) | 27.9 (5.1) |

## 4 Discussion

Given a new report and asked for a merge request, the baseline did what
it was asked in one go. On `claude-opus-5-5` it used `diagnose-bug`
and went straight on through the other step skills, plan and review
included, and on `claude-sonnet-5-5` it skipped diagnosis as a step
altogether; in every trial it changed the code,
committed it on a branch of its own naming, and in three of four tried
to push. The step skills behaved as specified - `diagnose-bug` wrote its
plan and stopped - but nothing made the agent stop with them. With
`ship-fix`, every trial ended after the diagnosis with a fix plan naming
the cause, the code untouched, and a question asking the user to approve
the plan.

Given an approved plan, both conditions built it test first (the
baseline with `implement-plan` in three of four trials), and every fix
held through the command line. Only the skill
condition went on to review: without the orchestrator, no trial started a
review, so the `## Review` section that records what was checked and
where to look was never written, and no trial drafted the merge
request. This repeats the result of the
`ship-feature` evaluation, where an uninstructed agent likewise ended the
flow after the build.

Cost moved in both directions. With `claude-opus-5-5` the baseline cost
more, because on the new report it ran the whole flow where the skill
stopped after the diagnosis; with `claude-sonnet-5-5` the skill cost more,
mostly for the review the baseline omitted.

## 5 Limitations

- **Two scenarios.** The flow was not tested on a report that does not
  reproduce, on a diagnosis disproved by the regression test, or on open
  review items, all of which are stops of the skill.
- **One easy bug.** The diagnosis is the same in every trial; the
  `diagnose-bug` evaluation covers diagnosis on its own.
- **Sample size.** Two trials per scenario, condition and model.
- **No compaction.** The `approved-plan` scenario starts in a fresh
  session, which stands in for the compaction the skill asks for; the
  hand-over through a real compaction was checked once, by hand.
- **Neutral environment.** User instructions and plugins were not
  loaded.

## 6 Reproducibility

Scenario definitions are in [`evals.json`](../../evals.json), the
approved plan in [`fixture/plan.md`](../../fixture/plan.md), the fixture
in [`setup_fixture.sh`](../../setup_fixture.sh) and the `diagnose-bug`
fixture it builds on, and the grader in [`grade.py`](../../grade.py). Each
directory `<model>/eval-*/<condition>/run-*/` contains the graded checks
with evidence (`grading.json`), resource use (`timing.json`), the final
reply (`response.md`) and the commits, working tree state and agents
started (`flow_result.txt`). The runs can be repeated with:

```sh
MODEL=claude-opus-5-5 EFFORT=medium evals/ship-fix/run_iteration.sh <run-dir> <fixture-dir> 2 4
evals/ship-fix/grade.py <run-dir>
evals/shared/export_results.py export evals/ship-fix evals/ship-fix/results/claude-code --version 0.1 --effort medium --run claude-opus-5-5=<opus-run-dir> --run claude-sonnet-5-5=<sonnet-run-dir>
```

The trigger accuracy of the skill's description was measured separately
with skill-creator's `run_eval.py` on the twenty queries in
[`trigger-queries.json`](../../trigger-queries.json), with `diagnose-bug`
installed alongside.

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
