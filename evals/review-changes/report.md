<!--
Template for results/<harness>/README.md, rendered by
evals/shared/export_results.py. {{placeholders}} are filled from the
exported results. The prose in the Summary, Discussion and Limitations
interprets one specific run: review it by hand after every new export.
-->
# Evaluation of the `review-changes` skill v{{version}} in Claude Code

{{harness}}, `{{opus_model}}` and `{{sonnet_model}}` at {{effort}} effort, {{n_scenarios}} scenarios, three conditions, {{trials}} trials per scenario, condition and model, {{date_long}}.

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
expensive condition. Version 0.8, which adds the harness's security
review, matched version 0.7 in detection on eight scenarios including five with
security defects, with the same detection and judged report quality at
64% more cost per trial (section 6).

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
Version 0.8 adds a security item to that order and runs the harness's
own security review alongside; it is compared with 0.7 in section 6.

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

All trials ran in {{harness}} (`claude -p`) at {{effort}} effort with the
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

## 6 Version comparison: v0.7 and v0.8

Version 0.8 added a parallel run of the harness's security review
(Claude Code's `/security-review`) and a security item to the review
checklist. It was compared with version 0.7 on the three scenarios above
and five new ones, all on the same command line tool with a local
`origin` whose `HEAD` is `main`, as after a clone (Table 6). Each
version ran three trials per scenario with `claude-opus-5-5` at medium
effort in Claude Code 2.1.332, on 2026-11-26; trials ran with `open`,
`xdg-open` and the tool's opener replaced by recording stubs. Results
are in [`v0.7-vs-v0.8/`](v0.7-vs-v0.8/), produced by
[`compare_versions.py`](../../compare_versions.py).

**Table 6.** Security scenarios.

| Scenario | Branch | Planted |
|---|---|---|
| security-diff | Import of shared bookmark files and `bm open` | Command injection: the URL reaches a shell inside double quotes; any URL scheme accepted; no test of a rejected scheme |
| stacked-base | `bm remove`, stacked on the unmerged security-diff branch and reviewed against it | Unknown id exits 0; no test for it. The injection lies only in the lower branch and must not be fixed |
| no-origin-head | security-diff with `origin/HEAD` unset, as after adding a remote by hand | As security-diff |
| clean-branch | The sharing feature implemented correctly | Nothing in `src/opener.ts` and `src/urls.ts`; a change there is a false positive |
| subtle-xss | An HTML export on top of the merged, correct sharing feature | The escaping covers `& < >` but not quotes, and the title is also written into an attribute: stored XSS from a shared title. Not planted but present: `href` is unescaped too, reachable through `bm add`, which takes any URL |

**Table 7.** Successful trials (all checks passed), and v0.8 trials in
which a subagent invoked `/security-review`.

| Scenario | v0.7 | v0.8 | v0.8 invoked `/security-review` |
|---|---|---|---|
| seeded-defects | 3/3 | 3/3 | 3/3 |
| vague-prompt | 3/3 | 3/3 | 3/3 |
| architecture | 3/3 | 3/3 | 3/3 |
| security-diff | 3/3 | 3/3 | 3/3 |
| stacked-base | 3/3 | 0/3 | 3/3 |
| no-origin-head | 3/3 | 3/3 | 0/3 |
| clean-branch | 3/3 | 3/3 | 3/3 |
| subtle-xss | 3/3 | 3/3 | 3/3 |

**Table 8.** Blind judgment of the owner report, total of 40, mean (sd),
and how often each version's report was ranked first of the two.

| Scenario | v0.7 | v0.8 |
|---|---|---|
| seeded-defects | 33.0 (2.6) | 34.7 (0.6) |
| vague-prompt | 35.0 (1.0) | 31.7 (2.3) |
| architecture | 34.0 (0.0) | 35.7 (0.6) |
| security-diff | 35.0 (0.0) | 32.3 (4.7) |
| stacked-base | 31.7 (2.9) | 34.7 (0.6) |
| no-origin-head | 34.7 (0.6) | 33.3 (1.2) |
| clean-branch | 33.7 (1.5) | 32.3 (3.2) |
| subtle-xss | 35.3 (1.2) | 34.3 (0.6) |
| All | 34.0 (1.8) | 33.6 (2.3) |
| Ranked first | 14 of 24 | 10 of 24 |

**Table 9.** Resource use per trial, mean (sd); cost and duration
include subagents.

| Measure | v0.7 | v0.8 |
|---|---|---|
| Cost (USD) | 0.48 (0.11) | 0.79 (0.23) |
| Duration (s), median | 103 | 111 |
| Duration (s), mean | 112 (24) | 167 (241) |
| Output tokens | 10533 (2439) | 15631 (6267) |
| Subagents | 1.0 (0.0) | 2.8 (1.1) |

Detection did not improve: version 0.7 found, proved and fixed the
command injection, the scheme check and the subtle attribute injection
in every trial, as version 0.8 did, and neither version changed the
correct security code of the clean branch. The planted defects are
visible to a careful general review; the scenarios cannot show defects
that only a security-focused pass finds.

The mechanism worked as specified. With `origin/HEAD` set, every v0.8
trial had a subagent invoke `/security-review`, and on the stacked
branch every one of them reviewed `git diff <target>...HEAD` in place of
the command's diff against `origin/HEAD` and found no vulnerability in
it, which is correct. Without `origin/HEAD` the command fails while
loading; in the final runs the reviewer skipped it and said so, and its
own pass still found both defects.

The only failed check is a deliberate one: in all three stacked trials,
the security agent noted the lower branch's command injection as outside
the diff it reviewed, and v0.8 reported it as an open item to fix on
that branch, without touching it; v0.7 never mentioned it. The judge
scored this in v0.8's favour (34.7 against 31.7), reasoning that an
owner about to merge the stack should know.

Report quality did not differ beyond noise: 34.0 against 33.6 of 40,
v0.8 first in 10 of 24 comparisons (two-sided sign test, p = 0.54). Cost
rose by 64% per trial, from 2.8 subagents on average in place of one:
the security agent and the command's own vulnerability and
false-positive agents. Median duration rose by 8%, because the security
review runs in parallel with the reviewer's own pass. The mean is
dominated by one trial in which the background agent's completion notice
reached the headless session 18 minutes after the review had ended and
caused an extra turn.

Two changes to the skill came out of earlier runs of this comparison.
First, a reviewer told only to "start" the security review briefed its
agent to review on its own, so the command never ran; the skill now says
to invoke it by name. Second, the instruction to pass the range when
`origin/HEAD` is unset could not work, since the command fails before
reading it; the skill now skips the command there.

## 7 Reproducibility

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
CONFIGS="with_skill without_skill code_review" MODEL={{opus_model}} EFFORT={{effort}} evals/review-changes/run_iteration.sh <run-dir> <fixture-dir> 3 5
evals/review-changes/grade.py <run-dir>
evals/review-changes/judge.py <run-dir> 1,2,3
evals/shared/export_results.py export evals/review-changes {{out_dir}} --version {{version}} --effort {{effort}} --run {{opus_model}}=<opus-run-dir> --run {{sonnet_model}}=<sonnet-run-dir>
```

The version comparison in section 6, with two copies of the skill in
`<skills>/v0.7/` and `<skills>/v0.8/`:

```sh
CONFIGS="v0.7 v0.8" SKILL_VERSIONS=<skills> MODEL=claude-opus-5-5 evals/review-changes/run_iteration.sh <run-dir> <fixture-dir> 3 6
evals/shared/session_usage.py <run-dir>/eval-*/*/run-*
evals/review-changes/grade.py <run-dir>
evals/review-changes/judge.py <run-dir> 1,2,3
evals/review-changes/compare_versions.py <run-dir> evals/review-changes/results/claude-code/v0.7-vs-v0.8 v0.7 v0.8
```

## Sources

[1] Anthropic. skill-creator. https://github.com/anthropics/skills/tree/main/skills/skill-creator
