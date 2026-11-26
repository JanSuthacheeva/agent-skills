# Plan: security review in review-changes

## Decision

review-changes runs the harness's own security review of the branch alongside its
normal review, so ship-feature and ship-fix get it on every flow without changing
either. The ship skills stay untouched.

Verified facts:

- Claude Code's `/security-review` (2.1.332, prompt in the binary) diffs against a fixed
  base: `git diff origin/HEAD...`, `git log origin/HEAD...`. It takes no base argument.
  On a stacked branch (`--base` flow, target is not the remote default branch) it would
  review the whole stack. It is a skill a subagent can invoke, and subagents can start
  their own agents (probed 2026-11-26).
- Codex has no built-in equivalent; `/review` has no security mode. The Codex Security
  plugin (`codex plugin add codex-security@openai-curated`) adds the skill
  `codex-security:security-diff-scan`, which takes the range in plain words ("review the
  changes from origin/main to HEAD"). Docs:
  https://learn.chatgpt.com/docs/security/plugin/code-changes (was
  developers.openai.com/codex/security/plugin/code-changes).
- Both tools report and do not fix; Claude Code's reads code only, without running it.

## Units

### `skills/review-changes/SKILL.md`

- Step 3 opens with: if the harness has a security review for changes (Claude Code's
  `/security-review`, Codex's `codex-security:security-diff-scan` when the plugin is
  installed), start a parallel agent that invokes it by name on `<target>...HEAD` while
  you review. Claude Code's command always diffs against `origin/HEAD`: when the target
  is another branch, tell the agent to review `git diff <target>...HEAD` in place of the
  diff the command shows. Without `origin/HEAD` (a remote added by hand, not cloned) the
  command fails to load (seen in the eval): skip it and say so. Without a parallel
  agent, run it yourself after your own pass.
- Wait for its findings before fixing anything. They are the reviewer's own: prove each,
  fix the cheap ones, unproven ones go to Open as questions.
- New checklist item 2, **Security**: untrusted input reaching queries, shells, paths or
  templates; missing auth or authorization checks; secrets in code or logs. Kept even when
  the tool runs - it is the fallback in any harness without one and a second look in
  those with one.
- Summary, Checks: say whether the security review ran and with which tool.
- Version 0.7 -> 0.8.

## Tasks

- [x] review-changes: start the harness's security review in parallel on the branch's
      range, treat its findings as the reviewer's own, add the Security checklist item and
      the summary line, bump to 0.8
- [x] review-changes: wait for the security agent's findings before
      fixing (decided after review: a finding lost to a summary written
      first is the costly case)
- [x] evals (asked for after review): security scenarios in evals/review-changes - an
      injection in the branch's own diff, a stacked branch whose security bug is only in
      the lower branch, no origin/HEAD, a clean branch, a subtle XSS - and v0.7 against
      v0.8 on the full suite, three trials each, written into report.md

## Review

Reviewed in an isolated agent: the commits since the earlier review at
cbdb2bb (da6111b..2c92892), with the whole branch as context. The
step-3 change (invoke the command by name, skip it without
`origin/HEAD`) matches the plan's Units section. All eight scenarios
build with `setup_fixture.sh` and pass `npm test`; graded against the
unfixed fixtures, every planted-defect check fails and clean-branch
passes 5/5, so the checks discriminate. `compare_versions.py` on the
graded trials reproduces the committed `comparison.md` byte for byte.

**Fixed**

- `run_trial.sh` ran a version config silently without the skill when
  its directory was missing under `SKILL_VERSIONS` (or the config was
  mistyped), and graded it under that version's name; shown by running
  the selection lines with a missing directory. It now fails (3bd15b7).
- `SKILL.md` step 3 had a line at 77 columns (0bc865e).
- `report.md` and the rendered README said v0.8's own pass, "not the
  security agent", reported the lower branch's injection; the
  transcripts show the security agent noted it in all three stacked
  trials. Cost rise was 65% from rounded means, 64% unrounded
  (c9fe114).

The `run_trial.sh` fix was re-checked in a separate pass (every config
case run in isolation), not by an independent agent; trials were not
re-run.

**Open**

- The Codex side of the two-tool claim is still unchecked. Recommend
  re-checking when either tool updates.
- subtle-xss: `href` is written unescaped too, and `bm add` (on main)
  stores any URL, so `bm add 'x" onmouseover="alert(1)'` also breaks out
  of the exported page. Not planted; a reviewer fixing it is not
  penalised by the grader. Recommend naming it in the scenario's
  `planted` notes, or validating `add`, before the next run.
- The abstract says v0.8 "matched" v0.7 on all eight scenarios while
  Table 7 shows stacked-base 0/3 (the deliberate heuristic failure
  section 6 explains). Recommend leaving as is or saying "matched in
  detection".
- "Three subagents in place of one" is approximate (v0.8 mean 2.8,
  range 1-5).

**Where to look**

- `skills/review-changes/SKILL.md` step 3, the opening paragraph: the
  only behaviour change since the last review.
- `evals/review-changes/setup_fixture.sh` the `case $variant` block:
  how each security scenario's base, origin and `origin/HEAD` are set.
- `evals/review-changes/report.md` section 6: the claims drawn from the
  trials.
- Routine, skim: the per-run result files, `grade.py` checks (verified
  against the unfixed fixtures), the `splitlines` to `split("\n")`
  change in the other evals scripts (so U+2028 inside JSON strings does
  not split a transcript line).

**Checks**

At c9fe114: `py_compile` on every changed Python file, `bash -n` on the
review-changes shell scripts, `setup_fixture.sh` plus `npm test` for
all eight scenarios - all green. No lint or type checks exist for the
skill text. No security review tool was run: the changes are eval
tooling and Markdown run locally, with no untrusted input beyond the
fixtures.
