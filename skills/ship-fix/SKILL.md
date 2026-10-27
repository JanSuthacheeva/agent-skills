---
name: ship-fix
description: >-
  Takes a bug from report or ticket to an open merge request by running
  diagnose-bug, implement-plan, review-changes and write-merge-request in
  order, stopping only where a decision belongs to the user and resuming
  from what the repository shows after an interruption. Use when the user
  asks to fix a bug or ticket all the way through, says "fix SHOP-311",
  "ship this fix", "take this bug to an MR" or "continue fixing", or wants
  a half-built fix plan carried on to a merge request. Not for features
  (ship-feature), for only diagnosing a bug (diagnose-bug), or for any
  other single step - build, review or MR - which the step's own skill
  handles.
metadata:
    author: Jan Suthacheeva
    version: "0.1"
---

Run the four delivery skills as one flow for a bug, so the user only makes
the decisions that are theirs: what the bug is when the report is unclear,
the fix plan, what the build or the review could not settle, and the push.
Every step is the step's own skill, unchanged - this skill only decides
which comes next, what each gets and where to stop.

## 1. Find where it stands

Derive the next step from the repository, never from memory, so the flow
resumes correctly in a new session:

| Found | Next |
|---|---|
| No fix plan for the report | Diagnose |
| A fix plan not yet committed on a fix branch | Ask the user to approve it |
| A plan with open task boxes | Build, from the first open task |
| All boxes ticked, no `## Review` in the plan | Review |
| `## Review` with open items not yet decided | Ask the user, then build the decided ones |
| Review done, no merge request for the branch | Merge request |
| A merge request is open | Done: give its URL |

The plan is the one the user names, else the plan the current branch adds
or ticks off, else an uncommitted fix plan for the same report - which is
not approved yet. If the request names a ticket and a tool can read it,
read it: it is the report, and the fix branch is named after its
identifier. Check that the commits agree with the ticked boxes;
if they do not, say so before going on. Tell the user in one line where
the flow stands and what comes next.

## 2. Diagnose - in this conversation

Use the diagnose-bug skill here, since its stops are conversations with
the user. If it stops - the report does not reproduce, or what should
happen is unclear - put its findings and what would help to the user, and
diagnose again once they answer. A report that does not reproduce gets no
plan and no branch.

When it has written the fix plan, always stop for approval, even with no
open questions: the plan decides what changes, and it is the cheapest
point to correct a wrong diagnosis. Show the root cause in two sentences,
the evidence, the plan's path and its open questions with
recommendations. Write the answers into the plan.

Once the user approves, make sure the work happens on a branch other than
the default one - named after the ticket identifier when there is one,
else after the bug, following the repository's branch convention - and
commit the plan on it.

Then hand over to the build in one line: ask the user to run `/compact`
and then say "continue fixing". You cannot compact yourself, and the
build should start from the plan, not from the diagnosis. If the user
goes on without compacting, build anyway.

## 3. Build - in this conversation

Use the implement-plan skill here, so the user can follow the build. The
plan is the spec: anything it does not say surfaces as a question, not
something filled in from the diagnosis or a summary of it.

The first task's regression test must fail for the reason the plan names
before the fix is written. If it passes, or fails for another reason, the
diagnosis is wrong: stop, show what the test did, and recommend
diagnosing again rather than adjusting the test until it fails. If the
user agrees, use diagnose-bug again to rewrite the plan in place, its
boxes open and the disproved cause noted, commit it, and return to the
approval stop.

If the build stops:

- **Blocked** on an expensive deviation: put the finding and your
  recommendation to the user, write the decision into the plan, commit
  it, and go on building.
- **Red base** - tests other than the plan's regression test that failed
  before the build began: ask the user whether to build on it.

When the build goes back to work after a review, tell implement-plan the
commit at which the review's checks last passed, so it does not run the
suite again on code nothing has changed.

## 4. Review - in a fresh agent

Start another fresh agent with only the review-changes skill, the branch,
its target, the plan's path and the commit at which the build's final
tests, lint and type checks passed. That commit is a fact you saw, not an
opinion of the code, and it saves the review from running the suite again
on unchanged code. It must not see this conversation, a report of the
build or your opinion of the code - an isolated review is the point of
this step. Tell it that it is that isolated review, so it reviews instead
of trying to isolate itself again. Without fresh agents, ask the user to
run the review in a new session and resume from there.

Then read the `## Review` section it wrote into the plan:

- **Open is empty**: go on.
- **Open has items**: put them to the user with the reviewer's
  recommendations. Write what the user decides into the plan as new tasks
  under `## Tasks`, before the end-to-end task, untick that task so the
  reproduction runs again, commit, and go back to Build. A second review then
  covers the new commits.

## 5. Merge request - in this conversation

Use the write-merge-request skill. Show the title and description, and
push and create the merge request only when the user says so. If one
already exists, offer to update its description instead.

## Stops

The flow waits for the user at exactly these points: a report that does
not reproduce or whose expected behaviour is unclear, approval of the fix
plan (including its open questions) and the compaction after it, a regression test that disproves the
diagnosis, a blocked build or red base, open review items, and the push.
Everywhere else it goes on without asking.

At a stop, say in a few lines what was found, the options and your
recommendation, and ask the user directly.

When the merge request is open, end with its URL, the commits per step,
the reproduction's result after the fix, and the review's "Where to look".
