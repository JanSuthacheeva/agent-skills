I reviewed `feature/bookmark-tags` against `main`, the plan and `AGENTS.md`, and fixed everything I found. I reproduced each bug with the real CLI against a temporary store file before fixing it. All 15 tests pass and the fixes are in two commits.

**Bugs:**
1. **A corrupt store file could wipe all bookmarks** (`src/store.ts`). `load()` caught JSON parse errors and returned `[]`, so the next `add` or `tag` overwrote the file. I confirmed this: I damaged a file, ran `add`, and only the new bookmark was left. `load()` now throws again, as it did on `main`, and the file is left alone.
2. **`bm list --tag` with no tag listed everything and exited 0** (`src/cli.ts`). It now prints `usage: bm list [--tag <tag>]` and exits 2. Any other unknown option to `list` gets the same usage error.

**Architecture:**
3. **The `tag` command bypassed the store.** It had its own copy of the lookup, de-duplication and save logic, which goes against "the CLI never touches the file directly" in `AGENTS.md` and the plan's call chain. `BookmarkStore::tag` existed but nothing called it. The command now normalizes the tag and calls `store.tag`.
4. **`BookmarkStore::tag` printed a warning when a bookmark already had the tag.** The plan says that case is a silent no-op, and the store shouldn't print anyway. I removed the warning. `tag` now also checks the tag is valid before reading the file.
5. **Minor:** `listByTag` re-normalized the tag once per bookmark inside the filter. It now does it once.

**Tests the plan promised but were missing:**
- At the store level: tagging with a tag the bookmark already has, tagging an unknown id, and a corrupt file throwing.
- At the CLI level: an unknown id gives `no bookmark 7` with exit 1, and `list --tag` with no tag gives exit 2.

Separately, the plan links to a review page at `.lavish/bookmark-tags-implementation.html`, which isn't in the repo. It's harmless, but the link is broken.

The `/commit` skill your instructions ask for isn't available in this session, so I committed with plain `git commit`.