<!--
Template for results/<harness>/README.md, rendered by
evals/shared/export_results.py. {{placeholders}} are filled from the
exported results. The prose in the Summary, Discussion and Limitations
interprets one specific run: review it by hand after every new export.
-->
# Evaluation of the `implement-plan` skill v{{version}} in Claude Code

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}` at {{effort}} effort, {{n_scenarios}} scenarios, {{trials}} trials per scenario, condition and model, {{date_long}}.

## Summary

The `implement-plan` skill instructs a coding agent to build an approved
implementation plan task by task: tests first, one commit per task, the
plan's names and signatures, an end-to-end check, and a rule for changes
the code forces on the design - cheap ones are made and written back into
the plan, expensive ones stop the build. It was evaluated against a
baseline without the skill on three plans for a small TypeScript command
line tool, with two models. With `{{opus_model}}`, both conditions passed
every check in every trial ({{opus_skill_pass}} of {{opus_n_trials}} versus
{{opus_base_pass}} of {{opus_n_trials}}). With `{{sonnet_model}}`, the skill
condition passed every check in {{sonnet_skill_pass}} of
{{sonnet_n_trials}} trials and the baseline in {{sonnet_base_pass}} of
{{sonnet_n_trials}}: without the skill, the smaller model changed a public
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
version {{version}}) has four phases. The agent reads the whole plan and
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

{{table_scenarios}}

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and local
settings, without plugins or MCP servers. In the **skill** condition, the
skill was copied into the fixture's project skills; in the **baseline**
condition it was absent. The prompt was identical in both. The author's
global instruction file remained loaded in both conditions, which includes
a rule to commit each completed unit of work; the baseline is therefore
somewhat informed about the commit discipline the skill prescribes.

### 2.4 Procedure

All trials ran in {{harness}} (`claude -p`) at {{effort}} effort with the
models `{{opus_model}}` and `{{sonnet_model}}` on {{date_long}} or the days
before it. Each trial started from a freshly generated repository. Agents
could use shell commands and file tools with edits accepted automatically;
`git push` was denied. In the skill condition, the skill was invoked in
{{opus_skill_invoked}} trials with `{{opus_model}}` and in
{{sonnet_skill_invoked}} with `{{sonnet_model}}`, verified from the session
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

With `{{opus_model}}`, {{opus_skill_pass}} of {{opus_n_trials}} skill
trials ({{opus_skill_rate}}; 95% CI {{opus_skill_ci}}) and
{{opus_base_pass}} of {{opus_n_trials}} baseline trials ({{opus_base_rate}};
95% CI {{opus_base_ci}}) succeeded; Fisher's exact test yields
p = {{opus_vs_base_fisher_p}}.

With `{{sonnet_model}}`, {{sonnet_skill_pass}} of {{sonnet_n_trials}} skill
trials ({{sonnet_skill_rate}}; 95% CI {{sonnet_skill_ci}}) and
{{sonnet_base_pass}} of {{sonnet_n_trials}} baseline trials
({{sonnet_base_rate}}; 95% CI {{sonnet_base_ci}}) succeeded; Fisher's exact
test yields p = {{sonnet_vs_base_fisher_p}}. The skill condition did better
in {{sonnet_vs_base_wins}} scenarios, worse in {{sonnet_vs_base_losses}}
and equally in {{sonnet_vs_base_ties}} (sign test p = {{sonnet_vs_base_sign_p}}).

**Table 2.** Successful trials per scenario (all checks passed).

{{table_results}}

### 3.2 Failure analysis

**Table 3.** Failed checks, by model and condition (number of trials).

{{table_failures}}

### 3.3 Cost

**Table 4.** Resource use per trial, mean (standard deviation).

{{table_cost}}

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
MODEL={{opus_model}} EFFORT={{effort}} evals/implement-plan/run_iteration.sh <run-dir> <fixture-dir> 3 4
evals/implement-plan/grade.py <run-dir>
evals/shared/export_results.py export evals/implement-plan {{out_dir}} --version {{version}} --effort {{effort}} --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator

[2] Wilson, E. B. (1927). Probable inference, the law of succession, and
statistical inference. *Journal of the American Statistical Association*,
22(158), 209-212.

[3] Fisher, R. A. (1922). On the interpretation of chi-squared from
contingency tables, and the calculation of P. *Journal of the Royal
Statistical Society*, 85(1), 87-94.
