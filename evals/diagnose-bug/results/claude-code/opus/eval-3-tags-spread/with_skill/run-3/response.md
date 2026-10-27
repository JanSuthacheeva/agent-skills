I reproduced SHOP-313 and found the cause. The plan to fix it is at `docs/plans/2026-10-27-fix-tag-spreads-to-all-bookmarks.md`; no code was changed.

**Root cause:** The tag command does use the id, so the reporter's guess is wrong. When `fromRecord()` loads a bookmark that has no `tags` field, it gives it the module-level `noTags` array instead of a new one (`src/store.ts:38`, array defined at `src/store.ts:18`). Every bookmark saved before the tags update therefore shares one array. When `tag()` adds a tag to it (`src/store.ts:75`), all of those bookmarks get the tag, and `save()` writes it to the file for each of them. This came in with f026bce, the commit that added tagging.

**Evidence:**
- **Old file:** I created a 3-bookmark file with the version before tags (c34a1ee). After `bm tag 3 recipes`, `bm list --tag recipes` listed bookmarks 1, 2 and 3, and the file had `"tags": ["recipes"]` on all three.
- **New file:** the same steps on a file created by the current version listed only bookmark 3. So the bug only hits bookmarks saved before the update, which is why it showed up "since I updated."
- **Direct check:** I loaded two old records and compared their tag arrays: `b[0].tags === b[1].tags` is `true`.
- **Why the tests miss it:** the existing test "bookmarks saved before tags load with no tags" creates its bookmark with `add()`, which already writes `tags: []`. It never loads a record without tags.

**What else is affected:** No other code has the same mistake. The bigger problem is files already damaged: every file with old bookmarks that has been tagged since the update now has those tags saved on all of its old bookmarks. The fix stops new damage but doesn't clean that up, and the file doesn't record which bookmark was really tagged.

**Fix in the plan:** change `fromRecord()` to give each bookmark its own new array (`record.tags ?? []`) and remove `noTags`. The first task is a regression test with two old-style records, which fails today with `['A', 'B']` instead of `['B']`.

**Open question:**
1. Should we repair files that are already damaged? I recommend no automatic repair, because there's no way to tell real tags from spread ones. Instead, tell affected users (at least the reporter) to remove the extra tags by hand. A `bm untag` command would help, but it's a new command, so it should be its own ticket.

The only change in the working tree is the new plan; I removed the scratch files and the temporary worktree.