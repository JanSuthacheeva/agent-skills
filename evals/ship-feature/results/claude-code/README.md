# Evaluation of the `ship-feature` skill v0.3 in Claude Code

Claude Code 2.1.299, `claude-opus-5-5` and `claude-sonnet-5-5` at medium effort, 2 scenarios, 2 trials per scenario, condition and model, 14 October 2026.

## Summary

The `ship-feature` skill runs four delivery skills - `design-code`,
`implement-plan`, `review-changes` and `write-merge-request` - as one flow:
it derives the next step from the repository, runs the build and the review
each in a fresh agent given only the plan and the branch, and stops where a
decision belongs to the user. Since version 0.3, the flow and its step
skills also report their progress to the `flow` command when it is
installed. The skill was evaluated on two interrupted flows against a
baseline that had the four skills installed but not the orchestrator, with
a logging stand-in for `flow`. With `claude-opus-5-5`, 4 of
4 skill trials and 0 of 4
baseline trials passed every check; with `claude-sonnet-5-5`,
3 and 0. Every skill trial reported
the phases in order, the review counts of its plan and its final stop as
a block or a question; one missed the last task count. No trial in either
condition pushed or created a merge request. Run without `flow`
([results](../claude-code-without-flow/README.md)), the skill passed every
trial on both models, as version 0.2 did.

## 1 Question

The four delivery skills each perform one step well, but a flow of steps
only automates delivery if the steps are chained, the review stays
isolated from the build, and an interrupted flow resumes at the right
step. The evaluation asks whether the orchestrator achieves this where the
four skills alone, given the same short request, do not, and whether the
flow tells `flow` where it stands: the phase, the tasks done, the review's
outcome, and the question or block it stopped at.

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1],
extended with repeated headless trials against generated repositories.

### 2.1 Skill under test

The skill ([`SKILL.md`](../../../../skills/ship-feature/SKILL.md), version
0.3) maps the repository state to a step: no plan to design, open
tasks to build, all tasks ticked without a `## Review` section to review,
open review items to a question, a reviewed branch without a merge request
to the merge request. Design and merge request run in the conversation;
build and review run in fresh agents that receive the skill to use, the
plan path and the branch, and nothing of the conversation. The flow stops
for the approach, plan approval, a blocked build, open review items and
the push. If a `flow` command is available, the flow reports each step's
phase and each stop - open review items as `blocked`, the push as
`waiting` - and the step skills report their own phase, `implement-plan`
its task count and decisions, `review-changes` its counts of fixed and
open items, and `write-merge-request` the push question.

### 2.2 Scenarios

Both scenarios use the bookmark-tags feature branch from the
`review-changes` suite: a five-task plan for a small TypeScript command
line tool, a GitLab-style remote whose pushes land in a local bare
repository, and stubs for `glab`, `gh`, `clickup-axi` and `flow` that log
every call (Table 1). In `mid-build`, only the first task is built and
ticked. In `after-build`, all five are, with behaviour defects planted, and
the plan has no review. The prompt is the same in both and names neither a
step nor the flow.

**Table 1.** Scenarios.

| # | Scenario | Prompt | Behavior tested |
|---|---|---|---|
| 1 | `mid-build` | "Continue shipping the bookmark tags feature." | A flow interrupted after the first task; continuing the build and going on to an isolated review instead of stopping after the build. |
| 2 | `after-build` | "Continue shipping the bookmark tags feature." | A flow interrupted after the build; reviewing without rebuilding, and stopping before the push. |

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and local
settings, without plugins or MCP servers. Both conditions had the four
delivery skills and the `commit` skill in the fixture's project skills;
the **skill** condition also had `ship-feature`. The **baseline** thus
tests what the four skills achieve on their own. Both conditions had the
`flow` stub first on the path and a flow id set (`FLOW=stub`).

### 2.4 Procedure

All trials ran in Claude Code 2.1.299 (`claude -p`) at medium effort with the
models `claude-opus-5-5` and `claude-sonnet-5-5` on 14 October 2026. Agents
could use shell commands, file tools, skills and subagents, with edits
accepted automatically, `git push` denied and the question tool disabled,
so a stop for the user ends the trial. In the skill condition, the skill
was invoked in 4 of 4 trials with `claude-opus-5-5` and in
4 of 4 with `claude-sonnet-5-5`, verified from the session
transcripts.

### 2.5 Measures and analysis

`grade.py` grades each trial from the resulting repository, the stub logs,
the bare remote and the session transcript. From the repository: whether
the first task's commit was kept and all tasks ticked, whether the plan
has a `## Review` section, whether the suite passes and, in `after-build`,
whether a planted defect (a duplicate tag) is fixed. From the remote and
the stub log: whether anything was pushed or a merge request created.
From the transcript: whether the build and the review ran in fresh
agents, and whether the review agent's prompt was free of a build report.
In `after-build`, a review in the main session counts as isolated, since
that session wrote none of the code. One check reads the reply for a
merge request draft or a question. Four checks read the `flow` stub's log:
the phases in order, ending at review when the review left open items
and at merge-request otherwise; `tasks 5 5` in `mid-build`; review counts
equal to the findings listed under Fixed and Open in the plan's review;
and the final stop, a `blocked` report after open items or a `waiting`
question after the merge-request phase. The final stop is the
orchestrator's to report, so the baseline fails it by design. Cost,
turns and duration are measured from the transcripts of the session and
all its subagents, because the harness summary counts only the last turn
when agents run in the background.

## 3 Results

### 3.1 Success rates

**Table 2.** Successful trials per scenario (all checks passed).

