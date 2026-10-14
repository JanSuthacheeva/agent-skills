---
name: implement-plan
description: >-
  Implements an approved implementation plan task by task: works through
  its `- [ ]` task checklist in order, writes each task's tests first,
  keeps to the plan's names, signatures and call chains, commits every
  task, and finishes with an end-to-end check and a short note on how the
  result works. Use when the user asks to implement, build, execute or start on a
  plan file, especially one written by design-code, or says "build it" or
  "go" after approving a plan. Not for writing plans (use design-code) or
  for small changes that have no plan.
metadata:
    author: Jan Suthacheeva
    version: "0.3"
---

Build what the plan says, in the order its tasks say, so the user gets the
design they approved - not one that drifted task by task. The plan is the
record: it stays true to the code, and its checkboxes show how far the
build is.

## 1. Load

- Read the whole plan, not only the tasks. The units, signatures, call
  chains and assumptions are the spec each task is built against.
- Find the tasks: the `## Tasks` section, or the plan's checkboxes. Ticked
  ones are done - resume at the first open task, and check `git log`
  agrees.
- Read the project's agent and contributor rules (such as `AGENTS.md`
  and lint configs) and the existing code the plan cites, and find how
  tests, lint and type checks are run.
- Run the tests once before changing anything. Failures that exist before
  you start are not yours, but they hide yours, so report them up front.
- Tick each task's checkbox in the plan when it is done, so the file
  shows how far the build is. If your environment offers a tool for
  reporting plan progress, use it instead - doing, done, blocked - and
  let it tick the boxes.

## 2. Build each task

One task at a time, in order:

1. Mark it as in progress, if your progress tool has that state.
2. Write the tests the task names, run them, and see them fail for the
   expected reason - a missing method, a wrong value - not a typo or an
   import error. A task without a test of its own (wiring, a migration)
   still needs something that proves it; say what.
3. Implement it with the plan's names and signatures exactly, following
   the conventions the plan cites.
4. Run the task's tests, then the affected suite, lint and type checks.
   Do not start the next task while anything is red.
5. Tick it and commit it as one commit, with the project's commit
   convention or skill. Plan updates from this task go in the same commit.

Small, green, committed steps mean a wrong turn costs one task, and the
history reads like the plan.

## 3. When the design is wrong

Building shows things the design missed. Sort each change by what it
costs to reverse once shipped - the same rule design-code used to decide
what to ask:

- **Make it** when it is cheap to undo: an internal name, an extracted
  helper, a private method, the parameter order of an internal call, an
  extra test. Update the plan where it changed - unit, signature, call
  chain - and note it for the summary, so the plan stays the record.
- **Stop and ask** when it is expensive to undo or the user would notice:
  what is stored and in what format, migrations, the public surface
  (commands, flags, endpoints, payloads), user-visible behaviour, a new
  dependency, or a different approach than the one chosen. Mark the task
  blocked if you can, explain what you found, and give your recommendation. Do not
  build a workaround in the meantime.

A task that turns out much larger than it looked gets split: add the new
tasks as checkboxes in its place before building them.

## 4. Verify and hand over

- Run the end-to-end check the plan ends with, the way a user would use
  the feature - the real command, request or page - and show what you
  observed. Passing unit tests are not that check.
- Run the full test suite, lint and type checks once more.
- Summarize in a few lines:
  - the tasks done, with their commits
  - every deviation from the plan, and why
  - anything blocked or left open
  - how the result works: the path from the entry point through the main
    units, so the user understands what was built, not only that it was
    built

Do not push or open a merge request unless asked.
