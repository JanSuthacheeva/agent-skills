# agent-skills

Agent skills I use day to day, each shipped with evals that measure whether
the skill actually changes the agent's behavior.

## Skills

| Skill | What it does | Eval results |
|---|---|---|
| [commit](commit/SKILL.md) | Writes and creates git commits in Scoped Commits format (`scope: description`): reuses scopes from the log, adds a `Refs:` trailer from the branch's ticket id, keeps git's default revert and merge messages, and never pushes. | [Claude Code, Opus 5.5](commit/evals/results/claude-code/README.md): 55/55 trials pass with the skill, 40/55 without |

Skills are tested in Claude Code with Claude Opus 5.5. Other harnesses that
support the Agent Skills format should work but are untested.

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
