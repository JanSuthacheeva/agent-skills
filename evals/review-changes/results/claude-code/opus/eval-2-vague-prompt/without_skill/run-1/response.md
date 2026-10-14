I reviewed `feature/bookmark-tags` against the plan (`docs/plans/2026-10-14-bookmark-tags.md`) and `AGENTS.md`. All six bugs below showed up when I ran the real CLI against a temp store file. They're fixed and committed in two commits. All 17 tests pass, and I re-ran the same CLI commands to confirm each one now behaves correctly.

**Bugs fixed**
1. **Duplicate tags:** running `bm tag 1 work` and then `bm tag 1 Work` saved `["work","work"]`. The plan says re-adding an existing tag should do nothing, and now it does.
2. **`list --tag` didn't normalize the tag:** `list --tag Work` found nothing because it didn't lowercase and trim the tag first. Now it finds the bookmark.
3. **`list --tag` accepted invalid tags:** `list --tag 'to do'` silently exited 0. It now prints `invalid tag: to do` and exits 2.
4. **`list --tag` with no value:** it quietly listed every bookmark. It now prints `usage: bm list [--tag <tag>]` and exits 2. Unknown options to `list` get the same error.
5. **Wrong exit code for an unknown id:** `tag 9 work` exited 2, but `AGENTS.md` and the plan say "not found" is exit 1. It now exits 1.
6. **Empty id:** `tag "" work` read the empty string as id 0 and printed `no bookmark 0`. It now gets the usage error.

**Matching the plan**
- I renamed `listTagged` to `listByTag`, the name the plan's interface uses. It now normalizes its argument, the same way `tag()` does.
- The plan's tasks were all ticked off, but some tests they called for were missing. I added tests for a duplicate tag and an unknown id (both in the store and the CLI), plus the CLI cases above.

**Commits**
- `773fc01 bm: dedupe tags and normalize the listByTag filter`
- `bab11a8 bm: validate list --tag and exit 1 for an unknown bookmark`

The `/commit` skill isn't installed in this session, so I committed with `git` directly and followed the repo's `bm: ...` message style.