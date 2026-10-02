# Evaluation of the `code-design` skill v0.4 in Claude Code

Claude Code 2.1.286, `claude-opus-5-5` at medium effort, 3 scenarios, 3 runs per scenario and method, 1 October 2026.

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
9 blind comparisons (3 scenarios x 3 runs),
`code-design` received a mean judge score of 34.7 of 40 and
passed 77/81 assertions, against 34.0 and
76/81 for `feature-dev`; the paired score difference to
`feature-dev` (+0.7 points, p = 0.68) is
not distinguishable from zero. Its lead over `superpowers`
(+3.4, p = 0.082) is suggestive but not
established, and its lead over planning without a skill
(+7.8, p = 0.0039) is consistent across every
comparison. `code-design` scored highest on clarity and reviewability, and
cost 3.18 USD per run against 2.79 for
`feature-dev` and 1.46 without a skill. At equal judged quality,
`feature-dev` is therefore the more cost-effective of the two leading
methods.

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

- **`code-design`** ([`SKILL.md`](../../../../skills/code-design/SKILL.md), version 0.4), invoked as `/code-design <task>`.
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
`--resume` for every turn) with `claude-opus-5-5` at medium effort,
which subagents inherit. To make runs reproducible
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

Three measures are primary: the judge score, the assertions passed and the
cost.

**Judge score.** For each scenario and run, a judge (`claude-sonnet-5-5`)
receives the four final plans under shuffled labels, without the
conversations, and the pinned repository. It scores each plan from 1 to 10
on correctness, completeness, clarity and reviewability (at most 40 per
plan). It is told not to reward length, styling or format, and to check at
least three claims per plan against the repository. It also ranks the four
plans; the ranks are reported as a secondary measure.

**Assertions.** A grader (`claude-sonnet-5-5`) checks each run
against nine format-neutral assertions: grounded claims, repository
conventions, a structurally different alternative, agreement with the
user's answers and hidden preferences, elicitation (no hidden preference
decided silently), end-to-end coverage including failures, consistent
names and signatures, fit with existing interfaces, and the scenario's key
fact. Cited `file:line` references are additionally checked by script.

**Cost.** Cost in USD as reported by the harness, tokens excluding cache
reads, output tokens, cache reads, executor turns and wall-clock duration,
for the method only; the simulated user's cost is excluded. Tokens are
counted from the session logs, including subagents, because the headless
result's usage omits them; its cost already includes them. Subagents may
run on a cheaper model, so tokens and cost are not proportional across
methods.

`code-design` is compared with each other method by an exact two-sided
Wilcoxon signed-rank test [3] on the paired judge-score differences of the
9 comparisons. The ranks are compared with a Friedman test [4]
and pairwise sign tests.

## 3 Results

### 3.1 Overall

**Table 2.** Judge score and cost per run (mean, standard deviation), assertions passed, and judge score per USD.

| Method | Judge score (of 40) | Assertions passed | Cost per run (USD) | Judge score per USD |
|---|---|---|---|---|
| `code-design` | 34.7 (2.1) | 77/81 | 3.18 (1.04) | 10.9 |
| `feature-dev` | 34.0 (1.7) | 76/81 | 2.79 (1.61) | 12.2 |
| `superpowers` | 31.2 (3.5) | 73/81 | 2.26 (1.17) | 13.8 |
| `plain` | 26.9 (1.5) | 68/81 | 1.46 (0.57) | 18.4 |

**Table 3.** Paired judge-score differences of `code-design` against each other method, over 9 comparisons.

| Compared with | Mean score difference | `code-design` higher / lower / equal | Wilcoxon p |
|---|---|---|---|
| `feature-dev` | +0.7 | 4 / 4 / 1 | 0.68 |
| `superpowers` | +3.4 | 7 / 2 / 0 | 0.082 |
| `plain` | +7.8 | 9 / 0 / 0 | 0.0039 |

### 3.2 By scenario

**Table 4.** Mean judge score (of 40) / mean rank per scenario.

| Scenario | `code-design` | `feature-dev` | `superpowers` | `plain` |
|---|---|---|---|---|
| `takumi-weekly-goals` | 35.3 / 1.7 | 34.0 / 2.0 | 31.7 / 2.7 | 27.7 / 3.7 |
| `clickup-status-command` | 35.0 / 2.0 | 35.0 / 1.0 | 28.7 / 3.3 | 26.3 / 3.7 |
| `mdterm-bookmarks` | 33.7 / 2.7 | 33.0 / 2.0 | 33.3 / 1.7 | 26.7 / 3.7 |

### 3.3 By criterion

**Table 5.** Mean judge score per criterion (of 10).

