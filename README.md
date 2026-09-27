# agent-skills

Agent skills I use day to day.

Trying to keep the evals up to date and run them for different harnesses and models. For now, only Claude Code.

## Skills

| Skill | What it does | Eval results |
|---|---|---|
| [commit](commit/SKILL.md) | Writes + creates git commits in Scoped Commits format (`scope: description`): reuses scopes from log, adds a `Refs:` trailer from branch's ticket id (if available), keeps git's default revert and merge messages. Never pushes. | [Claude Code, Opus 5.5](commit/evals/results/claude-code/README.md): 55/55 trials pass with the skill, 40/55 without |

## Install

Clone the repo and link the skill into your skills directory, so updates
arrive with `git pull`:

```sh
git clone https://github.com/JanSuthacheeva/agent-skills.git
ln -s "$PWD/agent-skills/commit" ~/.claude/skills/commit
```

## Evals

Each skill has an `evals/` directory with scenario definitions, fixture
setup, a trial runner and a grader. Results are published per harness under
`evals/results/`. The eval method is based on the evaluation workflow of
Anthropic's [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
skill, adapted for repeated headless trials against git fixtures.

## License

[MIT](LICENSE)
