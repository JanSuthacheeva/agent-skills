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
  Requires python3 and npx (lavish-axi) for the review pages.
metadata:
    author: Jan Suthacheeva
    version: "0.2"
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
  make; the pages cite them.

If a requirement is ambiguous in a way that changes the design (not a
detail you can decide and flag), ask before phase 2. Keep it to the
questions that matter.

## 2. Approaches - the user decides

Present two or three approaches that differ in structure, not in naming:
where the logic lives, what owns the state, sync vs async, a new
abstraction vs extending an existing one, which layer is responsible. If
only one approach is sensible, say so and show the alternatives you
rejected and why, rather than inventing strawmen.

Write `.lavish/<slug>-approaches.md` and render it (see "Approaches page"
below).
Keep it lean - this page only has to support one decision, so about a
screen per approach:

- `## What exists today` first, a few bullets with citations, so the user
  can check your understanding of the codebase.
- `## Approach A - <name>` per approach: the idea in two or three
  sentences, a small Mermaid `flowchart` of the units involved, then short
  bullet lists for what it touches, how it fits the conventions found in
  phase 1, and its costs (complexity, coupling, migration, testability,
  what it makes harder later). Make the costs as visible as the benefits.
- `## Recommendation` with your pick and why, followed by a `decision`
  block with one option per approach.

Open the page, poll for the decision, and answer follow-up annotations
until the user has chosen. The chosen approach may be a mix - take what
they say literally.

## 3. Implementation page - the user reviews

Now design the chosen approach in full. Write signatures in the codebase's
own language and syntax, following its conventions exactly, but with no
bodies (`;`, `{ ... }`, `todo!()` or the language's equivalent). Every name
is a proposal the user will judge, so choose names that say what the thing
does in the codebase's vocabulary.

Build the implementation page by hand as a lavish artifact,
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
8. **Open questions** - design choices you could not settle alone, each
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

Open it, poll, and iterate on the user's annotations. Update the artifact
in place - rename consistently everywhere, remove resolved open questions
and fold the answer into the design. Continue until the user approves.

## 4. Persist

Once approved, write the design as a Markdown plan so a later
implementation session can follow it without the browser. Use the
project's existing plan location if it has one (`docs/plans/`,
`.claude-bw/plans/`, or wherever earlier plans live), otherwise
`docs/plans/<YYYY-MM-DD>-<slug>.md`. If a hook or project rule rejects
that path, use the location it asks for and mention it.

The Markdown carries the same content as the artifact: decision recap,
units with signatures in fenced code blocks, data structures, call chains
as numbered steps (Mermaid `sequenceDiagram` blocks are fine here),
conventions followed, test seams, and any decisions made during review.
Link the HTML artifact path at the top.

End the lavish session with `npx -y lavish-axi end <file>` and tell the
user where both files are. Do not start implementing unless asked.

## Approaches page

The approaches page is written as Markdown and turned into the lavish page
by a bundled script, so it costs no hand-written HTML. The script owns
that page's design, so no lavish playbooks are needed for it. The
implementation page is hand-built (phase 3).

- Render: `python3 <this skill's directory>/scripts/render.py <file>.md`
  writes `<file>.html` next to it. Re-run it after every edit.
- Mermaid ` ```mermaid ` blocks render as diagrams. In flowcharts, tag
  nodes with `:::new`, `:::modified` or `:::existing` for consistent
  colouring. Quote labels that contain punctuation (`A["Get(id)"]`).
- `[new]`, `[modified]`, `[existing]`, `[removed]`, `[recommended]` and
  `[rejected]` in headings, lists and tables render as badges.
- A choice the user should make in the browser is a fenced `decision`
  block; it renders as a form that sends the answer back through lavish:

  ````
  ```decision
  id: approach
  question: Which approach should the design use?
  - A: Check first, in the command (recommended)
  - B: Send first, explain on failure
  ```
  ````

- Review loop (both pages): open with `npx -y lavish-axi <file>.html`,
  then run `npx -y lavish-axi poll <file>.html` (in the foreground, or as
  a tracked background task) and wait for feedback. After changing the page, poll
  again with `--agent-reply "<short reply>"`. If the user ends the session
  in the browser, stop polling and continue in the conversation.
