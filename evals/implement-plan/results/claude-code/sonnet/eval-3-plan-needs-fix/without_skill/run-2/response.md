I implemented the plan: `bm tag <id> <tag>` and `bm list --tag <tag>` now work. All 17 tests pass. I also ran `add`, `tag` and `list --tag` against a temp store file. Tagging an unknown id exits 1 and prints `no bookmark 9`. An invalid tag exits 2 and prints `invalid tag: a b`.

- **Plan deviation:** the plan declared `InvalidTagError` as `constructor(readonly raw: string)`. That's a parameter property, which AGENTS.md forbids because Node can't strip it. I declared `raw` as an explicit field instead.
- **Normalizing in the CLI:** `run` calls `normalizeTag` before the store call, as the call chain says. That way `tagged <id> <tag>` always prints the normalized tag, even when the bookmark already had it.
- **Commit:** everything is in one commit, `cc2b812 bm: add bookmark tags`, made with plain `git commit` because the `/commit` skill isn't available here. It is one commit rather than one per task. I also ticked off the tasks in the plan file.

The new code is in `src/tags.ts`, `src/store.ts` and `src/cli.ts`, with tests in `test/`.