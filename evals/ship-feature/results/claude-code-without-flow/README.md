# Evaluation of the `ship-feature` skill v0.3 in Claude Code, without `flow`

Claude Code 2.1.299, `claude-opus-5-5` and `claude-sonnet-5-5` at medium effort, 2 scenarios, 2 trials per scenario, condition and model, 14 October 2026.

## Summary

Since version 0.3, `ship-feature` and its four step skills report their
progress to the `flow` command if it is available, and are meant to work
the same without it. This run repeats the suite of the
[main report](../claude-code/README.md) with no `flow` command and no flow
id, graded on the checks of version 0.2 alone. With `claude-opus-5-5`,
4 of 4 skill trials and
2 of 4 baseline trials passed every
check; with `claude-sonnet-5-5`, 4 and
1. Version 0.2 scored 4 and 2 of 4 on both models. The
agents looked for `flow`, found none and went on; no reply mentioned it.

## 1 Method

Scenarios, conditions, procedure and checks are those of the main report,
except that each trial ran with `FLOW=absent`: the fixture's `flow` stub
was removed, every path entry holding a `flow` command was dropped and no
flow id was set, so the skills' reporting lines found no `flow` to report
to. The four checks on reports are not graded. In the skill condition,
the skill was invoked in 4 of 4 trials with
`claude-opus-5-5` and in 4 of 4 with `claude-sonnet-5-5`.

**Table 1.** Scenarios.

| # | Scenario | Prompt | Behavior tested |
|---|---|---|---|
| 1 | `mid-build` | "Continue shipping the bookmark tags feature." | A flow interrupted after the first task; continuing the build and going on to an isolated review instead of stopping after the build. |
| 2 | `after-build` | "Continue shipping the bookmark tags feature." | A flow interrupted after the build; reviewing without rebuilding, and stopping before the push. |

## 2 Results

**Table 2.** Successful trials per scenario (all checks passed).

| # | Scenario | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|---|
| 1 | `mid-build` | 2/2 | 0/2 | 2/2 | 0/2 |
| 2 | `after-build` | 2/2 | 2/2 | 2/2 | 1/2 |
|  | **Total** | **4/4** | **2/4** | **4/4** | **1/4** |

**Table 3.** Failed checks, by model and condition (number of trials).

| Check | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| The plan has a ## Review section | 0 | 2 | 0 | 3 |
| The build ran in a fresh agent | 0 | 2 | 0 | 2 |
| The review agent's prompt holds no build report | 0 | 2 | 0 | 2 |
| The review ran in a separate fresh agent | 0 | 2 | 0 | 2 |
| Response drafts the MR or asks to push | 0 | 0 | 0 | 1 |
| The review ran isolated: a fresh agent, or a session that wrote none of the code | 0 | 0 | 0 | 1 |

**Table 4.** Resource use per trial including subagents, mean (standard
deviation).

| Measure | Opus Skill | Opus Baseline | Sonnet Skill | Sonnet Baseline |
|---|---|---|---|---|
| Cost (USD) | 0.772 (0.194) | 0.625 (0.074) | 0.308 (0.105) | 0.179 (0.014) |
| Output tokens | 14905 (4170) | 10730 (1358) | 10248 (3793) | 6481 (1399) |
| Agent turns | 29.8 (6.1) | 21.2 (5.0) | 24.8 (9.3) | 13.2 (1.5) |
| Duration (s) | 222.9 (31.4) | 184.8 (21.5) | 109.3 (36.6) | 77.3 (6.7) |

## 3 Discussion

Without `flow`, the skill passed every check in every trial on both
models, as version 0.2 did, at about the cost of the run with the stub.
The baseline again finished the build and stopped unreviewed in every
`mid-build` trial. With `claude-sonnet-5-5`, one `after-build` baseline
trial did not review the branch, so the baseline passed one trial fewer
than in version 0.2; with two trials per cell, this is within the
run-to-run variation the earlier results showed. That trial used no step
skill, so it never read a reporting line.

The transcripts show how the agents handled the missing command. In 12
of 16 trials, the main session or an agent it started checked for
`flow` (`which flow` or `command -v flow && flow report ...`), almost
always appended to a command it ran anyway, so the check added no turns.
No trial treated the missing command as an error, retried it or told
the user about it.

## 4 Reproducibility

```sh
FLOW=absent MODEL=claude-opus-5-5 EFFORT=medium evals/ship-feature/run_iteration.sh <run-dir> <fixture-dir> 2 8
evals/ship-feature/grade.py <run-dir>
evals/shared/export_results.py export evals/ship-feature evals/ship-feature/results/claude-code-without-flow --version 0.3 --effort medium --template report-without-flow.md --run claude-opus-5-5=<opus-run-dir> --run claude-sonnet-5-5=<sonnet-run-dir>
```
