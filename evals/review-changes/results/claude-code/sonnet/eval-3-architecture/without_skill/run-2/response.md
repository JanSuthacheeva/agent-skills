I reviewed the branch, fixed what I found, and committed it as b52cc47. All 16 tests pass.

**Fixed**
- **Bypassed the store:** the CLI's `tag` command loaded and saved the file itself and never called `BookmarkStore.tag`. That broke the "CLI never touches the file" rule in AGENTS.md and the plan. It now calls `store.tag`.
- **Data loss on a corrupt file:** `load()` caught JSON parse errors and returned `[]`, so the next `add` or `tag` would have overwritten a corrupt store with an almost-empty one. It now throws instead.
- **Warning on duplicate tags:** `store.tag` printed a `console.warn` when the tag was already there. The plan says tagging twice is a silent no-op, so I removed the warning.
- **`list --tag` with no value:** it silently listed everything. It now prints `usage: bm list [--tag <tag>]` and exits 2. It also normalizes the tag in the CLI, as the plan's call chain says.
- **Repeated normalizing:** `listByTag` re-normalized the tag for every bookmark. It now does it once.

**Tests added**
The plan promised tests for a duplicate tag and an unknown id, and neither existed. I added:
- tagging the same tag twice, at the store level
- an unknown id, at the store and CLI levels
- a non-numeric id
- `list --tag` with no tag
- a corrupt store file

The `/commit` skill isn't installed here, so I committed directly with `git`.