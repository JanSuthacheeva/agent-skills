<!--
Template for results/<harness>/README.md, rendered by
evals/shared/export_results.py. {{placeholders}} are filled from the
exported results. The prose in the Summary, Discussion and Limitations
interprets one specific run: review it by hand after every new export.
-->
# Evaluation of the `ship-fix` skill v{{version}} in Claude Code

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}` at {{effort}} effort, {{n_scenarios}} scenarios, {{trials}} trials per scenario, condition and model, {{date_long}}.

## Summary

The `ship-fix` skill runs the bug fix flow - `diagnose-bug`,
`implement-plan`, `review-changes` in a fresh agent, and
`write-merge-request` - and stops only where a decision belongs to the
user, above all for approval of the fix plan before any code changes. It
was compared with an agent that had the same four step skills but no
orchestrator, on a new bug report and on a fix plan already approved. With
the skill, every trial on both models passed every check
({{opus_skill_pass}} and {{sonnet_skill_pass}} of {{opus_n_trials}}).
Without it, none did ({{opus_base_pass}} and {{sonnet_base_pass}}): given
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
{{version}}) maps the repository state to a step: no fix plan to
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

{{table_scenarios}}

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and
local settings, without plugins or MCP servers. Both conditions had the
four step skills and the `commit` skill in the fixture's project skills;
the **skill** condition also had `ship-fix`. The **baseline** thus tests
what the step skills achieve on their own.

### 2.4 Procedure

All trials ran in {{harness}} (`claude -p`) at {{effort}} effort with the
models `{{opus_model}}` and `{{sonnet_model}}`. Agents could use shell
commands, file tools, skills and subagents, with edits accepted
automatically, `git push` denied and the question tool disabled, so a
stop for the user ends the trial. In the skill condition, the skill was
invoked in {{opus_skill_invoked}} trials with `{{opus_model}}` and in
{{sonnet_skill_invoked}} with `{{sonnet_model}}`, verified from the
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

{{table_results}}

**Table 3.** Failed checks, by model and condition (number of trials).

{{table_failures}}

**Table 4.** Resource use per trial, mean (standard deviation). Cost
includes subagents started by the session.

{{table_cost}}

## 4 Discussion

Given a new report and asked for a merge request, the baseline did what
it was asked in one go. On `{{opus_model}}` it used `diagnose-bug`
and went straight on through the other step skills, plan and review
included, and on `{{sonnet_model}}` it skipped diagnosis as a step
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
where to look was never written. This repeats the result of the
`ship-feature` evaluation, where an uninstructed agent likewise ended the
flow after the build.

Cost moved in both directions. With `{{opus_model}}` the baseline cost
more, because on the new report it ran the whole flow where the skill
stopped after the diagnosis; with `{{sonnet_model}}` the skill cost more,
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
MODEL={{opus_model}} EFFORT={{effort}} evals/ship-fix/run_iteration.sh <run-dir> <fixture-dir> 2 4
evals/ship-fix/grade.py <run-dir>
evals/shared/export_results.py export evals/ship-fix {{out_dir}} --version {{version}} --effort {{effort}} --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```

The trigger accuracy of the skill's description was measured separately
with skill-creator's `run_eval.py` on the twenty queries in
[`trigger-queries.json`](../../trigger-queries.json), with `diagnose-bug`
installed alongside.

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
