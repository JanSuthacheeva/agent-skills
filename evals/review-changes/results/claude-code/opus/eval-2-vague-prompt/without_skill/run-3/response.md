I reviewed `feature/bookmark-tags` against its plan and AGENTS.md. I reproduced each bug through the real CLI before fixing it. All 19 tests pass (10 before), and the same CLI commands now behave as the plan says.

**Bugs fixed:**
1. **Tagging twice added the tag twice.** `bm tag 1 work` run twice stored `["work","work"]`. The plan says a repeated tag should do nothing, so `BookmarkStore.tag` now skips tags the bookmark already has.
2. **`list --tag` didn't clean up the tag.** `bm list --tag Work` found nothing, and `list --tag "to do"` didn't report the invalid tag. The tag is now lowercased, trimmed and checked, the same way `tag` does it.
3. **`list --tag` with no value printed every bookmark.** It, and any unknown option, now prints `usage: bm list [--tag <tag>]` and exits 2.
4. **Wrong exit code for an unknown id.** It exited 2, but AGENTS.md and the plan say "not found" is exit 1. Fixed.
5. **Loose id parsing.** `Number()` read `bm tag "" work` as id 0, and read `0x1` as id 1. Ids must now be plain digits; anything else gets the usage error.

**Plan mismatch:** the plan names the method `listByTag`, but the code had `listTagged`. I renamed it to match the plan.

**Missing tests:** the plan's task list was all ticked, but tests for a repeated tag, an unknown id (store and CLI) and invalid characters didn't exist. I added those, plus tests for each bug above.

Three commits on top of the branch:
- `cc853fc` bm: cover empty and invalid tag characters
- `e71cd81` bm: make tagging idempotent and rename listTagged to listByTag
- `5d9ab09` bm: normalize list --tag, exit 1 for unknown id, strict id parsing

The plan doc links to `.lavish/bookmark-tags-implementation.html`, but that file isn't in the repo, so the link is broken. I left it alone.