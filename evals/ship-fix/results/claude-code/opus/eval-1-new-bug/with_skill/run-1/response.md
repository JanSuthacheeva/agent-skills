I've diagnosed SHOP-311 and written a fix plan. I need your approval before I build anything.

**Root cause:** `list --tag` isn't broken. Adding a bookmark deletes every bookmark's tags from the file. `toRecord()` at `src/store.ts:26` doesn't write `tags`, so `add()` → `save()` rewrites the whole file without them. This came in with 6d668ea: `tag()` worked around the gap at `src/store.ts:74`, but `save()` never got the fix.

**Evidence:** I followed the reporter's steps through the real CLI with `BM_FILE` pointed at a scratch file. Before the second `add`, bookmark 1 is stored with `"tags": ["work"]` and `list --tag work` shows it. After the `add`, no record in the file has a `tags` key, and `list --tag work` prints nothing (exit 0). It fails every run. All 15 existing tests pass, so none of them covers this.

**Also affected:** Any user who added a bookmark after tagging has already lost those tags. The file keeps no history, so the fix can't bring them back.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`
1. Add a regression test, then make `toRecord()` write `tags`.
2. Have `tag()` use `save()` instead of its own workaround.
3. Rerun the reproduction end to end.

**Open question:**
1. Should we try to repair tags that are already lost? **I recommend no:** they can't be recovered. The merge request will say that affected users need to re-tag their bookmarks.

If you approve, I'll commit the plan on a branch named `SHOP-311`. After that, please run `/compact` and say "continue fixing" to start the build.