---
name: diagnose-bug
description: >-
  Reproduces a reported bug end to end the way a user hits it, traces it
  to its root cause and proves the cause with an experiment, then writes a
  fix plan whose first task is a failing regression test and whose last is
  the end-to-end check - without changing any code. Use when the user asks
  to diagnose, reproduce or find the cause of a bug, says "why does X
  happen", "look into SHOP-311" or hands over a bug report or ticket.
  Not for building the fix (implement-plan, ship-fix) or for features
  (design-code).
metadata:
    author: Jan Suthacheeva
    version: "0.1"
---

Find out why a bug happens before anyone changes code, so the fix lands on
the cause and not on the place the user happened to notice it. A report
names a symptom, and a reporter's guess at the cause is often wrong; only a
reproduction and an experiment tell them apart. The result is a fix plan
another session can build without this conversation.

Change no code and commit nothing. Copy this checklist and tick it off as
you go:

```
- [ ] 1. Read the report
- [ ] 2. Reproduce it end to end
- [ ] 3. Find the root cause
- [ ] 4. Decide the fix
- [ ] 5. Write the fix plan
- [ ] 6. Hand over
```

## 1. Read the report

If the report names a ticket and a tool can read it, read it: the ticket
is the report. Pull out what the user expected, what happened instead, the
steps they took and their environment (version, data, platform).

Keep the reporter's guess at the cause apart from what they saw. "List is
broken" is a guess; "list shows nothing after I added a bookmark" is an
observation, and the observation is what you reproduce.

If what should happen is unclear - the report could describe intended
behaviour, or two readings lead to different fixes - ask before going on.
A fix for the wrong expectation is a new bug.

## 2. Reproduce it end to end

Reproduce it the way the user hits it: the real command, request or page,
with the reporter's steps and input, against the application as it runs,
not a unit test written from a guess. A unit test only exercises the path
you already suspect; the end-to-end run shows the path the user takes.
Read [references/reproduce.md](references/reproduce.md) for how to do this
per kind of surface and for intermittent bugs.

Record the exact steps, the input and the output you observed, and how
often it fails. Keep anything you create for it - scratch data, files,
scripts - outside the project or remove it afterwards.

If it does not reproduce after the reporter's steps and the obvious
variations, stop: write no plan. Tell the user what you tried, what you
observed and what would help (data, version, exact steps), and ask.

## 3. Find the root cause

The root cause is the first place where the state goes wrong, not the
place where it becomes visible. Trace back from the symptom: where did the
wrong value come from, and where did that come from, until you reach code
that does the wrong thing with correct input.

- Form one hypothesis at a time and test it with an experiment that could
  prove it wrong: inspect the stored data, add a temporary log, run a
  scratch test, call the unit directly. Reading code suggests a cause; an
  experiment proves it.
- The cause must explain every symptom in the report, including the ones
  the reporter did not connect. If one is left over, keep looking.
- Find when it came in, with `git log -S <code>` or `git blame` on the
  lines: the commit's intent often shows what the code was meant to do,
  and whether other places were changed the same way.

Remove every temporary log and scratch test before going on.

## 4. Decide the fix

Fix where it first goes wrong. A guard where the symptom shows leaves the
wrong state in place for the next reader of it.

- Look for siblings: the same mistake in other places, written by the same
  commit or copied from the same pattern.
- Look at the data: if the bug has already written wrong data, the fix
  stops new damage but does not repair the old. Always list it.
- Sort every choice by what it costs to reverse once shipped. Assume the
  cheap ones - an internal name, a helper, the shape of the test - and
  list them. Ask about the expensive ones: what is stored and in what
  format, a repair of data already damaged, the public surface (commands,
  flags, endpoints, payloads), and user-visible behaviour beyond what the
  report expects. They become open questions in the plan, each with your
  recommendation.

## 5. Write the fix plan

Write the plan where the project keeps its plans (`docs/plans/`,
`.claude/plans/` or wherever earlier plans live), otherwise in
`docs/plans/<YYYY-MM-DD>-fix-<slug>.md`. Follow the format in
[references/fix-plan-format.md](references/fix-plan-format.md).

The first task adds the regression test and fixes the cause in one step,
naming the message the test fails with today; whoever builds it sees the
test fail for that reason before fixing. The last task runs the
reproduction from step 2 again and names the output that shows it fixed.
Use checkboxes only in the `## Tasks` section, since progress trackers
count every checkbox in the file.

## 6. Hand over

Leave the working tree as you found it, except for the plan. Do not
commit, branch or start the fix unless the user asks.

Tell the user in a few lines:

- the root cause in two sentences, with its `file:line`
- the evidence: the reproduction and the experiment that proved the cause
- what else is affected, including damaged data
- the plan's path, and its open questions, numbered, each with your
  recommendation
