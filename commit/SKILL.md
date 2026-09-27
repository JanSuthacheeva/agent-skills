---
name: commit
description: >-
  Write and create a git commit in Scoped Commits format (`<scope>:
  <description>`). Use when the user says "commit" or asks for a commit
  message, or when a finished unit of work is ready to commit. Never pushes,
  pulls, merges or rebases.
compatibility: Requires git
metadata:
    author: Jan Suthacheeva
    version: "2.7"
allowed-tools: >-
  Bash(git status:*) Bash(git branch:*) Bash(git log:*) Bash(git diff:*)
  Bash(git add:*) Bash(git commit:*) Read
---

Commit the staged changes with one Scoped Commits message.

## Workflow

1. One call: `git status --short; git branch --show-current;
   git log --format=%s -n 20; git diff --staged --stat`
2. Nothing staged: `git add <paths>` for the files of the finished
   work yourself. Leave out unrelated changes and scratch files, and
   name them in your reply. Never `git add .` or `-A`. Ask only if you
   can't tell which changes belong to the work.
3. Read `git diff --staged` unless you made exactly these changes in
   this session.
4. Commit right away with one `-m` per paragraph, then show the
   message. Never push, pull, merge, rebase, `--no-verify` or
   `--no-gpg-sign`.

## Rules

- Subject `<scope>: <description>`: max 72 chars, start lowercase, no
  type prefix (`feat`, `fix`) even if the log uses them.
- Scope: the area touched, named as the codebase names it; reuse scopes
  from the log. Nest for precision (`api: auth: ...`), comma-separate
  multiple (`api, worker: ...`), `treewide` for the whole tree, or omit
  if nothing fits.
- Body only if the subject isn't enough: wrap at 72, explain why, not
  what. State breaking changes and their migration here.
- Branch matches `[A-Z]+-\d+` (first match): add `Refs: <ID>` trailer.
  Never invent one.
- Reverts and merges keep git's default message.

## Example

```
billing: round totals per line instead of per invoice

Per-invoice rounding drifted from the PDF totals by up to one cent,
which the accounting export rejected.

Refs: HGAI-2050
```
