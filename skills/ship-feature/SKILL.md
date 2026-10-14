---
name: ship-feature
description: >-
  Takes a feature from request or ticket to an open merge request by
  running design-code, implement-plan, review-changes and
  write-merge-request in order - the build and the review each in a fresh
  agent - stopping only where a decision belongs to the user, and resuming
  from what the repository shows after an interruption. Use when the user
  asks to ship, deliver or take a feature or ticket all the way through,
  says "ship SHOP-217", "do the whole flow" or "continue shipping", or
  wants a half-built plan carried on to a merge request. Not for a single
  step on its own - plan, build, review or MR - which the step's own skill
  handles.
metadata:
    author: Jan Suthacheeva
    version: "0.2"
---

Run the four delivery skills as one flow, so the user only makes the
decisions that are theirs: the approach, the plan, what the build or the
review could not settle, and the push. Every step is the step's own skill,
unchanged - this skill only decides which comes next, what each gets and
where to stop.

## 1. Find where it stands

Derive the next step from the repository, never from memory, so the flow
resumes correctly in a new session:

| Found | Next |
|---|---|
| No plan for the request | Design |
| A plan with open task boxes | Build, from the first open task |
| All boxes ticked, no `## Review` in the plan | Review |
| `## Review` with open items not yet decided | Ask the user, then build the decided ones |
| Review done, no merge request for the branch | Merge request |
| A merge request is open | Done: give its URL |

The plan is the one the user names, else the plan the current branch adds
or ticks off. If the request names a ticket and a tool can read it, read
it: it is the request, and the branch is named after its identifier.
Check that the commits agree with the ticked boxes; if they do not, say
so before going on. Tell the user in one line where the flow stands and
what comes next.

## 2. Design - in this conversation

Use the design-code skill here, since its two stops - choosing the
approach and approving the implementation - are conversations with the
user. Continue only after the user has approved the plan. Then make sure
the work happens on a feature branch, not the default branch, and that the
plan is committed on it.

## 3. Build - in a fresh agent

Start a fresh agent, if your environment can, and give it only:

- the instruction to use the implement-plan skill (by name, or the path
  of its skill file if the agent cannot load skills by name)
- the plan's path and the branch
- decisions the user made for this build, if any

Never the design conversation or a summary of it: the plan is the spec,
and anything the plan does not say should surface as a question, not be
filled in from memory. Without fresh agents, run the build here.

When the agent returns, check the result in the repository - commits,
ticked boxes, a green suite - rather than trusting its report. If it
stopped:

- **Blocked** on an expensive deviation: put its finding and
  recommendation to the user, write the decision into the plan, commit
  it, and start a new build agent.
- **Red base** - tests that failed before the build began: ask the user
  whether to build on it.

## 4. Review - in a fresh agent

Start another fresh agent with only the review-changes skill, the branch,
its target and the plan's path. It must not see this conversation, the
build agent's report or your opinion of the code - an isolated review is
the point of this step. Tell it that it is that isolated review, so it
reviews instead of trying to isolate itself again. Without fresh agents,
ask the user to run the review in a new session and resume from there.

Then read the `## Review` section it wrote into the plan:

- **Open is empty**: go on.
- **Open has items**: put them to the user with the reviewer's
  recommendations. Write what the user decides into the plan as new tasks
  under `## Tasks`, commit, and go back to Build. A second review then
  covers the new commits.

## 5. Merge request - in this conversation

Use the write-merge-request skill. Show the title and description, and
push and create the merge request only when the user says so. If one
already exists, offer to update its description instead.

## Stops

The flow waits for the user at exactly these points: approach, plan
approval, a blocked build or red base, open review items, and the push.
Everywhere else it goes on without asking. At a stop, say in a few lines
what was found, the options and your recommendation. If your environment
lets you report to a coordinating session, send the stop there;
otherwise ask the user directly.

When the merge request is open, end with its URL, the commits per step,
and the review's "Where to look".
