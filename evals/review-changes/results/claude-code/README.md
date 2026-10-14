# Evaluation of the `review-changes` skill v0.2 in Claude Code

Claude Code 2.1.296, `claude-opus-5-5` and `claude-sonnet-5-5`, 3 scenarios, three conditions, 3 trials per scenario, condition and model, 14 October 2026.

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
36.0 of 40 with `claude-opus-5-5`, against
30.0 for the uninstructed review and 22.0 for
`/code-review`, and ranked it first in 9 of 9 comparisons;
with `claude-sonnet-5-5` the scores were 35.7,
29.3 and 23.1. The skill was the most
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
version 0.2) has six steps: isolate the review from the
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

| # | Scenario | Prompt | Behavior tested |
|---|---|---|---|
| 1 | `seeded-defects` | "review this branch against the plan in docs/plans/2026-10-14-bookmark-tags.md and fix what you find" | A plausible-looking branch whose tests pass but which has two behaviour bugs, an error-path drift, a silent rename and a test gap. |
| 2 | `vague-prompt` | "review my branch and fix what you find" | The same defects with a prompt that names no plan; whether the review finds the plan and project rules itself. |
| 3 | `architecture` | "review my branch and fix what you find" | A branch that matches the plan and behaves correctly but breaks a layer boundary, loses data on a corrupt file and prints from the store. |

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and local
settings, without plugins or MCP servers, so no condition had seen how the
branch was written. In the **skill** condition, the skill was copied into
the fixture's project skills. The **baseline** received the same prompt
without the skill. The **`/code-review`** condition replaced the prompt
with Claude Code's built-in `/code-review medium --fix`, which reviews the
branch against its target and applies its findings to the working tree.

### 2.4 Procedure

All trials ran in Claude Code 2.1.296 (`claude -p`) at medium effort with the
models `claude-opus-5-5` and `claude-sonnet-5-5`. Agents could use shell
commands, file tools and subagents, with edits accepted automatically and
`git push` denied. In the skill condition, the skill was invoked in
9 of 9 trials with `claude-opus-5-5` and in
9 of 9 with `claude-sonnet-5-5`, verified from the session
transcripts. The skill results with `claude-opus-5-5` are from version
0.2; the other two conditions with that model were run once for an
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
placed under shuffled labels; a headless judge on `claude-opus-5-5`, given
the request and the list of planted problems, verifies at least three
claims per report against its repository and scores each report from 1 to
10 on accuracy, pointers to risk, decisions put to the owner, and
readability, then ranks the three. The judge prompt is in
[`judge.md`](../../judge.md).

## 3 Results

### 3.1 Detection and repair

With `claude-opus-5-5`, 9, 9 and
0 of 9 trials passed every check in the
skill, baseline and `/code-review` conditions. With `claude-sonnet-5-5`,
the counts were 9, 9 and
0. Table 2 lists them per scenario and Table 3 the failed
checks.

**Table 2.** Successful trials per scenario (all checks passed).

| # | Scenario | Opus Skill | Opus Baseline | Opus `/code-review` | Sonnet Skill | Sonnet Baseline | Sonnet `/code-review` |
|---|---|---|---|---|---|---|---|
| 1 | `seeded-defects` | 3/3 | 3/3 | 0/3 | 3/3 | 3/3 | 0/3 |
| 2 | `vague-prompt` | 3/3 | 3/3 | 0/3 | 3/3 | 3/3 | 0/3 |
| 3 | `architecture` | 3/3 | 3/3 | 0/3 | 3/3 | 3/3 | 0/3 |
|  | **Total** | **9/9** | **9/9** | **0/9** | **9/9** | **9/9** | **0/9** |

**Table 3.** Failed checks, by model and condition (number of trials).

| Check | Opus Skill | Opus Baseline | Opus `/code-review` | Sonnet Skill | Sonnet Baseline | Sonnet `/code-review` |
|---|---|---|---|---|---|---|
| The fixes are committed and the working tree is clean | 0 | 0 | 9 | 0 | 0 | 9 |

### 3.2 Report quality

**Table 4.** Blind judgment of the owner report, mean score per criterion
(1-10), total of 40 with standard deviation, and mean rank among the three
conditions (1 is best).

| Model | Condition | Accuracy | Risk | Decisions | Readability | Total /40 (SD) | Mean rank |
|---|---|---|---|---|---|---|---|
| Opus | Skill | 9.0 | 9.1 | 8.9 | 9.0 | 36.0 (0.5) | 1.00 |
| Opus | Baseline | 8.9 | 7.4 | 5.7 | 8.0 | 30.0 (1.6) | 2.00 |
| Opus | `/code-review` | 6.9 | 6.6 | 4.3 | 4.2 | 22.0 (1.4) | 3.00 |
| Sonnet | Skill | 9.0 | 9.1 | 8.8 | 8.8 | 35.7 (0.9) | 1.00 |
| Sonnet | Baseline | 8.7 | 7.2 | 5.1 | 8.3 | 29.3 (1.4) | 2.00 |
| Sonnet | `/code-review` | 7.4 | 6.6 | 4.1 | 5.0 | 23.1 (1.7) | 3.00 |

### 3.3 Cost

**Table 5.** Resource use per trial, mean (standard deviation). Cost
includes subagents started by the session; output tokens do not. The
harness reported no token or turn counts for the `/code-review` command
(n/a).

| Measure | Opus Skill | Opus Baseline | Opus `/code-review` | Sonnet Skill | Sonnet Baseline | Sonnet `/code-review` |
|---|---|---|---|---|---|---|
| Cost (USD) | 0.513 (0.066) | 0.357 (0.038) | 0.255 (0.028) | 0.135 (0.018) | 0.107 (0.008) | 0.071 (0.010) |
| Output tokens | 7544 (1247) | 6451 (945) | n/a | 3693 (1247) | 2949 (401) | n/a |
| Agent turns | 20.7 (3.2) | 12.4 (2.9) | n/a | 8.6 (2.7) | 7.7 (1.1) | n/a |
| Duration (s) | 96.9 (13.9) | 63.1 (11.2) | 58.5 (6.6) | 37.6 (15.9) | 25.5 (3.1) | 22.6 (1.9) |

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
baseline with `claude-opus-5-5`; delegating that review to a smaller model
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
CONFIGS="with_skill without_skill code_review" MODEL=claude-opus-5-5 evals/review-changes/run_iteration.sh <run-dir> <fixture-dir> 3 5
evals/review-changes/grade.py <run-dir>
evals/review-changes/judge.py <run-dir> 1,2,3
evals/shared/export_results.py export evals/review-changes evals/review-changes/results/claude-code --version 0.2 --run claude-opus-5-5=<opus-run-dir> --run claude-sonnet-5-5=<sonnet-run-dir>
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
