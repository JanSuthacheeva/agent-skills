---
name: merge-request
description: >-
  Write the title and description of a GitLab merge request or GitHub pull
  request for the current branch - what changed and why, not a tour of the
  diff - and create it once the user approves the push. Use when the user
  asks to open, create or draft an MR or PR, write or improve an MR/PR
  description, or get a branch ready for review, even if they just say
  "MR please". Not for reviewing MRs or writing commit messages.
compatibility: >-
  Requires git, and glab (GitLab) or gh (GitHub) to create the MR. Reads
  the ticket title with clickup-axi when it is installed.
metadata:
    author: Jan Suthacheeva
    version: "0.2"
allowed-tools: >-
  Bash(git status:*) Bash(git branch:*) Bash(git log:*) Bash(git diff:*)
  Bash(git remote:*) Bash(git symbolic-ref:*) Bash(git rev-parse:*)
  Bash(clickup-axi tasks:*) Bash(glab mr list:*) Bash(gh pr view:*) Read
---

Write an MR a reviewer can judge in a minute: what the branch does and why.
The diff is one click away, so the description carries what the diff
cannot show - the reason, the decisions a reviewer would question, and
what breaks or stays open.

## Workflow

1. One call: `git branch --show-current; git remote get-url origin;
   git symbolic-ref --short refs/remotes/origin/HEAD; git status --short`.
   The target is the default branch unless the user names another.
2. One call: `git log --format='%h %s%n%b' <target>..HEAD;
   git diff --stat <target>...HEAD`. Read the diff itself where the
   commits do not explain why something changed. If the branch follows a
   plan or ticket, read it - it usually holds the why.
3. Check for an open MR of the branch (`glab mr list --source-branch
   <branch>` or `gh pr view`). If one exists, say so and offer to rewrite
   its description instead of creating a second one.
4. Write the title and description (below) and show them. Stop there.
5. Create the MR only when the user's latest message asks to push or
   create it - pushing publishes the branch, so earlier approval does not
   count. Then `git push -u origin <branch>` and
   `glab mr create --target-branch <target> --title ... --description ...`
   or `gh pr create --base <target> --title ... --body ...`, and give the
   URL. Never force-push. Pass the description through a quoted heredoc,
   `--description "$(cat <<'EOF' ... EOF)"`, so backticks and `$` reach
   the MR as written instead of escaped or expanded.

Uncommitted changes are not part of the MR. Mention them, do not commit
them yourself.

## Title

- Branch name contains a ticket ID (`[A-Z]+-\d+`, first match) and the
  ticket's title can be read, e.g. with `clickup-axi tasks <ID>`:
  `<ID> <ticket title>`, the title verbatim.
  `SHOP-142 Checkout: Remember the last used shipping address`
- Otherwise Scoped Commits, like the repo's commits: `<scope>: <description>`,
  max 72 chars, starting lowercase, reusing scopes from the log.
  `billing: round totals per line instead of per invoice`

## Description

```
<What the MR does and why, in one to three sentences: the problem or goal
first, then the change that addresses it.>

- <A decision a reviewer would question, with its reason.>

<Breaking changes and how to migrate, if any.>
<What is deliberately left out or follows later, if anything.>

Refs: <ID>
```

- Scale it to the change: a one-commit fix can be a single sentence.
- Bullets only for decisions that are not obvious from the code: a
  trade-off, a rejected alternative, a deviation from a convention or
  plan, a migration or data change, a new dependency. Each one says why.
- Take the reasons from the commits, the plan, the ticket or the code.
  A reason you would have to guess is not one: leave the decision out, or
  ask. A reviewer trusts the description as the author's intent.
- Leave out what the diff already shows or reviewers do not need: a
  file-by-file or commit-by-commit list, a "How to test" section or test
  checklist, generic checklists, empty template headings, screenshots
  placeholders, and praise for the change.
- `Refs: <ID>` only when the branch has a ticket ID; never invent one.
  On GitHub, `Closes #<n>` when the branch closes an issue.
- Write in the language of the repo's commits.

## Example

Branch `feature/SHOP-142-remember-address`, three commits that store the
address of the last order and prefill checkout with it:

```
SHOP-142 Checkout: Remember the last used shipping address

Returning customers had to type their shipping address on every order.
Checkout now prefills it from the customer's last order.

- The address is read from the last order instead of a new
  saved-addresses table, so there is no migration; a real address book
  can replace it later without touching checkout.
- Guests are not affected - nothing is stored without an account.

Refs: SHOP-142
```
