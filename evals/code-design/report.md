<!--
Template for results/<harness>/README.md, rendered by export_results.py.
{{placeholders}} are filled from the exported results. The prose in the
Summary, Discussion and Limitations interprets one specific run: review it
by hand after every new export.
-->
# Evaluation of the `code-design` skill v{{version}} in Claude Code

{{harness}}, `{{model}}`, {{n_scenarios}} scenarios, {{runs}} runs per scenario and method, {{date_long}}.

## Summary

`code-design` is a planning skill: before any code is written, it
investigates the codebase, lets the user choose between structurally
different approaches, and then lays out the chosen design as units, typed
signatures, data and call chains, without function bodies. It is evaluated
against three other ways of planning the same change in Claude Code: the
`superpowers` brainstorming workflow, the `feature-dev` workflow and the
model without a planning skill. All four are told to deliver the plan as a
lavish HTML page and a Markdown file, run in the same public-only
environment and answer to the same simulated user. Across
{{n_blocks}} blind comparisons ({{n_scenarios}} scenarios x {{runs}} runs),
`code-design` received the highest mean judge score ({{target_judge}} of 40)
and the highest scores for clarity and reviewability, while `feature-dev`
achieved the better mean rank ({{feature_dev_rank}} against
{{target_rank}}) and the higher completeness. The difference between these
two, and between them and `superpowers`, is not resolved at this sample
size; all three planning methods were ranked above planning without a
skill. `code-design` plans cost about {{cost_ratio_feature_dev}} times as
much as `feature-dev` plans and {{cost_ratio_plain}} times as much as
planning without a skill.

## 1 Question

A planning skill is only worth its cost if the plan it produces is easier
to discuss and correct than the plan the model would write anyway. Two
confounds make this hard to measure. Planning methods differ in output
medium and format, and a judge tends to reward the format it is shown, not
the design behind it. And methods that ask the user questions depend on the
answers they get, so an evaluation without a user cannot tell asking from
guessing.

The evaluation therefore holds the output medium, the environment and the
user constant, grades with format-neutral criteria, and asks one question:
how well can the repository owner discuss and correct the code design from
the plan, before any code exists?

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1]
(configurations run side by side, scenario-specific assertions, aggregated
benchmark) and extends it with multi-turn runs against a simulated user and
blind ranking by a judge model.

### 2.1 Methods compared

- **`code-design`** ([`SKILL.md`](../../../../skills/code-design/SKILL.md), version {{version}}), invoked as `/code-design <task>`.
- **`superpowers`** (plugin `superpowers@claude-plugins-official`), invoked as `/superpowers:brainstorming <task>`, which continues into its own plan-writing skill.
- **`feature-dev`** (plugin `feature-dev@claude-plugins-official`), invoked as `/feature-dev:feature-dev <task>`.
- **`plain`**: the task without a planning skill.

Each method is invoked explicitly, so the evaluation measures the method,
not whether its description triggers.

### 2.2 Scenarios

Each scenario pairs a request, phrased as a user would type it, with a real
repository pinned to one commit, and with hidden user preferences that the
simulated user reveals only when asked (Table 1).

**Table 1.** Scenarios.

