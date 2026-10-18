# agent-skills

Agent skills I use day to day.

Trying to keep the evals up to date and run them for different harnesses and models. For now, only Claude Code.

## Skills

| Skill | What it does | Eval results |
|---|---|---|
| [design-code](skills/design-code/SKILL.md) | Plans the code design of a change before any code exists: investigates the codebase, lets you pick between structurally different approaches, then lays out units, typed signatures, data and call chains (no function bodies) as HTML review pages (claude.ai Artifacts in Claude Code, [lavish](https://www.npmjs.com/package/lavish-axi) elsewhere) plus a Markdown plan. | [Claude Code, Opus 5.5, medium effort](evals/design-code/results/claude-code/README.md): judge score and assertions on par with `feature-dev` (34.7 vs 33.6 of 40, 77 vs 76 of 81) at about the same cost (2.90 vs 2.79 USD per run); most reviewable plans of four planning methods |
| [implement-plan](skills/implement-plan/SKILL.md) | Builds an approved plan task by task: tests first, one commit per task, the plan's names and signatures. Makes cheap deviations and writes them back into the plan, stops on expensive ones (stored data, public surface, user-visible behavior), ends with an end-to-end check and how the result works. | [Claude Code, Opus 5.5 and Sonnet 5.5, medium effort](evals/implement-plan/results/claude-code/README.md): Opus 9/9 trials pass with and without the skill; Sonnet 9/9 with, 1/9 without (changed a public file format, merged tasks, left the plan stale) |
| [review-changes](skills/review-changes/SKILL.md) | Reviews a branch in a context that has not seen the implementation, proves findings, fixes the cheap ones and re-reviews them, and reports what was fixed, what is open and where to look. | [Claude Code, Opus 5.5 and Sonnet 5.5, medium effort](evals/review-changes/results/claude-code/README.md): every condition repairs every planted defect; blind-judged owner report 36.0 of 40 vs 30.0 for a plain review and 22.0 for `/code-review` (Opus), 35.7 vs 29.3 and 23.1 (Sonnet), ranked first in 18 of 18 |
| [write-merge-request](skills/write-merge-request/SKILL.md) | Writes MR/PR title and description around the why: decisions a reviewer would question, deploy steps such as new env variables, a short reading order for larger diffs; follows the repo's template. Pushes and creates the MR only when asked. | [Claude Code, Opus 5.5 and Sonnet 5.5, medium effort](evals/write-merge-request/results/claude-code/README.md): 18/18 trials pass with the skill, 6/18 without (Opus); 17/18 vs 5/18 (Sonnet) |
| [ship-feature](skills/ship-feature/SKILL.md) | Runs the four skills above as one flow from request or ticket to merge request: builds in your conversation after a `/compact` so you can follow it, reviews in a fresh agent given only the plan and the branch, stops only for your decisions (approach, plan, blocked build, open review items, push), and resumes from what the repository shows. | [Claude Code, Opus 5.5 and Sonnet 5.5, medium effort](evals/ship-feature/results/claude-code/README.md): with the skill, every trial builds in the conversation where tasks are open, reviews in a fresh agent and reports its stop to saaio (then called `flow`); 4/4 trials pass all checks (Opus), 2/4 (Sonnet, each missed one report), 0/4 without; [without saaio](evals/ship-feature/results/claude-code-without-flow/README.md) 4/4 vs 2/4 (Opus), 4/4 vs 0/4 (Sonnet); measured while the skills still reported to saaio, which now follows them through hooks |
| [commit](skills/commit/SKILL.md) | Writes + creates git commits in Scoped Commits format (`scope: description`): reuses scopes from log, adds a `Refs:` trailer from branch's ticket id (if available), keeps git's default revert and merge messages. Never pushes. | [Claude Code, Opus 5.5 and Sonnet 5.5, medium effort](evals/commit/results/claude-code/README.md): 55/55 trials pass with the skill, 45/55 without (Opus); 54/55 vs 27/55 (Sonnet) |
| [setup-saaio](skills/setup-saaio/SKILL.md) | Prepares a repo so [saaio](https://github.com/JanSuthacheeva/saaio) can run several workers side by side, each in its own worktree: makes compose ports configurable (today's ports kept as defaults), writes `.saaio/setup` and `.saaio/teardown` that give each worktree its own ports, `.env` and containers from `SAAIO_SLOT` (Docker Compose, Laravel Sail, plain dev servers), and proves them in a scratch worktree. | [Claude Code, Opus 5.5, medium effort](evals/setup-saaio/results/claude-code/README.md): 44/45 checks with the skill, 38/50 without; every skill trial proves the scripts in a scratch worktree, no baseline trial does |

Together they form a flow from idea to merge request:
`design-code` -> `implement-plan` -> `review-changes` -> `write-merge-request`,
with `commit` used throughout. `ship-feature` runs the flow for you; each
skill also works on its own. [saaio](https://github.com/JanSuthacheeva/saaio)
follows them through Claude Code's own hooks, so the skills know nothing
about it; `setup-saaio` gets a repo ready for saaio's parallel workers.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), for Claude Code,
Codex and other supported agents:

```sh
npx skills add JanSuthacheeva/agent-skills --skill commit
npx skills add JanSuthacheeva/agent-skills --skill design-code
npx skills add JanSuthacheeva/agent-skills --skill implement-plan
npx skills add JanSuthacheeva/agent-skills --skill review-changes
npx skills add JanSuthacheeva/agent-skills --skill setup-saaio
npx skills add JanSuthacheeva/agent-skills --skill ship-feature
npx skills add JanSuthacheeva/agent-skills --skill write-merge-request
```

`design-code` publishes its review pages as claude.ai Artifacts when it runs in
Claude Code, and otherwise opens them with the
[lavish](https://www.npmjs.com/package/lavish-axi) skill, which it then expects
to be installed as well.

Or clone the repo and link the skill into your skills directory, so updates
arrive with `git pull`:

```sh
git clone https://github.com/JanSuthacheeva/agent-skills.git
ln -s "$PWD/agent-skills/skills/commit" ~/.claude/skills/commit
```

## Evals

Each skill has an eval suite under `evals/<skill>/` with scenario definitions,
fixtures, a trial runner and a grader. Results are published per harness
under `evals/<skill>/results/`. The eval method is based on the evaluation
workflow of Anthropic's
[skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
skill, adapted for repeated headless trials against git fixtures. The
`design-code` evals add multi-turn runs against a simulated user and blind
ranking against other planning methods.

## License

[MIT](LICENSE)
