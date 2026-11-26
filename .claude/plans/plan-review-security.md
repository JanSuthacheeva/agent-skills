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
  installed), start it in a parallel agent on `<target>...HEAD` while you review. Claude
  Code's command always diffs against `origin/HEAD`: when the target is another branch,
  tell the agent to review `git diff <target>...HEAD` in place of the diff the command
  shows. Without a parallel agent, run it yourself after your own pass.
- Its findings are the reviewer's own: prove each, fix the cheap ones, unproven ones go to
  Open as questions.
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