| Criterion | `code-design` | `feature-dev` | `superpowers` | `plain` |
|---|---|---|---|---|
| Correctness | 8.44 | 8.56 | 7.78 | 6.67 |
| Completeness | 8.00 | 8.78 | 8.00 | 6.67 |
| Clarity | 9.00 | 8.11 | 7.78 | 7.22 |
| Reviewability | 9.22 | 8.56 | 7.67 | 6.33 |

### 3.4 Failed assertions

**Table 6.** Number of runs in which an assertion failed (of 9 per method).

| Assertion | `code-design` | `feature-dev` | `superpowers` | `plain` |
|---|---|---|---|---|
| alternatives | 0 | 2 | 3 | 5 |
| api-fit | 0 | 0 | 0 | 1 |
| elicitation | 2 | 1 | 1 | 3 |
| grounded | 0 | 1 | 1 | 0 |
| key-fact | 0 | 0 | 3 | 3 |
| preferences-honoured | 2 | 1 | 0 | 1 |

### 3.5 Cost

**Table 7.** Resource use per run, mean.

| Measure | `code-design` | `feature-dev` | `superpowers` | `plain` |
|---|---|---|---|---|
| Cost (USD) | 3.18 | 2.79 | 2.26 | 1.46 |
| Tokens excl. cache reads | 226,574 | 319,217 | 162,560 | 111,377 |
| of which in subagents | 0 | 171,084 | 7,812 | 0 |
| Output tokens | 72,669 | 75,569 | 48,723 | 27,553 |
| Cache reads | 2,454,278 | 2,140,877 | 1,986,340 | 1,183,740 |
| Executor turns | 3.8 | 3.6 | 7.0 | 2.7 |
| Duration (min) | 12.0 | 9.2 | 9.7 | 5.2 |

### 3.6 Ranks

The judge's forced ranking is reported as a secondary measure. It shows
which plan the judge preferred when made to choose, but discards how large
the differences were.

**Table 8.** Mean rank (1 = best) and first places.

| Method | Mean rank | First places |
|---|---|---|
| `code-design` | 2.11 | 3/9 |
| `feature-dev` | 1.67 | 4/9 |
| `superpowers` | 2.56 | 2/9 |
| `plain` | 3.67 | 0/9 |

The Friedman test over all comparisons yields chi-squared = 11.93
(df = 3, p = 0.0076).

**Table 9.** Pairwise ranks of `code-design` against each other method.

| Compared with | `code-design` ranked higher | ranked lower | Sign test p |
|---|---|---|---|
| `feature-dev` | 3 | 6 | 0.51 |
| `superpowers` | 6 | 3 | 0.51 |
| `plain` | 8 | 1 | 0.039 |

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

`feature-dev` matched `code-design` on judged quality at lower cost: it
was ranked first most often and scored highest on completeness, but its plans described call
flow less precisely. `superpowers` produced the most thorough edge-case
coverage in `mdterm-bookmarks`, but its plans often contained full
implementation code, which lowered clarity, and it missed the broken build
in every `clickup-status-command` run.

`code-design` is the most expensive method, although `feature-dev` uses
more tokens in total: in four of its nine runs `feature-dev` delegated
exploration and architecture to subagents on Claude Sonnet 5.5, a cheaper
model, while `code-design` does all of its work in the main Claude Opus 5.5
session. `code-design` also produces about 2.6 times the output tokens of
`plain` and about 1.5 times those of `superpowers`, mainly because it
writes two review pages (an approaches page and an implementation page)
and a more detailed design. Since its
judged quality matches `feature-dev`, its additional cost buys a format
that is easier to review rather than a better design; whether that is
worth it depends on how much of the plan the user intends to review and
correct before implementation.

## 5 Limitations

- **Sample size.** Three runs per scenario and method give nine paired
  comparisons. They cannot resolve differences of a few points between the
  planning methods; only the separation from `plain` is clear.
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
evals/code-design/run_iteration.sh <run-dir> 3 4
# grade every run with grader.md, then for each run index:
evals/code-design/blind.py <run-dir> <run> <seed>
evals/code-design/export_results.py export <run-dir> evals/code-design/results/claude-code --version 0.4 --model claude-opus-5-5 --effort medium
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator

[2] Chen, K. lavish-axi. https://www.npmjs.com/package/lavish-axi

[3] Wilcoxon, F. (1945). Individual comparisons by ranking methods.
*Biometrics Bulletin*, 1(6), 80-83.

[4] Friedman, M. (1937). The use of ranks to avoid the assumption of
normality implicit in the analysis of variance. *Journal of the American
Statistical Association*, 32(200), 675-701.
