<!--
Template for results/claude-code-without-flow/README.md, rendered by
evals/shared/export_results.py from trials run with FLOW=absent; the main
report is report.md. {{placeholders}} are filled from the exported
results. The prose interprets one specific run: review it by hand after
every new export.
-->
# Evaluation of the `ship-feature` skill v{{version}} in Claude Code, without `flow`

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}` at {{effort}} effort, {{n_scenarios}} scenarios, {{trials}} trials per scenario, condition and model, {{date_long}}.

## Summary

Since version 0.3, `ship-feature` and its four step skills report their
progress to the `flow` command if it is available, and are meant to work
the same without it; since version 0.4, the flow builds in the
conversation instead of a fresh agent. This run repeats the suite of the
[main report](../claude-code/README.md) with no `flow` command and no flow
id, graded without the checks on reports. With `{{opus_model}}`,
{{opus_skill_pass}} of {{opus_n_trials}} skill trials and
{{opus_base_pass}} of {{opus_n_trials}} baseline trials passed every
check; with `{{sonnet_model}}`, {{sonnet_skill_pass}} and
{{sonnet_base_pass}}. Version 0.3 scored 4 and 2 of 4 with
`{{opus_model}}` and 4 and 1 with `{{sonnet_model}}`, version 0.2 4 and 2
on both. The agents looked for `flow`, found none and went on; no reply
mentioned it.

## 1 Method

Scenarios, conditions, procedure and checks are those of the main report,
except that each trial ran with `FLOW=absent`: the fixture's `flow` stub
was removed, every path entry holding a `flow` command was dropped and no
flow id was set, so the skills' reporting lines found no `flow` to report
to. The four checks on reports are not graded. In the skill condition,
the skill was invoked in {{opus_skill_invoked}} trials with
`{{opus_model}}` and in {{sonnet_skill_invoked}} with `{{sonnet_model}}`.

**Table 1.** Scenarios.

{{table_scenarios}}

## 2 Results

**Table 2.** Successful trials per scenario (all checks passed).

{{table_results}}

**Table 3.** Failed checks, by model and condition (number of trials).

{{table_failures}}

**Table 4.** Resource use per trial including subagents, mean (standard
deviation).

{{table_cost}}

## 3 Discussion

Without `flow`, the skill passed every check in every trial on both
models, as versions 0.2 and 0.3 did: it built in the conversation where
tasks were open, with no build agent, reviewed in a fresh agent and
stopped before the push, at about the cost of the run with the stub. The
baseline again finished the build and stopped unreviewed in every
`mid-build` trial. With `{{sonnet_model}}`, neither `after-build` baseline
trial reviewed the branch: both found the planted defects by running the
command line tool, fixed them and stopped without a `## Review`, so the
baseline passed one trial fewer than with version 0.3 and two fewer than
with version 0.2. With two trials per cell, this is within the
run-to-run variation the earlier results showed. Neither trial used a
step skill, so neither read a reporting line.

The transcripts show how the agents handled the missing command. In 14
of 16 trials, the main session or an agent it started checked for
`flow` (`which flow` or `command -v flow && flow report ...`), almost
always appended to a command it ran anyway, so the check added no turns.
No trial treated the missing command as an error, retried it or told
the user about it.

## 4 Reproducibility

```sh
FLOW=absent MODEL={{opus_model}} EFFORT={{effort}} evals/ship-feature/run_iteration.sh <run-dir> <fixture-dir> 2 8
evals/ship-feature/grade.py <run-dir>
evals/shared/export_results.py export evals/ship-feature {{out_dir}} --version {{version}} --effort {{effort}} --template report-without-flow.md --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```
