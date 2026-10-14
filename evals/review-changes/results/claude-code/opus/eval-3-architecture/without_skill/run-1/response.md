I reviewed `feature/bookmark-tags` against `main` and the plan in `docs/plans/2026-10-14-bookmark-tags.md`, and fixed four problems. I reproduced each one through the real CLI first. All 17 tests pass (10 before), and a full run of add, tag, a duplicate tag, `list --tag`, and the error cases against a temp store file gives the right output and exit codes.

**Fixes (one commit each):**

1. **A broken store file got silently wiped** (`fa24589`). `BookmarkStore::load` treated an unreadable file as an empty list, so the next `add` overwrote all the user's bookmarks. I reproduced this: the old bookmark was gone. Loading now fails loudly again, the way it did before this branch, and there's a test for it.

2. **The CLI did tagging itself instead of using the store** (`080cf23`). `bm tag` read the bookmarks, changed them and saved the file directly, copying `BookmarkStore::tag` and breaking the rule in AGENTS.md that only the store touches the file. That also meant `store.tag` was never called. Separately, `store.tag` printed a warning with `console.warn`, but printing is the CLI's job, and the plan says a duplicate tag should do nothing quietly. The CLI now calls `store.tag`, and the store no longer prints anything.

3. **Tests the plan lists as done were missing** (also in `080cf23`). The tasks were checked off, but there were no tests for a duplicate tag or an unknown id, in either the store or the CLI. I added them.

4. **Bad arguments got through** (`d075b72`):
   - `bm list --tag` with no tag listed every bookmark. It now prints a usage message and exits with 2.
   - `bm tag "" work` printed `no bookmark 0` because an empty id was read as 0, and `1.5` wasn't rejected cleanly either. Both now give the usage message and exit with 2.
   - `list --tag` now normalizes the tag in the CLI, as the plan describes, and an invalid tag exits with 2. I also changed `listByTag` to normalize the tag once rather than once per bookmark.

**Two things to know:**
- A broken store file now crashes with a raw error and stack trace, which is how `main` behaves too. A friendlier version would need its own error type and an exit code; AGENTS.md only defines 1 (not found) and 2 (bad input), so I left that choice to you.
- The `/commit` skill isn't available in this session, so I committed with plain `git commit`.