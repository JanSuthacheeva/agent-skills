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
  or `origin/HEAD` is not set (a remote added by hand, not cloned), tell the agent to
  review `git diff <target>...HEAD` in place of the diff the command shows. Without a parallel agent, run it yourself after your own pass.
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

## Review

Reviewed in an isolated agent against this plan. The change matches the
plan: the parallel security review on `<target>...HEAD`, the
`origin/HEAD` caveat, findings treated as the reviewer's own, the new
**Security** item at 2, the Checks line and the bump to 0.8.

**Fixed**

- The description rewrap left `request, or after` alone on a line, then
  ran on at the old width (730ebbd).
- `/security-review` runs `git diff origin/HEAD...`; in a repository
  whose remote was added by hand, not cloned, `origin/HEAD` is unset and
  git fails with "ambiguous argument 'origin/HEAD...'" (shown in a
  scratch repo). The skill now also passes the range in that case
  (1e450a8, plan updated).
- The eval report template still described the step-3 order without
  security, so the next run would have described 0.8 wrongly (6d91b68).

The fixes are text only and were re-read in a separate pass, not by an
independent agent.

**Open**

- Nothing tells the reviewer to wait for the parallel security agent
  before step 4 or the summary. "Its findings are yours" implies it;
  recommend leaving it unless a flow run shows a summary written before
  the agent returned.
- The two-tool claims (Claude Code 2.1.332's fixed `origin/HEAD` base,
  Codex's `security-diff-scan`) are tied to current versions. The
  `origin/HEAD` base was confirmed in the 2.1.332 binary; the Codex side
  was not checked here.

**Where to look**

- `skills/review-changes/SKILL.md` step 3, the opening paragraph: the
  only real behaviour change, and the base-branch caveat that decides
  whether a stacked branch gets reviewed correctly.
- Checklist item 2 and the renumbering: routine, skim.

**Checks**

No tests, lint or type checks exist for skill text. YAML frontmatter
parses (checked with Ruby) at 6d91b68. No security review tool was run:
the diff is Markdown only.
