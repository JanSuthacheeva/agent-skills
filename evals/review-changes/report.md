<!--
Template for results/<harness>/README.md, rendered by
evals/shared/export_results.py. {{placeholders}} are filled from the
exported results. The prose in the Summary, Discussion and Limitations
interprets one specific run: review it by hand after every new export.
-->
# Evaluation of the `review-changes` skill v{{version}} in Claude Code

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}`, {{n_scenarios}} scenarios, three conditions, {{trials}} trials per scenario, condition and model, {{date_long}}.

## Summary

The `review-changes` skill instructs a coding agent to review a branch in a
context that has not seen its implementation, to prove each finding before
acting on it, to fix findings that are cheap to reverse and leave the rest
to the owner, to have production-code fixes reviewed again, and to end with
a short report of what was fixed, what remains open and where a human
should look. It was compared with an uninstructed review and with Claude
Code's built-in `/code-review` command, all three in fresh sessions, on
three branches with planted defects. In detection and repair the
conditions did not differ: every condition repaired every planted defect,
and `/code-review` failed only the check that fixes are committed, which it
does not do by design. The conditions differed in the report left for the
branch owner. A blind judge scored the skill's report at
{{opus_skill_judge}} of 40 with `{{opus_model}}`, against
{{opus_base_judge}} for the uninstructed review and {{opus_cr_judge}} for
`/code-review`, and ranked it first in {{opus_skill_firsts}} comparisons;
with `{{sonnet_model}}` the scores were {{sonnet_skill_judge}},
{{sonnet_base_judge}} and {{sonnet_cr_judge}}. The skill was the most
expensive condition.

## 1 Question

Automating review is only useful if the owner can trust the result without
re-reading the change. Two properties determine this: whether the review
finds and repairs what is wrong, and whether its report lets the owner see
what changed, which decisions remain theirs and where the residual risk
lies. A review by the agent that wrote the code is also suspected of
confirming its own choices, which is why every condition in this
evaluation ran in a session without the implementation's history. The
evaluation asks whether the skill improves either property over an
uninstructed review and over an existing review command.

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1],
extended with repeated headless trials against generated repositories and
a blind comparative judgment of the reports, as in the evaluation of the
`design-code` skill in this repository.

### 2.1 Skill under test

The skill ([`SKILL.md`](../../../../skills/review-changes/SKILL.md),
version {{version}}) has six steps: isolate the review from the
implementation's context, gather the diff, plan, project rules and a test
baseline, review every changed line in order of the cost of a miss (data,
boundaries, behavior against the plan, errors, tests, conventions), fix
proven findings that are cheap to reverse with a failing test first and
one commit each, have production-code fixes reviewed again by a fresh
agent on a smaller model, and report the fixed findings, the open ones
with recommendations, and two to four places to look in reading order.

### 2.2 Scenarios

All scenarios use a feature branch adding tags to a small TypeScript
command line tool, implemented against a written plan, with three commits
and tests that pass (Table 1). In `seeded-defects` and `vague-prompt`, the
branch contains two behavior defects, a deviation from the plan's exit
code, a silent rename of a planned method and a missing test; the prompts
differ in whether they name the plan. In `architecture`, the branch
matches the plan and behaves correctly on its happy paths, but the command
line layer reimplements the store's tagging, a parse error in the store is
swallowed so that a corrupt file is overwritten, and the store prints to
the console against the project's rules.

**Table 1.** Scenarios.

{{table_scenarios}}

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and local
settings, without plugins or MCP servers, so no condition had seen how the
branch was written. In the **skill** condition, the skill was copied into
the fixture's project skills. The **baseline** received the same prompt
without the skill. The **`/code-review`** condition replaced the prompt
with Claude Code's built-in `/code-review medium --fix`, which reviews the
branch against its target and applies its findings to the working tree.

### 2.4 Procedure

All trials ran in {{harness}} (`claude -p`) at medium effort with the
models `{{opus_model}}` and `{{sonnet_model}}`. Agents could use shell
commands, file tools and subagents, with edits accepted automatically and
`git push` denied. In the skill condition, the skill was invoked in
{{opus_skill_invoked}} trials with `{{opus_model}}` and in
{{sonnet_skill_invoked}} with `{{sonnet_model}}`, verified from the session
transcripts. The skill results with `{{opus_model}}` are from version
{{version}}; the other two conditions with that model were run once for an
earlier skill version, which does not affect them.

### 2.5 Measures and analysis

Correctness is graded by `grade.py` from the resulting repository by
exercising the behavior behind each planted defect through the command
line tool and the store: tagging twice, listing with a differently cased
tag, tagging an unknown identifier, loading a corrupt file. It further
checks that the planned method name agrees between code and plan, that a
test covers the unknown-identifier path, that the suite passes, that a
correct file stayed untouched and that fixes are committed. One check
counts the planted problems named in the reply by keyword.

The report is judged by `judge.py`. For each scenario and trial, the three
conditions' final replies and copies of their resulting repositories are
placed under shuffled labels; a headless judge on `{{opus_model}}`, given
the request and the list of planted problems, verifies at least three
claims per report against its repository and scores each report from 1 to
10 on accuracy, pointers to risk, decisions put to the owner, and
readability, then ranks the three. The judge prompt is in
[`judge.md`](../../judge.md).

## 3 Results

### 3.1 Detection and repair

With `{{opus_model}}`, {{opus_skill_pass}}, {{opus_base_pass}} and
{{opus_cr_pass}} of {{opus_n_trials}} trials passed every check in the
skill, baseline and `/code-review` conditions. With `{{sonnet_model}}`,
the counts were {{sonnet_skill_pass}}, {{sonnet_base_pass}} and
{{sonnet_cr_pass}}. Table 2 lists them per scenario and Table 3 the failed
checks.

**Table 2.** Successful trials per scenario (all checks passed).

{{table_results}}

**Table 3.** Failed checks, by model and condition (number of trials).

{{table_failures}}

### 3.2 Report quality

**Table 4.** Blind judgment of the owner report, mean score per criterion
(1-10), total of 40 with standard deviation, and mean rank among the three
conditions (1 is best).

{{table_judge}}

### 3.3 Cost

**Table 5.** Resource use per trial, mean (standard deviation). Cost
includes subagents started by the session; output tokens do not. The
harness reported no token or turn counts for the `/code-review` command
(n/a).

{{table_cost}}

## 4 Discussion

The planted defects did not separate the conditions. A fresh session asked
to review the branch found and repaired the behavior defects, the plan
deviations and the architectural defects, including the silent data loss,
whether or not the prompt named the plan, and so did `/code-review`. For
detection, the isolation of the review appears to matter more than its
instructions; this evaluation did not test a non-isolated review.

The reports differed markedly. The uninstructed review produced accurate,
readable narratives but resolved user-visible questions on its own, for
example by turning a missing option value into an error, and seldom told
the owner where to look. `/code-review` produced a structured list of
findings that was accurate but hard to read as an owner and put no
decisions to the owner. The skill's report separated fixed findings with
their commits, open decisions with a recommendation, and a reading order
that started at the code where stored data was at risk and named the
routine parts. These are the properties the judge rewarded under risk and
decisions, where the differences were largest.

Version 0.1 of the skill had the fixes reviewed by a fresh agent on the
same large model, which raised cost per trial by about 80% over the
baseline with `{{opus_model}}`; delegating that review to a smaller model
in version 0.2 reduced the difference without a change in the judged
quality.

## 5 Limitations

- **Judge.** The judge is a language model from the same family as the
  reviewed configurations and was given the list of planted problems,
  which a real owner would not have. Its scores are a proxy for an owner's
  judgment, not a measurement of it.
- **Easy defects.** All conditions repaired every planted defect, so the
  scenarios cannot show differences in detection; harder or subtler
  defects might.
- **Sample size and dependence.** Three trials per scenario, condition and
  model; trials within a scenario share a branch.
- **Scenario design.** One small codebase, written alongside the skill,
  without a held-out set.
- **Uncounted subagent tokens.** The harness's token counts exclude
  subagents, so the skill's re-review of fixes appears in cost but not in
  output tokens.
- **Author's environment.** The author's global instruction file was
  loaded in all conditions.

## 6 Reproducibility

Scenario definitions and planted problems are in
[`evals.json`](../../evals.json), the fixture in [`fixture/`](../../fixture/)
and [`setup_fixture.sh`](../../setup_fixture.sh), the grader in
[`grade.py`](../../grade.py) and the judge in [`judge.py`](../../judge.py)
and [`judge.md`](../../judge.md). Each directory
`<model>/eval-*/<condition>/run-*/` contains the graded checks with
evidence (`grading.json`), resource use (`timing.json`), the final reply
(`response.md`) and the commits made (`review_result.txt`);
`<model>/judge/run-*/` contains the unblinded verdicts. The runs can be
repeated with:

```sh
CONFIGS="with_skill without_skill code_review" MODEL={{opus_model}} evals/review-changes/run_iteration.sh <run-dir> <fixture-dir> 3 5
evals/review-changes/grade.py <run-dir>
evals/review-changes/judge.py <run-dir> 1,2,3
evals/shared/export_results.py export evals/review-changes {{out_dir}} --version {{version}} --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
