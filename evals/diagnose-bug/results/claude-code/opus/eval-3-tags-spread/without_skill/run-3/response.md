I fixed SHOP-313. The reporter guessed that `tag` ignores the id, but it doesn't. The real problem was how old bookmarks get their tag list when the file is loaded.

**Cause:** The bug came in with the tagging commit (4706200). Bookmarks saved before that commit have no `tags` field in the file. When loading, `fromRecord` in `src/store.ts` gave every one of them the same shared `noTags` array instead of a new empty list. When `tag()` adds a tag to one of those bookmarks, it changes that shared array, so every pre-update bookmark gets the tag. The save then writes the tag to all of them. That's why the reporter saw all 40 bookmarks tagged.

I reproduced it with a pre-update file: after `bm tag 3 recipes`, `bm list --tag recipes` listed bookmarks 1, 2 and 3.

**Fix:** Each loaded bookmark now gets its own empty list (`record.tags ?? []`), and I removed the shared `noTags` constant.

**Test:** The existing tests missed this because they only use bookmarks created with `add()`, which already get their own empty list. I added a regression test to `test/store.tags.test.ts` that writes a pre-update file and tags a single bookmark. It fails without the fix and passes with it, and the full suite passes (16 tests).

The reporter's file still has the wrong tags, because the bug saved them to disk. The fix can't tell which bookmark was meant to have the tag, so they'll need to remove it by hand. There's no untag command yet, so for now that means editing the JSON file. I haven't committed anything or updated the ticket.