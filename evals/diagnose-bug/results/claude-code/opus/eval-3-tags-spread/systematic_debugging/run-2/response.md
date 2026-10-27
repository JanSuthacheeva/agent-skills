I fixed SHOP-313. The reporter's guess was wrong: the `tag` command does use the id. The bug only hits bookmark files written before the update, and it does more than show wrong results — the wrong tags get saved into the file.

**Cause:** in `src/store.ts`, when a bookmark has no `tags` field (every bookmark saved by the old version), loading gave it a default empty list. All of those bookmarks were handed the *same* list rather than one each. So `bm tag 3 recipes` correctly found bookmark 3 and added `recipes` to its list, but that list was shared with every other old bookmark. Saving then wrote `"tags": ["recipes"]` onto all of them. Bookmarks added after the update each get their own list, which is why the existing tests and a new file worked fine.

**What I did:**
- I reproduced it with an old-style file: tagging bookmark 3 tagged all three bookmarks and saved that to disk. On a file created by the new version, it worked correctly.
- I added a test to `test/store.tags.test.ts` that writes an old-style file, tags one bookmark, and checks the others stay untagged. It failed before the fix. The existing test "bookmarks saved before tags load with no tags" never actually covered this, because `add` always writes `tags: []`.
- **Fix:** each loaded bookmark now gets its own empty list (`record.tags ?? []`), and I removed the shared one. All 16 tests pass, and my reproduction now lists only bookmark 3.

**Your decision:** the fix stops this happening again, but it can't repair files that are already wrong. The reporter's file now has `recipes` on all 40 bookmarks, and nothing in the file shows which one they actually tagged. They'll need to remove the tag by hand or restore a backup, and there's no `untag` command yet. That's probably worth saying in the ticket reply.

I haven't committed anything or updated the ticket.