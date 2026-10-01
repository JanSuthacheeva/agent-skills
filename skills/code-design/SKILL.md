---
name: code-design
description: >-
  Plan the code design of a feature or change before writing it: investigate
  the codebase, compare implementation approaches in a lavish artifact for
  the user to pick from, then lay out every class, method signature, data
  structure and call chain with diagrams - no function bodies. Use whenever
  the user asks to plan an implementation, design the code for a feature,
  figure out how something should be structured, which classes or methods
  are needed, or wants to discuss the design before any code is written,
  even if they just say "plan this" or "how would we build X". Not for
  product specs, task checklists, or trivial one-file changes.
compatibility: >-
  Requires the lavish skill (npx lavish-axi) for the review artifacts.
metadata:
    author: Jan Suthacheeva
    version: "0.4"
---

Produce a code design the user can discuss and correct before any code
exists. The design is about structure: which units exist, what they are
called, what their signatures are, and in what order they call each other
when something happens. It is not a task list and not an implementation -
method bodies are deliberately left out so the discussion stays on the
shape of the code, where changes are still cheap.

The work has four phases. Phases 2 and 3 each end at a human decision;
do not skip ahead of it.

## 1. Investigate

A design that ignores how the codebase already works is wrong even if it
is clean in isolation, so earn the right to propose one first.

- Find the entry points the feature hangs off (routes, commands, key
  handlers, jobs, events, CLI flags) and trace one or two similar existing
  features end to end. The closest sibling feature is the best template for
  naming, layering and wiring.
- Collect the conventions the design must follow: layering and where logic
  lives, naming patterns (suffixes like `Service`, `Repository`, `DTO`,
  module and file naming), how dependencies are injected, how errors are
  represented and surfaced, how data crosses boundaries, how things are
  tested. Read project rule files (`CLAUDE.md`, `AGENTS.md`, `.claude/rules/`,
  lint configs) - they state conventions the code only implies.
- Note what already exists that the feature can reuse, and what will have
  to change.
- For wide sweeps, dispatch Explore subagents in parallel and read the key
  files yourself. Keep `file:line` references for every claim you will
  make; the artifacts cite them.

If a requirement is ambiguous in a way that changes the design (not a
detail you can decide and flag), ask before phase 2. Keep it to the
questions that matter. Every behaviour you decide on the user's behalf
instead - an edge case, a default, where something lives - goes on the
assumptions list in phase 3, so no decision is made silently.

## 2. Approaches - the user decides

Present two or three approaches that differ in structure, not in naming:
where the logic lives, what owns the state, sync vs async, a new
abstraction vs extending an existing one, which layer is responsible. If
only one approach is sensible, say so and show the alternatives you
rejected and why, rather than inventing strawmen.

Build a lavish artifact, `.lavish/<slug>-approaches.html` (open the
`comparison`, `diagram` and `input` playbooks first). It only has to
support one decision, so keep it lean - roughly a screen per approach,
not a mini design doc. For each approach show:

- The idea in two or three sentences.
- One small component diagram: which units exist and how they connect,
  marking new, modified and existing units distinctly. Signatures,
  data shapes and call sequences belong on the implementation page.
- What it touches (files/modules), and how well it fits the conventions
  found in phase 1, with citations.
- Costs as visibly as benefits: complexity, coupling, migration,
  testability, performance, what it makes harder later.

Put a short "What exists today" section first so the user can check your
understanding of the codebase. End with your recommendation and why, and a
native radio form (one option per approach plus a rationale/notes
textarea) that queues exactly one prompt on submit, as the `input` playbook
describes.

Open it with `npx -y lavish-axi <file>`, poll for the decision, and answer
follow-up annotations until the user has chosen. The chosen approach may
be a mix - take what they say literally.

## 3. Implementation page - the user reviews

