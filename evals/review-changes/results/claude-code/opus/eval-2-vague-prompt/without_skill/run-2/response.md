I reviewed `feature/bookmark-tags` against its plan (`docs/plans/2026-10-14-bookmark-tags.md`) and `AGENTS.md`, and fixed seven problems in one commit, `45fa925`. All 17 tests pass, and I ran each bug through the real CLI (`npm run bm`) before and after the fix.

**Bugs I reproduced and fixed:**
1. **Duplicate tags were saved:** tagging `1 work` and then `1 Work` stored `"work"` twice. The plan says a repeated tag should do nothing, and now it does (`src/store.ts`).
2. **`list --tag` didn't clean up the tag:** `list --tag Work` returned nothing, and `list --tag "to do"` succeeded silently. It now lowercases and trims the tag first, and rejects invalid ones with `invalid tag: ...`.
3. **Wrong exit code for an unknown id:** it exited with 2, but `AGENTS.md` and the plan say 1 for "not found".
4. **`list --tag` with no tag after it listed everything:** it now prints `usage: bm list [--tag <tag>]` and exits 2.
5. **An empty id was read as 0:** `tag "" work` printed "no bookmark 0". Ids must now be plain digits, otherwise you get the usage message.

**Mismatches with the plan:**

6. **Method name:** it was `listTagged`; I renamed it to `listByTag`, as the plan specifies.
7. **Missing tests:** none existed for duplicate tags or unknown ids. I added those, plus tests for the `list --tag` edge cases, bad ids and invalid characters.

**Left for you:**
- **Stricter `list`:** `list` followed by any argument other than `--tag <tag>` now shows the usage message. Before, extra arguments were silently ignored.
- **Missing review page:** the plan links to `.lavish/bookmark-tags-implementation.html`, which doesn't exist.
- **Task checkboxes:** every task in the plan was ticked even though the work above was missing. They're accurate now that it's fixed.
- **Commit method:** I committed with plain git because the `/commit` skill isn't available in this session.