All five tasks are done and committed, and the plan's checkboxes are ticked. The full suite passes (21 tests, 4 of them from before). The repo has no lint or type-check script, so there was nothing to run there.

**Commits**
1. `7d61ab4` adds `normalizeTag` and `InvalidTagError`.
2. `763f990` adds `tags` to `Bookmark`, creates new bookmarks with `tags: []`, and reads old files without `tags` as `[]`.
3. `958ac64` adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`.
4. `54b6133` adds `bm tag <id> <tag>` and `bm list --tag <tag>`.
5. `70cc280` ticks the end-to-end task in the plan.

**End-to-end check** against a temp store file with `npm run bm`:
- `tag 2 " Runtime"` printed `tagged 2 runtime` and exited 0.
- `list --tag runtime` printed only `2  Deno  https://deno.com`.
- Tagging the same tag again was a no-op, and the file shows a single `runtime` tag.
- Unknown id printed `no bookmark 9` and exited 1.
- Invalid tag printed `invalid tag: a b` and exited 2.
- Non-numeric id printed the usage line and exited 2.

**Deviations**
- I added `usage: bm list [--tag <tag>]` with exit 2 for an unknown `list` option or `--tag` with no value. The plan didn't cover that case, so I added it to the plan's error list.
- The `commit` skill doesn't exist here, so I committed with plain git.
- In task 3 I wrote the tests and the implementation before running the tests red. They passed afterwards, but the failing-first check was skipped for that task.

Nothing is blocked or open.

**How it works**
- `src/main.ts` calls `run(argv, store, out)` in `src/cli.ts`.
- For `tag` and `list --tag`, `run` calls `normalizeTag` in `src/tags.ts`, which trims, lowercases and validates against `a-z`, `0-9` and `-`.
- `run` then calls `BookmarkStore::tag` or `listByTag` in `src/store.ts`.
- `tag` loads the bookmarks, appends the tag if it's new and saves. `listByTag` filters the loaded bookmarks.
- `withTagErrors` in `cli.ts` maps `InvalidTagError` to exit 2 and `BookmarkNotFoundError` to exit 1.
- The store normalizes the tag again itself, so it stays correct for any caller.
- `load()` fills in `tags: []` for files written before this change, so no migration is needed.