Now design the chosen approach in full. Write signatures in the codebase's
own language and syntax, following its conventions exactly, but with no
bodies (`;`, `{ ... }`, `todo!()` or the language's equivalent). Every name
is a proposal the user will judge, so choose names that say what the thing
does in the codebase's vocabulary.

Build the implementation page as a new lavish artifact,
`.lavish/<slug>-implementation.html` (open the `plan`, `diagram`, `code`
and `input` playbooks first). It holds the design and its code-level
detail on one page, with these sections:

1. **Decision recap** - the chosen approach in two sentences, and what was
   explicitly decided in phase 2.
2. **Structure overview** - one diagram of every unit involved, grouped by
   layer or module, new / modified / existing marked distinctly, arrows for
   dependencies.
3. **Units** - one card per class, module, struct or file:
   - file path, layer, new or modified
   - responsibility in one sentence (if it needs "and", question the split)
   - injected dependencies / collaborators
   - public methods with full typed signatures, each with a one-line
     description of what it does and what it returns or throws
   - for modified units, only the added or changed members, and what
     changes about existing ones
4. **Data** - new or changed DTOs, value objects, enums, models, schema or
   migrations, with fields and types. Show which boundary each one crosses.
5. **Call chains** - the heart of the design. For each trigger (a user
   action, request, command, event, job, key press) a sequence diagram of
   the calls in order, from the entry point down to persistence or output
   and back. Under each diagram, a numbered list of the same steps as
   `Caller -> Callee::method(args): Return`. Include the error paths: what
   fails where, what is thrown or returned, which layer handles it, and
   what the user ends up seeing. Draw error paths in the diagram too, but
   visually secondary to the happy path.
6. **Conventions followed** - the patterns the design copies, each with the
   `file:line` of the existing code it mirrors. Call out any place the
   design deviates from a convention and why.
7. **Test seams** - briefly, which units get tested at which level and
   what gets faked. One line per unit is enough.
8. **Assumptions** - every user-visible behaviour the design decides
   without the user having said so (edge cases, defaults, scope, where a
   setting lives, what happens on repeat or failure), one line each, so
   the user can confirm or overturn them at a glance.
9. **Open questions** - design choices you could not settle alone, each
   with your recommended answer and an input control so the user can
   answer in place.

Keep the diagrams one concept each: the overview shows topology, each call
chain shows one trigger. A dense everything-diagram is harder to review
than several small ones.

Before serving, check the design against itself: every method in a call
chain exists on a unit card with the same signature, every unit on a card
appears in the overview, every DTO used in a signature is defined in Data
or already exists. Mismatches here are what makes a design review go in
circles.

Open it, poll, and iterate on the user's annotations. Apply all changes
from one round of feedback in a single message, as parallel edits: every
separate tool call re-reads the whole conversation, so many sequential
small edits cost more than the page itself. Rewrite the page only when
the changes touch most of it. Rename consistently everywhere, remove
resolved open questions and fold the answer into the design. Continue
until the user approves.

## 4. Persist

Once approved - not before - write the design as a Markdown plan, in one
go, so a later implementation session can follow it without the browser.
Use the project's existing plan location if it has one (`docs/plans/`,
`.claude-bw/plans/`, or wherever earlier plans live), otherwise
`docs/plans/<YYYY-MM-DD>-<slug>.md`. If a hook or project rule rejects
that path, use the location it asks for and mention it.

The page stays the review surface; the Markdown only carries what an
implementation session needs, so do not copy the page into it. Link the
implementation page at the top, then: the decision in a few lines, units
with their paths and signatures in fenced code blocks, data structures,
call chains as numbered `Caller -> Callee::method(args): Return` steps
including error paths, test seams, the assumptions, and any decisions
made during review. Leave out the diagrams, the rationale prose and the
convention citations.

End the lavish session with `npx -y lavish-axi end <file>` and tell the
user where both files are. Do not start implementing unless asked.

## Artifacts

Save the pages under `.lavish/` in the project unless told otherwise.
Follow the lavish skill for design system choice, layout and render
verification.
