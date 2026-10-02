# agent-skills

Agent skills I use day to day.

Trying to keep the evals up to date and run them for different harnesses and models. For now, only Claude Code.

## Skills

| Skill | What it does | Eval results |
|---|---|---|
| [code-design](skills/code-design/SKILL.md) | Plans the code design of a change before any code exists: investigates the codebase, lets you pick between structurally different approaches, then lays out units, typed signatures, data and call chains (no function bodies) as [lavish](https://www.npmjs.com/package/lavish-axi) review pages plus a Markdown plan. | [Claude Code, Opus 5.5 (medium effort)](evals/code-design/results/claude-code/README.md): judge score and assertions on par with `feature-dev` (34.7 vs 34.0 of 40, 77 vs 76 of 81) at about 1.1 times its cost; most reviewable plans of four planning methods |
| [commit](skills/commit/SKILL.md) | Writes + creates git commits in Scoped Commits format (`scope: description`): reuses scopes from log, adds a `Refs:` trailer from branch's ticket id (if available), keeps git's default revert and merge messages. Never pushes. | [Claude Code, Opus 5.5](evals/commit/results/claude-code/README.md): 55/55 trials pass with the skill, 40/55 without |

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), for Claude Code,
Codex and other supported agents:

```sh
npx skills add JanSuthacheeva/agent-skills --skill commit
npx skills add JanSuthacheeva/agent-skills --skill code-design
```

`code-design` renders its review pages with the
[lavish](https://www.npmjs.com/package/lavish-axi) skill, which it expects to
be installed as well.

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
`code-design` evals add multi-turn runs against a simulated user and blind
ranking against other planning methods.

## License

[MIT](LICENSE)
