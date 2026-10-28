The push was denied, so I haven't pushed the branch or created the MR. Everything up to that point is done.

**Cause:** `toRecord` in `src/store.ts` didn't write `tags`. `add()` saves the whole list, so adding a bookmark wiped the tags on every existing one. `list --tag` worked fine, but there were no tags left to find.

**Fix:** `toRecord` now includes tags, and `tag()` calls `save()` instead of its own record mapping. I added a regression test that adds, tags, then adds again. It failed before the fix, and all 16 tests pass now.

**Committed:** branch `fix/SHOP-311-tags-lost-on-add`, one commit (`store: keep tags when saving bookmarks`, with a `Refs: SHOP-311` trailer).

**Pending:** the push and `glab mr create` still need to run. If you approve the push, I'll run both. Here is the MR text:

- **Title:** SHOP-311 Tags disappear
- **Description:** Adding a bookmark wiped the tags of all existing ones, because `toRecord` did not write `tags` and `add()` saves the whole list. So `bm list --tag work` came back empty after any `bm add`. `toRecord` now includes tags, and `tag()` uses `save()` instead of its own record mapping. `list --tag` itself was fine; the data was lost on write. Refs: SHOP-311

No open MR exists for this branch.

Tags already lost from existing bookmark files can't be recovered. Those bookmarks need re-tagging.