| # | Scenario | Repository | Request | Hidden preferences | Key fact |
|---|---|---|---|---|---|
| 1 | `takumi-weekly-goals` | private Laravel and React app | Weekly practice goals per topic, with dashboard progress and a notification when the goal is reached. | In-app toast, no email or queue; Monday-Sunday in UTC; goal set on the topic page only; the toast may fire again after a correction. | Mirrors the existing before/after promotion detection. |
| 2 | `clickup-status-command` | [`iamcommee/clickup-cli`](https://github.com/iamcommee/clickup-cli) (Go) | A `tasks status <id> <status>` command that validates against the list's statuses. | Case-insensitive exact match; no-op with exit 0 if unchanged; board order; no confirmation prompt. | The repository does not build at the pinned commit. |
| 3 | `mdterm-bookmarks` | [`bahdotsh/mdterm`](https://github.com/bahdotsh/mdterm) (Rust) | Vim-style marks: `m` + letter sets, `'` + letter jumps, persisted per file. | Mouse capture moves to `M`; a-z only, per file; platform state directory; marks survive resizes and small edits. | `m` is already bound to mouse capture. |

### 2.3 Environment

All runs use Claude Code in headless mode (`claude -p`, resumed with
`--resume` for every turn) with `{{model}}`. To make runs reproducible
with public components only, no user settings, user hooks, user
instructions (`CLAUDE.md`) or MCP servers are loaded. Each run starts from
a fresh clone of the pinned commit, into which the lavish skill [2] is
installed for every method and `code-design` only for its own runs; only
the method's own plugin is enabled. Every method receives the same
appended instruction: deliver the final plan as a lavish HTML page and a
Markdown file, ask when a decision is needed, and do not implement.

### 2.4 Simulated user

A second model (`claude-sonnet-5-5`, no tools) plays the repository owner.
After every turn of the method it reads the method's last message and the
text of any plan page written or changed in that turn, and replies. It
answers only what is asked, uses its hidden preferences where a question
touches them and otherwise accepts the method's recommendation, reviews a
finished plan once, never asks for code, and replies `APPROVED` when the
plan is done. A run ends one turn after approval or after 14 turns.

### 2.5 Measures

**Blind ranking (primary).** For each scenario and run, a judge
(`claude-sonnet-5-5`) receives the four final plans under shuffled labels,
without the conversations, and the pinned repository. It scores each plan
from 1 to 10 on correctness, completeness, clarity and reviewability, and
ranks the four. It is told not to reward length, styling or format, and to
check at least three claims per plan against the repository.

**Assertions (secondary).** A grader (`claude-sonnet-5-5`) checks each run
against nine format-neutral assertions: grounded claims, repository
conventions, a structurally different alternative, agreement with the
user's answers and hidden preferences, elicitation (no hidden preference
decided silently), end-to-end coverage including failures, consistent
names and signatures, fit with existing interfaces, and the scenario's key
fact. Cited `file:line` references are additionally checked by script.

**Cost.** Cost in USD as reported by the harness, tokens excluding cache
reads, output tokens, executor turns and wall-clock duration, for the
method only; the simulated user's cost is excluded.

Methods are compared with a Friedman test over the {{n_blocks}} ranked
comparisons [3], and `code-design` with each other method by a two-sided
sign test on pairwise ranks.

## 3 Results

### 3.1 Overall

**Table 2.** Judge score (mean, standard deviation), rank and assertions per method.

{{table_overall}}

The Friedman test over all comparisons yields chi-squared = {{friedman_chi2}}
(df = 3, p = {{friedman_p}}).

**Table 3.** Pairwise ranks of `code-design` against each other method.

{{table_pairwise}}

### 3.2 By scenario

**Table 4.** Mean judge score (of 40) / mean rank per scenario.

{{table_scenarios}}

### 3.3 By criterion

**Table 5.** Mean judge score per criterion (of 10).

{{table_criteria}}

### 3.4 Failed assertions

**Table 6.** Number of runs in which an assertion failed (of {{runs_per_method}} per method).

{{table_failures}}

### 3.5 Cost

**Table 7.** Resource use per run, mean.

{{table_cost}}

## 4 Discussion

The methods differ overall, but most of that difference separates the
three planning methods from planning without a skill: `plain` was ranked
last or second to last in every comparison, missed the broken build in
`clickup-status-command` in all of its runs and rarely weighed a
structurally different design.

Among the planning methods, the profiles differ more than the totals.
`code-design` scored highest on clarity and reviewability, the two criteria
it is built for. Judges repeatedly cited the per-unit signatures, the
numbered call chains with failure branches and the list of assumptions as
what made individual decisions easy to challenge. It never failed the
alternatives or key-fact assertions, which is consistent with its explicit
investigation and approaches phases.

Its weakness is concentrated in one scenario. In two of three
`mdterm-bookmarks` runs it anchored marks to bare source line numbers, so
marks drift after edits made between sessions, without asking how robust
marks had to be; the third run anchored to line and text and passed. The
assumptions list made the choice visible but did not turn it into a
question. This accounts for most of its lower correctness and completeness
and for its last place in one comparison. The skill would benefit from
asking about the durability requirements of persisted state, not only
listing them.

`feature-dev` was the most consistent method: it was ranked first most
often and scored highest on completeness, but its plans described call
flow less precisely. `superpowers` produced the most thorough edge-case
coverage in `mdterm-bookmarks`, but its plans often contained full
implementation code, which lowered clarity, and it missed the broken build
in every `clickup-status-command` run.

`code-design` is the most expensive method. It produces about twice the
output tokens of `feature-dev` and `plain` and about 1.5 times those of
`superpowers`, mainly because it writes two review pages (an approaches
page and an implementation page) and a more detailed design.

## 5 Limitations

- **Sample size.** Three runs per scenario and method give nine ranked
  comparisons. The pairwise sign tests cannot resolve differences between
  the planning methods; only the separation from `plain` is clear.
- **Model as judge.** Each comparison was scored by a single judge model,
  of the same family as the methods under test, with no second judge or
  human rating. Blinding is partial: `code-design` is recognizable by its
  two-page structure.
- **Simulated user.** One persona answers every method. Its hidden
  preferences were written together with the scenarios, it approves
  readily after one review, and it answers in text rather than through the
  lavish review page, so the browser review loop is not exercised.
- **Scenario design.** The three scenarios were written in the same process
  in which the skill was revised, without a held-out set, and one scenario
  uses a private repository that cannot be rerun independently.
- **Grading adjustments.** Two grading rules were made explicit after
  grading to keep runs consistent: a plan that openly deviates from a
  preference does not honour it, and for `mdterm-bookmarks` any per-user
  state or data directory satisfies the storage preference while marks
  must relocate after edits between sessions. The affected assertion was
  re-graded for all runs of a scenario under the same rule.
- **Invocation and environment.** Every method was invoked explicitly, so
  triggering is not measured, and runs used no user settings, hooks or
  instructions. Methods that rely on a user's environment may behave
  differently in practice.
- **Cost figures** are estimates reported by the harness; on a
  subscription they count against usage limits rather than being billed.

## 6 Reproducibility

Scenario definitions are in [`evals.json`](../../evals.json), the methods
in [`configs.json`](../../configs.json), the simulated user in
[`sim_user.md`](../../sim_user.md), the grader in
[`grader.md`](../../grader.md) and the judge in
[`judge.md`](../../judge.md). The pinned `clickup-cli` commit exists only
as a local merge; [`fixtures/clickup-cli.bundle`](../../fixtures/clickup-cli.bundle)
recreates it on top of a public clone. Each directory
`eval-*/<method>/run-*/` contains the graded assertions with evidence
(`grading.json`), resource use (`timing.json`), run metadata
(`meta.json`) and, for public scenarios, the final plan files (`plans/`)
and the conversation with the simulated user (`transcript.md`). Unblinded
judge verdicts are in `eval-*/verdicts/`, aggregates in `summary.json`.
The private scenario is published with scores only. The run can be
repeated with:

```sh
evals/code-design/run_iteration.sh <run-dir> {{runs}} 4
# grade every run with grader.md, then for each run index:
evals/code-design/blind.py <run-dir> <run> <seed>
evals/code-design/export_results.py export <run-dir> evals/code-design/results/claude-code --version {{version}} --model {{model}}
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator

[2] Chen, K. lavish-axi. https://www.npmjs.com/package/lavish-axi

[3] Friedman, M. (1937). The use of ranks to avoid the assumption of
normality implicit in the analysis of variance. *Journal of the American
Statistical Association*, 32(200), 675-701.
