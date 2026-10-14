---
name: review-changes
description: >-
  Reviews the changes on a branch in an isolated context - without the
  conversation that wrote them - against the plan and the project's rules,
  proves each finding, fixes the ones that are cheap to reverse, reviews
  the production-code fixes again, and leaves a short summary of the
  risks and where a human should look. Use when the user asks to review a branch, an
  implementation or the current changes before a merge request, or after
  implement-plan has finished, even if they just say "review this". Not
  for commenting on someone else's merge request or for lint-only passes.
metadata:
    author: Jan Suthacheeva
    version: "0.4"
---

An agent reviewing code it just wrote tends to confirm its own choices, so
the review always runs in a context that has not seen the implementation:
it judges the code by what is in the repository, not by what was meant.

## 1. Isolate

- If this conversation wrote or planned the changes, do not review them
  here. Start a fresh agent, if your environment can, and give it only
  the branch, its target, the plan's path and this skill - never the
  conversation or your own summary of it. Without one, ask the user to
  run the review in a new session.
- If this conversation did not write them, you are already isolated: go on.
  This includes an agent started only to review, given just the branch
  and the plan - that agent is the isolated review, not a step before it.

## 2. Gather

- The commits and the diff against the target branch
  (`git log <target>..HEAD`, `git diff <target>...HEAD`).
- The plan: the one the user names, else a plan file the branch adds or
  ticks off, else the commits and the ticket as the statement of intent.
- The project's rules (such as `AGENTS.md`, contributing docs, lint
  configs) and the code the diff calls or is called from.
- Run the tests, lint and type checks once, so you know what was green
  before you touched anything.

## 3. Review

Read every changed line. Go through these in order, most costly to miss
first:

1. **Data** - what is stored and in what format, migrations, and what
   happens to stored data when something fails: a read error that turns
   into an empty result and is then saved over the file loses it.
2. **Boundaries** - each unit does the job the plan and the rules give it.
   Look for logic in the wrong layer, a unit bypassed and reimplemented
   by its caller, and code left dead by that.
3. **Behaviour against the plan** - every call chain, error path, exit
   code, message, name and signature the plan states.
4. **Errors** - swallowed, widened or mismapped errors, and failures that
   pass silently.
5. **Tests** - every behaviour and error path in the plan has a test that
   fails without the code.
6. **Conventions** - the project's rules and the patterns of the code
   around it.

Prove each finding before acting on it: a failing test, or a command run
that shows the wrong result. Something you suspect but cannot show is a
question for the summary, not a fix. Correct code you would have written
differently is not a finding.

## 4. Fix

Sort findings by what they cost to reverse once shipped:

- **Fix** the cheap ones: write the failing test first, fix, run the
  suite, lint and type checks, and commit each finding, or a few closely
  related ones, on its own. If a fix changes something the plan states,
  update the plan in the same commit.
- **Do not fix** the expensive ones - stored data and its format, the
  public surface (commands, flags, endpoints, payloads), user-visible
  behaviour, a different design. Put them in the summary with your
  recommendation.

## 5. Review the fixes

Fixes that only add or change tests are proven by running them; skip this
step for them. When a fix changed production code, review those commits
once more, by a fresh agent if you can - you wrote them, so the same bias
applies. Give it only the fix commits and the findings they address. It
checks a small diff against named findings, so a smaller, faster model is
enough. If you cannot start one - an agent that was itself started by
another often cannot - review them yourself in a separate pass: re-read
each fix commit against its finding as if someone else wrote it, try the
input that showed the finding and its neighbours, and say in the summary
that the fixes were not reviewed independently. Stop after this one
round; whatever is still open goes into the summary.

## 6. Summary

Keep it short and plain - the user reads this instead of every line:

- **Fixed** - one line per finding: what was wrong, how it showed, the
  commit.
- **Open** - findings left for the user and open questions, each with
  your recommendation.
- **Where to look** - the two to four places that carry the real risk,
  as a reading order the user can follow in one sitting, for example
  "`src/store.ts` `load()` to `save()`: what happens to a corrupt file".
  Say what is routine and can be skimmed.

If the branch has a plan, also write the summary into it as a
`## Review` section at the end, replacing an earlier one, and commit it.
The plan then records that the branch was reviewed, and whoever writes
the merge request can start its reading guide from it.

Do not push or open a merge request unless asked.
