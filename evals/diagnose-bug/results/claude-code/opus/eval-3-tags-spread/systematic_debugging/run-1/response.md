I've fixed SHOP-313. The reporter guessed the tag command ignores the id, but it doesn't: it finds the right bookmark.

**Cause:** in `src/store.ts`, bookmarks saved before tagging existed have no `tags` field. When loaded, they were all given the same shared empty array (`noTags`). `bm tag 3 recipes` added the tag to that one shared array, and saving wrote it out under every old bookmark. That's why it started after updating, and why the existing tests didn't catch it: they only use bookmarks created with the new version, which each get their own array.

**Reproduced:** with a bookmarks file in the old format (3 bookmarks, no `tags`), `bm tag 3 recipes` followed by `bm list --tag recipes` listed all three, and the file showed `"tags": ["recipes"]` on every one.

**Fix:**
- `src/store.ts`: each old bookmark now gets its own empty array (`record.tags ?? []`), and the shared `noTags` constant is removed.
- `test/store.tags.test.ts`: added a test that writes an old-format file, tags bookmark 3, and checks the tags come out as `[[], [], ['recipes']]`. It failed before the fix and passes now; the full suite passes (16 tests).

**This won't repair the reporter's file.** Their 40 bookmarks now really do all have `recipes` saved on them, and there's no way to tell which was tagged on purpose. Someone will need to tell them to remove the wrong tags by hand, or restore the file from a backup. Old-format bookmarks that haven't been tagged yet are not affected.

I haven't committed or updated the ticket.