# Evaluation of the `implement-plan` skill v0.1 in Claude Code

Claude Code 2.1.296, `claude-opus-5-5` and `claude-sonnet-5-5` at medium effort, 3 scenarios, 3 trials per scenario, condition and model, 14 October 2026.

## Summary

The `implement-plan` skill instructs a coding agent to build an approved
implementation plan task by task: tests first, one commit per task, the
plan's names and signatures, an end-to-end check, and a rule for changes
the code forces on the design - cheap ones are made and written back into
the plan, expensive ones stop the build. It was evaluated against a
baseline without the skill on three plans for a small TypeScript command
line tool, with two models. With `claude-opus-5-5`, both conditions passed
every check in every trial (9 of 9 versus
9 of 9). With `claude-sonnet-5-5`, the skill
condition passed every check in 9 of
9 trials and the baseline in 1 of
9: without the skill, the smaller model changed a public
file format the plan had not decided on, merged tasks into fewer commits
and left the plan out of date after deviating from it. The skill raised
mean cost per trial on both models.

## 1 Question

A plan that has been reviewed and approved is only worth as much as the
implementation's fidelity to it. Two failure modes are of interest. The
implementation can drift from the plan without saying so, which leaves the
plan wrong as a record and the reviewer unaware of the change. Or it can
follow the plan into a decision the plan did not make, such as changing a
stored format, which should have gone back to its owner. The evaluation
asks whether the skill reduces these failures relative to a capable model
given only the request to implement the plan, and whether the answer
depends on the model.

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1]:
paired configurations with and without the skill, scenario-specific graded
assertions, and aggregation into a benchmark, extended with repeated
headless trials against generated repositories.

### 2.1 Skill under test

The skill ([`SKILL.md`](../../../../skills/implement-plan/SKILL.md),
version 0.1) has four phases. The agent reads the whole plan and
the project's rules and runs the tests once; builds each task in order by
writing its tests, seeing them fail, implementing with the plan's names and
signatures and committing it with its checkbox ticked; sorts any deviation
the code forces by its cost to reverse, making cheap ones and recording
them in the plan, and stopping with a recommendation on expensive ones
(stored data, public surface, user-visible behavior); and finishes with an
end-to-end check and a short account of how the result works.

### 2.2 Scenarios

All scenarios use a command line bookmark manager written in TypeScript and
run by Node.js 22 without dependencies, with an `AGENTS.md` that states its
layering and conventions, and the same five-task plan for adding tags,
written in the format of the `design-code` skill. The scenarios differ in
how well the plan fits the code (Table 1). In `csv-store`, the plan assumes
a JSON store while the code persists a CSV file whose columns a code comment
declares a public format; storing tags therefore requires a format decision
the plan does not contain. In `plan-needs-fix`, the plan declares a
TypeScript parameter property, which the project's rules forbid because
Node.js cannot strip it; the build must deviate in a way that is cheap to
reverse.

**Table 1.** Scenarios.

| # | Scenario | Prompt | Behavior tested |
|---|---|---|---|
| 1 | `tags-plan` | "The plan in docs/plans/2026-10-14-bookmark-tags.md is approved. Implement it." | A plan that fits the code; task-by-task commits, green steps, plan fidelity and an end-to-end result. |
| 2 | `csv-store` | "The plan in docs/plans/2026-10-14-bookmark-tags.md is approved. Implement it." | A plan that is wrong about stored data; stopping at an expensive-to-reverse deviation instead of building past it. |
| 3 | `plan-needs-fix` | "The plan in docs/plans/2026-10-14-bookmark-tags.md is approved. Implement it." | A cheap deviation the code forces; whether the plan is kept true to the code and the deviation reported. |

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and local
settings, without plugins or MCP servers. In the **skill** condition, the
skill was copied into the fixture's project skills; in the **baseline**
condition it was absent. The prompt was identical in both. The author's
global instruction file remained loaded in both conditions, which includes
a rule to commit each completed unit of work; the baseline is therefore
somewhat informed about the commit discipline the skill prescribes.

### 2.4 Procedure

All trials ran in Claude Code 2.1.296 (`claude -p`) at medium effort with the
models `claude-opus-5-5` and `claude-sonnet-5-5` on 14 October 2026 or the days
before it. Each trial started from a freshly generated repository. Agents
could use shell commands and file tools with edits accepted automatically;
`git push` was denied. In the skill condition, the skill was invoked in
9 of 9 trials with `claude-opus-5-5` and in
9 of 9 with `claude-sonnet-5-5`, verified from the session
transcripts.

### 2.5 Measures and analysis

Correctness is graded by `grade.py` from the resulting repository, not from
the agent's report: the number of new commits, whether the test suite
passes at every new commit (run in a scratch worktree), the plan's
checkboxes, the signatures in the code, the command line tool exercised end
to end, the loading of a file written before tags existed, the state of the
working tree, and in `csv-store` whether the stored format and the command
line code stayed unchanged. One check per stopping scenario reads the
agent's reply for a question or recommendation. A trial is successful when
all checks of its scenario pass; this is the primary measure. Secondary
measures are the share of checks passed, cost in USD as reported by the
harness, output tokens, agent turns and duration.

Success rates are reported with Wilson score intervals [2]. Conditions are
compared per model with Fisher's exact test [3] on trial-level success,
which treats trials as independent, and with a two-sided sign test over
scenarios, which does not.

## 3 Results

### 3.1 Success rates

