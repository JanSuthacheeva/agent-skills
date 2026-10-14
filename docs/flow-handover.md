# Handover: making the skills report into `flow`, and auto mode

Written 2026-10-14. Piece 6 of 6 of the flows system; pieces 1-5 are built. Everything a
session in this repo needs is here; the full system record is
`~/projects/flow/docs/HANDOVER.md`.

## What `flow` is

`flow` (`~/projects/flow`, private on GitHub, installed at `~/.cargo/bin/flow`) tracks several
features worked on in parallel, one worker agent session per feature in its own git worktree.
It is an AXI: its main user is an agent, it answers in TOON with `help[]` next steps.

- `flow start "<request>"` (in a repo, inside tmux) makes a flow, a worktree
  `.flow/worktrees/<name>` on branch `flow/<name>`, runs the repo's `.flow/setup` hook, and
  opens a worker in a tmux window with `FLOW_ID` set. Claude workers start with
  `/ship-feature <request>`.
- Every flow is an append-only event log; `flow` alone folds it into state, phases with
  durations, tasks, blockers, decisions and a timeline. `flow status --json` is the contract
  for programs; `flow` / `flow status <name>` are the views for agents.
- `flow report <event>` appends one event. The flow comes from `$FLOW_ID` or `--flow <name|id>`.
  **Without a flow id it answers `skipped: no flow id` and exits 0**, so a skill can run it
  unconditionally and still work in a session that is not a flow.

Events a skill can report:

```
flow report phase <design|implement|review|merge-request>
flow report working
flow report delegated "<what a subagent does>"
flow report waiting "<the question for the user>"
flow report blocked "<why it cannot go on>"
flow report decision "<a choice made on the user's behalf>"
flow report tasks <done> <total>
flow report review --fixed <n> --open <n>
flow report merge-request <url>
flow report ended
```

Repeats are harmless: a repeated phase, question or block folds into the same view.

## What already reports without the skills (Claude Code only)

The `flows` mod in `~/projects/claude-code-mods/flows` is an adapter: in a Claude Code session
with `FLOW_ID` it turns engine events into reports. The skills must stay agent-agnostic and
must not depend on it, but in Claude Code it already covers:

| Claude Code event | Reported |
| --- | --- |
| `design-code`, `implement-plan`, `review-changes`, `write-merge-request` start (typed, via the Skill tool, or preloaded) | `phase` |
| a foreground subagent runs, then returns | `delegated`, then `working` |
| `AskUserQuestion`, or the end of Claude's turn (last line of the answer) | `waiting` |
| the next prompt, or the answer to a question | `working` |
| plan-progress reports progress or a block | `tasks`, `blocked` |
| `gh pr create` / `glab mr create` prints a URL | `merge-request` |
| every 30 s / session end | heartbeat / `ended` |

## What only the skills can report (piece 6, part 1)

These are invisible to any adapter, and other agents (Codex, ...) have no adapter at all.
Add one short, agent-agnostic instruction per skill, in the style implement-plan already uses
for its progress tool: "If a `flow` command is available, report ...; otherwise go on."

1. **Waiting on a browser review.** design-code waits in `npx lavish-axi poll` for the user's
   choice. The turn is still running, so the board shows the worker *working* while it really
   waits for the user. Before polling: `flow report waiting "Pick an approach on the page"`
   (and "Review the implementation page"); after the answer arrives: `flow report working`.
   Seen in the end-to-end run of 2026-10-14.
2. **Real questions instead of last lines.** At every stop, report the question itself:
   `flow report waiting "<question>"`. Today the board shows the last line of Claude's answer,
   which can be any sentence (seen: "The page uses the Tailwind/DaisyUI nord fallback...").
3. **Decisions.** Every choice made for the user - especially in auto mode - as
   `flow report decision "<choice and why, one line>"`. Nothing else can see them; the board's
   timeline and the MR's review guide depend on them.
4. **Review counts.** review-changes at its end: `flow report review --fixed <n> --open <n>`.
5. **Blocked.** implement-plan's expensive deviation, a red base, open review items:
   `flow report blocked "<one line>"` (ship-feature's stops).
6. **Phases for other agents.** Each skill at its start: `flow report phase <its phase>`. In
   Claude Code this duplicates the adapter, which is harmless.
7. **ship-feature's coordinating line** (`skills/ship-feature/SKILL.md`, "Stops": "If your
   environment lets you report to a coordinating session, send the stop there") becomes:
   report the stop with `flow report waiting|blocked`, then ask the user directly as today.

Keep every line conditional ("if a `flow` command is available") so the skills work
unchanged everywhere else, and keep tool names out of the skill text beyond `flow` itself.

## Auto mode (piece 6, part 2)

Decided 2026-10-14 (system approaches, round 2): small features run to the MR without stops;
the one review is at the end.

- ship-feature takes a mode: `guided` (today's stops) or `auto`. `flow start --mode auto`
  already records it on the flow; the skill needs to learn it from its arguments
  (e.g. `/ship-feature --auto <request>`).
- In auto, design-code picks its own recommended approach and writes the plan without the
  lavish review pages, recording every choice under a `## Decisions` section in the plan and
  with `flow report decision`.
- implement-plan and review-changes run as today.
- write-merge-request leads with the decisions, so the single review covers code and choices.
- **Guardrail:** anything expensive to reverse - stored data and its format, the public
  surface, user-visible behaviour (design-code's "Ask" category, implement-plan's "stop and
  ask") - stops the flow even in auto. Cheap decisions never do.
- Costs: a non-interactive path in design-code and ship-feature, and evals proving auto
  picks sensibly and really stops on the expensive cases (scenarios to add next to
  `evals/ship-feature/`).

## Gotchas seen while building pieces 1-5

- A skill typed as `/name` raises no skill-start event in Claude Code; adapters must read the
  prompt. Not a skill concern, but explains why the skills' own phase line is the robust one.
- Worktrees: each worker has its own folder; Docker projects run one stack per worktree via
  the repo's `.flow/setup` hook and `FLOW_SLOT` (ports), so tests run inside the worktree's
  own containers (`docker compose exec ...` from the worktree).
- `flow report` without a flow id exits 0 with `skipped`; never treat that as an error.

## Where things are

- `flow`: `~/projects/flow` - `README.md` (commands, output, hooks, Docker example),
  `docs/HANDOVER.md` (the whole system, decisions, verified facts), `docs/design/` (review
  pages of every piece).
- Board and adapter mod: `~/projects/claude-code-mods/flows` (experimental, published in the
  claude-code-mods marketplace; workers load it once installed with
  `/plugin install flows@claude-code-mods`).
- ship-feature is linked into `~/.claude/skills/ship-feature` (2026-10-14), like the other skills.
