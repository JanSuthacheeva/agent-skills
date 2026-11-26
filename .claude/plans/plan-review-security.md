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
0cd6830 (aeaba7c, 8c0bc0e), with the whole branch as context. The new
sentence in step 3 closes the open item that review left: the reviewer
now waits for the security agent before fixing, so its findings reach
step 4 and the summary. It is consistent with the no-agent path (run it
after your own pass, which is still before fixing). The whole branch
still matches the plan; the earlier fixes (730ebbd, 1e450a8, 6d91b68)
stand.

**Fixed**

- The plan's Units section still described the step-3 paragraph without
  the wait the new task added, and had one line run on past the wrap
  (ec73479).

The fix is plan text only and was re-read in a separate pass, not by an
independent agent.

**Open**

- The two-tool claims (Claude Code 2.1.332's fixed `origin/HEAD` base,
  Codex's `security-diff-scan`) are tied to current versions; the Codex
  side was not checked. Recommend re-checking when either tool updates.
- The README's review-changes eval numbers were measured on an earlier
  version without the security step. Recommend re-running the eval
  before quoting them for 0.8.

**Where to look**

- `skills/review-changes/SKILL.md` step 3, the opening paragraph: the
  only behaviour change on the branch - the parallel security review,
  the `origin/HEAD` caveat and the wait before fixing.
- Checklist item 2 and the renumbering, the description rewrap and the
  eval report template: routine, skim.

**Checks**

No tests, lint or type checks exist for skill text. YAML frontmatter
parses (checked with Ruby) at 8c0bc0e; the changed lines are within 74
columns. No security review tool was run: the diff is Markdown only.