With `claude-opus-5-5`, 9 of 9 skill
trials (100.0%; 95% CI 70.1%-100.0%) and
9 of 9 baseline trials (100.0%;
95% CI 70.1%-100.0%) succeeded; Fisher's exact test yields
p = 1.000.

With `claude-sonnet-5-5`, 9 of 9 skill
trials (100.0%; 95% CI 70.1%-100.0%) and
1 of 9 baseline trials
(11.1%; 95% CI 2.0%-43.5%) succeeded; Fisher's exact
test yields p = 4.1e-04. The skill condition did better
in 3 scenarios, worse in 0
and equally in 0 (sign test p = 0.2500).

**Table 2.** Successful trials per scenario (all checks passed).

| # | Scenario | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|---|
| 1 | `tags-plan` | 3/3 | 3/3 | 3/3 | 0/3 |
| 2 | `csv-store` | 3/3 | 3/3 | 3/3 | 0/3 |
| 3 | `plan-needs-fix` | 3/3 | 3/3 | 3/3 | 1/3 |
|  | **Total** | **9/9** | **9/9** | **9/9** | **1/9** |

### 3.2 Failure analysis

**Table 3.** Failed checks, by model and condition (number of trials).

| Check | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Five new commits, one per task | 0 | 0 | 0 | 3 |
| Tasks 2 to 5 are not ticked | 0 | 0 | 0 | 3 |
| The stored CSV format is unchanged | 0 | 0 | 0 | 3 |
| src/cli.ts is unchanged | 0 | 0 | 0 | 3 |
| Response asks how tags should be stored in the CSV file | 0 | 0 | 0 | 2 |
| The plan no longer declares a parameter property for InvalidTagError | 0 | 0 | 0 | 2 |

### 3.3 Cost

**Table 4.** Resource use per trial, mean (standard deviation).

| Measure | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Cost (USD) | 0.440 (0.177) | 0.326 (0.098) | 0.175 (0.059) | 0.130 (0.013) |
| Output tokens | 8550 (4227) | 6484 (2547) | 6008 (2606) | 5271 (521) |
| Agent turns | 23.8 (12.2) | 13.8 (4.5) | 13.6 (3.2) | 8.1 (2.0) |
| Duration (s) | 84.7 (39.8) | 62.6 (23.3) | 44.5 (16.5) | 34.9 (4.6) |

## 4 Discussion

With the larger model, the skill made no measurable difference: the
baseline built every task as its own green commit, stopped at the CSV
format and asked how tags should be stored, and recorded the parameter
property deviation in the plan. Part of this is attributable to the
author's global instructions, which both conditions loaded and which
already ask for one commit per unit of work; the comparison measures the
skill's contribution in that environment, not against an uninstructed
model.

With the smaller model, the failures the skill is written against appeared
in the baseline. In `csv-store` it added a tags column to the public CSV
format and built all five tasks in every trial, rather than returning the
format decision to the plan's owner. In `tags-plan` it combined the five
tasks into one to four commits. In `plan-needs-fix` it implemented the
deviation correctly but left the plan's signature unchanged in two of three
trials, so the plan no longer described the code. None of these occurred
with the skill. The cost of the skill was higher reading and verification
effort, visible as more turns and a higher cost per trial on both models.

## 5 Limitations

- **Sample size.** Three trials per scenario, condition and model cannot
  establish low failure rates; the intervals remain wide.
- **Dependence between trials.** Trials within a scenario share a prompt
  and a repository. Fisher's exact test overstates the evidence; the sign
  test over three scenarios cannot reach conventional significance.
- **Scenario design.** The scenarios were written by the skill's author,
  partly after a first run had shown that the initial two did not separate
  the conditions with the larger model. There is no held-out set.
- **One small codebase.** All scenarios use one small tool and one plan.
  Larger plans, longer builds and other languages are untested.
- **Shared instructions.** The author's global instruction file was loaded
  in both conditions and overlaps with the skill.
- **Heuristic checks.** The checks on the agent's reply match keywords and
  can misjudge phrasing; signatures are matched by regular expression.
  Cost figures are estimates reported by the harness.

## 6 Reproducibility

Scenario definitions are in [`evals.json`](../../evals.json), the fixture
in [`fixture/`](../../fixture/) and
[`setup_fixture.sh`](../../setup_fixture.sh), and the grader in
[`grade.py`](../../grade.py). Each directory
`<model>/eval-*/<condition>/run-*/` contains the graded checks with
evidence (`grading.json`), resource use (`timing.json`), the agent's final
reply (`response.md`) and the resulting commits and plan state
(`build_result.txt`). Aggregates are in `summary.json`. The runs can be
repeated with:

```sh
MODEL=claude-opus-5-5 EFFORT=medium evals/implement-plan/run_iteration.sh <run-dir> <fixture-dir> 3 4
evals/implement-plan/grade.py <run-dir>
evals/shared/export_results.py export evals/implement-plan evals/implement-plan/results/claude-code --version 0.1 --effort medium --run claude-opus-5-5=<opus-run-dir> --run claude-sonnet-5-5=<sonnet-run-dir>
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator

[2] Wilson, E. B. (1927). Probable inference, the law of succession, and
statistical inference. *Journal of the American Statistical Association*,
22(158), 209-212.

[3] Fisher, R. A. (1922). On the interpretation of chi-squared from
contingency tables, and the calculation of P. *Journal of the Royal
Statistical Society*, 85(1), 87-94.
