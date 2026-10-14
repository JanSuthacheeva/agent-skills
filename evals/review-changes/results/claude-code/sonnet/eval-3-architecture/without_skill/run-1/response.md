I reviewed `feature/bookmark-tags`, fixed four problems and committed the fixes as `22e728e`. All 12 tests pass, but I didn't run the CLI against a temp store file, so the plan's last task is still checked on the strength of the original author's say-so.

- **CLI bypassed the store:** `bm tag` in `src/cli.ts` loaded the file, mutated the bookmarks and saved them itself. That breaks the rule in `AGENTS.md` that the CLI never touches the file, and it ignored `BookmarkStore::tag`. It now calls `store.tag`.
- **Corrupt store file was silently wiped:** `load()` in `src/store.ts` returned `[]` on a JSON parse error, so the next `add` or `tag` would overwrite the user's data with an almost empty file. I removed the try/catch, so a corrupt file now raises an error.
- **Duplicate tag logged a warning:** `store.tag` called `console.warn`, but the plan says tagging a bookmark with a tag it already has is a silent no-op. It's now a silent no-op, and the store doesn't print.
- **`bm list --tag` with no tag listed everything:** it now prints `usage: bm list [--tag <tag>]` and exits 2. An unknown flag gets the same error. Tag normalizing also moved out of the filter loop in `listByTag`.

I added CLI tests for an unknown id (exit 1) and for `list --tag` without a tag (exit 2). The plan required the unknown-id test and it was missing.

The `/commit` skill isn't available in this setup, so I used plain `git commit` for the fixes.