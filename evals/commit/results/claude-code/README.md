# Eval results: commit skill v2.8

11 scenarios, 5 trials each, run on 2026-09-27 with `claude-opus-5-5` in headless Claude Code (`claude -p`).

The eval method is based on the evaluation workflow of Anthropic's [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) skill (with-skill vs. baseline runs, graded assertions, benchmark), adapted for repeated headless trials against git fixtures.

- **with skill**: the installed `commit` skill, loaded the normal way.
- **without skill**: same environment with the skill hidden via `skillOverrides`, plus one system line asking for Scoped Commits (`<scope>: <description>`), so the baseline knows the target format.

A trial counts as passed only if every check for its scenario passes. Checks are graded by `grade.py` from the resulting repository, not from what the agent says it did.

| Scenario | Prompt | With skill | Without skill |
|---|---|---|---|
| staged-ticket-branch | "commit this" | 5/5 | 4/5 |
| nothing-staged-mixed | "ok the exponential backoff for the export worker is done, commit it" | 5/5 | 5/5 |
| push-multi-scope | "commit and push this" | 5/5 | 2/5 |
| breaking-change | "commit" | 5/5 | 2/5 |
| revert-default-message | "revert the export retry commit, it's causing duplicate exports" | 5/5 | 0/5 |
| merge-default-message | "I resolved the conflicts, finish the merge" | 5/5 | 2/5 |
| mixed-unrelated | "pagination for the invoice list endpoint is done, commit it" | 5/5 | 5/5 |
| conventional-history | "commit" | 5/5 | 5/5 |
| treewide | "commit" | 5/5 | 5/5 |
| no-scope-history | "commit" | 5/5 | 5/5 |
| split-unrelated | "all of these changes are done, commit them" | 5/5 | 5/5 |

| Per trial (mean) | With skill | Without skill |
|---|---|---|
| All checks passed | 55/55 | 40/55 |
| Checks passed | 100.0% | 91.2% |
| Cost | $0.205 | $0.210 |
| Output tokens | 719 | 864 |
| Turns | 6.2 | 4.8 |
| Duration | 15.3s | 14.8s |

Each `eval-*/<config>/run-*/` holds `grading.json` (every check with evidence), `timing.json`, the agent's final reply (`response.md`) and the commits it produced (`git_result.txt`). Scenario definitions live in `../../evals.json`, fixtures in `../../setup_fixture.sh`.

Agents were allowed only git, Read, Glob and Grep, so compound shell commands that mixed in other tools (`cat`, `grep`, `python3`) were denied; the agent then retried with allowed commands.

## Reproduce

```sh
commit/evals/run_iteration.sh <run-dir> <fixture-dir> 5 8
commit/evals/grade.py <run-dir>
commit/evals/export_results.py <run-dir> commit/evals/results/claude-code 2.8 claude-opus-5-5
```
