<!--
Template for results/<harness>/README.md, rendered by
evals/shared/export_results.py. {{placeholders}} are filled from the
exported results. The prose in the Summary, Discussion and Limitations
interprets one specific run: review it by hand after every new export.
-->
# Evaluation of the `diagnose-bug` skill v{{version}} in Claude Code

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}` at {{effort}} effort, {{n_scenarios}} scenarios, three conditions, {{trials}} trials per scenario, condition and model, {{date_long}}.

## Summary

The `diagnose-bug` skill instructs a coding agent to reproduce a reported
bug end to end the way a user meets it, to prove its root cause by
experiment, and to hand over a fix plan whose first task is a regression
test, without changing code. It was compared with superpowers'
`systematic-debugging` skill and with no skill on three bug reports
against a small command line tool: a bug whose reporter blames the wrong
command, a bug that only shows with data written by an earlier version,
and a report that does not reproduce. With `{{opus_model}}`, all three
conditions found the cause in almost every trial
({{opus_skill_diagnosis_pass}}, {{opus_sd_diagnosis_pass}} and
{{opus_base_diagnosis_pass}} of {{opus_n_trials}} trials passed every
diagnosis check). With `{{sonnet_model}}` the conditions separated: the
skill passed {{sonnet_skill_diagnosis_pass}}, `systematic-debugging`
{{sonnet_sd_diagnosis_pass}} and the uninstructed agent
{{sonnet_base_diagnosis_pass}} of {{sonnet_n_trials}}, almost entirely
because the latter two reproduced the bug in a unit test instead of
through the tool itself. Only the skill kept to its contract of
diagnosing without fixing; the other conditions repaired the code
directly. The skill was the most expensive condition.

## 1 Question

A fix is only as good as the diagnosis behind it. An agent that accepts
the reporter's account, or reproduces the bug in a test written from its
first guess, can repair the place where the symptom shows and leave the
cause, or the data it already damaged, in place. The evaluation asks
whether the skill makes an agent reproduce a bug the way the user met it,
find the cause where the state first goes wrong rather than where it
becomes visible, and stop when a report does not reproduce, compared with
an established debugging skill and with no instruction. It further asks
whether the skill keeps its contract: no code change, and a fix plan in
the agreed format for the build step that follows it.

## 2 Method

The evaluation follows the workflow of Anthropic's skill-creator skill [1],
extended with repeated headless trials against generated repositories, as
in the other evaluations in this repository.

### 2.1 Skill under test

The skill ([`SKILL.md`](../../../../skills/diagnose-bug/SKILL.md),
version {{version}}) has six steps: read the report and separate what the
user observed from their guess at the cause, reproduce it end to end with
the real interface and input, trace the wrong state back to where it
first goes wrong and prove each hypothesis by experiment, decide where
the fix belongs and what else is affected (including data already
damaged), write a fix plan in the format of its reference file, and hand
over with the working tree as found except for the plan. A report that
does not reproduce ends without a plan.

### 2.2 Scenarios

All scenarios use `bm`, a command line bookmark manager in TypeScript
whose test suite passes (Table 1); the prompt names a ticket that a stub
of the team's ticket tool returns. In `tags-lost`, `BookmarkStore.save()`
writes through a `toRecord()` that predates tags, so every `bm add`
deletes all tags, while `tag()` writes them itself; the reporter blames
`list --tag`. In `tags-spread`, every record loaded without a `tags`
field receives one shared empty array and `tag()` pushes into it, so
tagging one bookmark of a file written before tags existed tags all of
them; a file created by the current version does not show the bug, and
the obvious repair sits in `tag()`, where the symptom appears. In
`not-reproducible`, the report that titles with quotes corrupt the file
is false.

**Table 1.** Scenarios.

{{table_scenarios}}

### 2.3 Conditions

Every trial ran in a fresh headless session restricted to project and
local settings, without plugins or MCP servers, with the same prompt. In
the **skill** condition, the skill was copied into the fixture's project
skills. In the **`systematic-debugging`** condition, superpowers'
`systematic-debugging` skill (version 7.0.0) [2] was copied there
instead; it covers root-cause investigation and goes on to the fix by
design. The **baseline** had no skill. The fixture's agent instructions,
identical in all conditions, name the ticket tool and the variable that
points the tool at another bookmarks file.

### 2.4 Procedure

All trials ran in {{harness}} (`claude -p`) at {{effort}} effort with the
models `{{opus_model}}` and `{{sonnet_model}}`. Agents could use shell
commands, file tools and subagents, with edits accepted automatically and
`git push` denied; the bookmarks file variable pointed into the fixture.
The skill was invoked in {{opus_skill_invoked}} trials with
`{{opus_model}}` and {{sonnet_skill_invoked}} with `{{sonnet_model}}`;
`systematic-debugging` in {{opus_sd_other_skill}} and
{{sonnet_sd_other_skill}}, verified from the session transcripts. The
`tags-spread` scenario was added after a smoke run in which the other two
scenarios showed no difference between conditions.

### 2.5 Measures and analysis

`grade.py` grades each trial from its repository, its final reply and
the shell commands in its transcripts. Its checks fall into two parts.
**Diagnosis** checks apply to every condition: the bug was reproduced
through the tool's command line (for `tags-spread`, with a file from
before tags), the cause named is the one planted, any source change is at
the cause and removes the bug when the tool is run, a regression test was
written that fails on the original code or was named, and the damage
already done to users' files was named; for `not-reproducible`, the
report was tried through the command line with quotes in a title, no
source changed, and the reply says it did not reproduce and asks for
details. **Contract** checks are what the skill promises and apply to it
alone: source and tests unchanged and nothing committed, a fix plan with
the required sections, and its first task the regression test and its
last the end-to-end check; for `not-reproducible`, no plan. Text checks
are keyword heuristics; every failed diagnosis check was verified by hand
against the trial's reply and transcript, and the heuristics were
widened where they had missed a correct wording. A trial succeeds in a
part when it passes all of that part's checks; the conditions are
compared with a two-sided Fisher exact test over trials.

## 3 Results

### 3.1 Diagnosis

**Table 2.** Trials passing every diagnosis check, per scenario.

{{table_results_diagnosis}}

With `{{sonnet_model}}`, the difference between the skill and the
baseline is significant (Fisher p = {{sonnet_vs_base_diagnosis_fisher_p}});
against `systematic-debugging` it is not (p =
{{sonnet_vs_sd_diagnosis_fisher_p}}). With `{{opus_model}}`, neither
difference is (p = {{opus_vs_base_diagnosis_fisher_p}} and
{{opus_vs_sd_diagnosis_fisher_p}}).

**Table 3.** Failed checks, by model and condition (number of trials).
Contract checks fail by design outside the skill condition.

{{table_failures}}

### 3.2 Contract

**Table 4.** Trials passing every contract check, per scenario.

{{table_results_contract}}

### 3.3 Cost

**Table 5.** Resource use per trial, mean (standard deviation). Cost
includes subagents started by the session.

{{table_cost}}

## 4 Discussion

All conditions found the planted causes in nearly every trial, including
the bug the reporter attributed to the wrong command and the bug whose
obvious repair lies where the symptom shows; no condition repaired
`tag()` instead of the shared default. Finding the cause was therefore
not what separated them. What separated them was how the bug was
reproduced. With `{{sonnet_model}}`, the uninstructed agent reproduced
neither real bug through the tool: it read the code, wrote a unit test
from its reading and fixed it, and `systematic-debugging` did the same
in two of three trials of the bug that needs old data. A unit test written from the first
reading exercises the path the agent already suspects; it confirms a
hypothesis rather than the user's experience. Here the hypothesis was
right, so the fixes held, but the reproduction that would have caught a
wrong one was missing. The skill reproduced every bug through the tool,
rebuilding a file in the old format for `tags-spread`, in every trial on
both models. With `{{opus_model}}`, the other conditions reproduced through
the tool unprompted in all but one trial, and the skill added nothing
measurable to the diagnosis.

All conditions stopped on the report that does not reproduce and asked
for details, so the scenario shows no difference; it does show that the
skill's instruction to write no plan in that case was followed.

The contract is where the skill differs by construction: the two other
conditions fixed the code, as `systematic-debugging` is designed to and
as an uninstructed agent tends to, while the skill left the code alone
and wrote a fix plan whose first task is the regression test and whose
last reruns the reproduction. This is the property the delivery flow
relies on, since the plan is reviewed by the user before any code
changes and is then built by `implement-plan`. The extra cost of the
skill condition is mostly the plan.

## 5 Limitations

- **Easy causes.** Every condition found every planted cause on
  `{{opus_model}}`; the scenarios do not show whether the skill helps
  find a cause that is genuinely hard to find.
- **Keyword grading.** Text checks are heuristics; failed diagnosis
  checks were verified by hand, passed ones by sampling.
- **Sample size and dependence.** Three trials per scenario, condition
  and model; trials within a scenario share a repository.
- **Scenario design.** One small codebase, written alongside the skill,
  without a held-out set; one scenario was added after the smoke run.
- **Neutral environment.** User instructions and plugins were not
  loaded; an agent whose own instructions already ask for end-to-end
  reproduction would likely narrow the differences.

## 6 Reproducibility

Scenario definitions are in [`evals.json`](../../evals.json), the
fixture in [`fixture/`](../../fixture/),
[`tickets.json`](../../tickets.json) and
[`setup_fixture.sh`](../../setup_fixture.sh), and the grader in
[`grade.py`](../../grade.py). Each directory
`<model>/eval-*/<condition>/run-*/` contains the graded checks with
evidence (`grading.json`), resource use (`timing.json`), the final reply
(`response.md`) and the working tree state, command line calls and any
plan written (`diagnosis_result.txt`). The runs can be repeated with:

```sh
MODEL={{opus_model}} EFFORT={{effort}} evals/diagnose-bug/run_iteration.sh <run-dir> <fixture-dir> 3 5
evals/diagnose-bug/grade.py <run-dir>
evals/shared/export_results.py export evals/diagnose-bug {{out_dir}} --version {{version}} --effort {{effort}} --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```

The trigger accuracy of the skill's description was measured separately
with skill-creator's `run_eval.py` on the twenty queries in
[`trigger-queries.json`](../../trigger-queries.json).

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator

[2] Jesse Vincent. superpowers: systematic-debugging. https://github.com/obra/superpowers