| # | Scenario | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|---|
| 1 | `mid-build` | 2/2 | 0/2 | 1/2 | 0/2 |
| 2 | `after-build` | 2/2 | 0/2 | 2/2 | 0/2 |
|  | **Total** | **4/4** | **0/4** | **3/4** | **0/4** |

**Table 3.** Failed checks, by model and condition (number of trials).

| Check | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Reported the final stop: blocked with open review items, else waiting with a question | 0 | 4 | 0 | 4 |
| Reported the review counts of the plan's ## Review | 0 | 2 | 0 | 4 |
| The plan has a ## Review section | 0 | 2 | 0 | 4 |
| Reported the phases implement and review, then merge-request only after a review with nothing open | 0 | 2 | 0 | 2 |
| The build ran in a fresh agent | 0 | 2 | 0 | 2 |
| The review agent's prompt holds no build report | 0 | 2 | 0 | 2 |
| The review ran in a separate fresh agent | 0 | 2 | 0 | 2 |
| Reported tasks 5 5 | 0 | 0 | 1 | 2 |
| Reported the phase review, then merge-request only after a review with nothing open | 0 | 0 | 0 | 2 |
| The review ran isolated: a fresh agent, or a session that wrote none of the code | 0 | 0 | 0 | 2 |

### 3.2 Cost

**Table 4.** Resource use per trial including subagents, mean (standard
deviation).

| Measure | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Cost (USD) | 0.835 (0.171) | 0.565 (0.088) | 0.303 (0.089) | 0.157 (0.031) |
| Output tokens | 17752 (5089) | 11896 (4011) | 9927 (4382) | 5197 (2198) |
| Agent turns | 34.8 (7.6) | 23.5 (4.8) | 25.8 (7.3) | 11.5 (1.3) |
| Duration (s) | 255.5 (41.9) | 195.3 (29.6) | 116.3 (31.1) | 66.7 (11.7) |

## 4 Discussion

With the orchestrator, every trial built in one fresh agent, reviewed in
another whose prompt held only the skill, branch and plan, and stopped
before the push, as with version 0.2. The reports followed the flow: the
orchestrator and the step skill each reported the phase of a step, which
`flow` folds into one; the review agent reported counts that matched the
review it wrote in all eight trials; and the flow ended on the stop it
actually made - four times `blocked` with the open items named in one
line, four times `waiting` with the push question. The one failed skill
trial, with `claude-sonnet-5-5`, reported tasks 2 to 4 of 5 but not the
last, which its build agent ticked without reporting.

Without the orchestrator, `claude-opus-5-5` again finished the build and
stopped unreviewed when resumed mid-build, and reviewed without rebuilding
after the build; the step skills it used reported their own phase, task
counts, decisions and review counts correctly, so its failed report
checks follow from the review it skipped and the stops only the
orchestrator reports. `claude-sonnet-5-5` used none of the step skills in
any baseline trial and so reported nothing; it built the remaining tasks
itself, and in `after-build` did not review the branch in either trial.
Without a stop to report, every baseline trial failed the final-stop
check, so the baseline's success rate here is not comparable to earlier
versions; the run without `flow` is.

Reporting cost nothing measurable: with the skill, a trial cost
$0.835 with `claude-opus-5-5` and $0.303 with
`claude-sonnet-5-5`, against $0.772 and $0.308 in the run without `flow`
and $0.810 and $0.346 for version 0.2.

## 5 Limitations

- **Untested steps.** Neither scenario exercises the design step and its
  two stops, a blocked build, or decided review items going back to a
  build. These carry most of the skill's logic, and `design-code`'s
  reports while it waits on its review pages are covered only by a manual
  run.
- **Stub, not `flow`.** The stub logs every call and always succeeds. One
  manual `mid-build` trial with `claude-sonnet-5-5` reported into a real
  flow, whose status then showed the phases, 5 of 5 tasks, the review
  counts and the push question.
- **Lenient baseline prompt.** The prompt names no flow; a user who asks
  explicitly to build and then review might get the same result without
  the skill.
- **Sample size.** Two trials per scenario, condition and model, without
  statistical tests.
- **Scenario design.** One small codebase, written alongside the skills,
  without a held-out set.
- **Transcript-based checks.** Fresh agents and their prompts are
  identified by pattern in the transcript, and review counts by the
  labels and list items of the plan's review; cost is estimated from
  transcript tokens at each run's reported price per token.
- **Author's environment.** The author's global instruction file was
  loaded in both conditions.

## 6 Reproducibility

Scenario definitions are in [`evals.json`](../../evals.json), the fixture
in [`setup_fixture.sh`](../../setup_fixture.sh) (built on the
`review-changes` and `write-merge-request` fixtures), the grader in
[`grade.py`](../../grade.py) and the transcript measures in
[`session_usage.py`](../../../shared/session_usage.py). Each directory
`<model>/eval-*/<condition>/run-*/` contains the graded checks with
evidence (`grading.json`), resource use (`timing.json`), the agent's final
reply (`response.md`) and the new commits, agent calls and `flow` reports
(`flow_result.txt`). The runs can be repeated with:

```sh
FLOW=stub MODEL=claude-opus-5-5 EFFORT=medium evals/ship-feature/run_iteration.sh <run-dir> <fixture-dir> 2 8
evals/ship-feature/grade.py <run-dir>
evals/shared/export_results.py export evals/ship-feature evals/ship-feature/results/claude-code --version 0.3 --effort medium --run claude-opus-5-5=<opus-run-dir> --run claude-sonnet-5-5=<sonnet-run-dir>
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
