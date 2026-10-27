**Root cause:** `src/store.ts:20` defines one shared `noTags` array, and `fromRecord` (`src/store.ts:33`) hands it to every bookmark whose record has no `tags` key. `BookmarkStore.tag` (`src/store.ts:76`) pushes onto that array, so the tag lands on every such bookmark. It came in with 431d4f7. The tag command does use the id correctly, so the reporter's guess was wrong.

**Evidence:**
- **Reproduction:** I wrote a legacy-format file (three records with no `tags`) and ran `bm tag 3 recipes`. `list --tag recipes` then showed all three bookmarks, and the file contained `recipes` three times. It fails on every run.
- **Control:** bookmarks created with `bm add` on the current version, then `bm tag 2 x`, tagged only bookmark 2.
- **Not tested:** I didn't run a separate experiment that swaps in a per-record array. The cause rests on the reproduction, the control, and reading the code.

**Also affected:**
- Any real `.bookmarks.json` where `bm tag` has been run on a record without `tags` now has that tag on every such record. The fix stops new damage but doesn't repair those files.
- I found no other code with the same mistake.

**Plan:** `docs/plans/2026-10-27-fix-tag-applies-to-all-bookmarks.md`. The working tree has only the new `docs/` folder. No code is changed and nothing is committed.

**Open question:**
1. Should the fix repair files that are already damaged? I recommend no, because the correct tags can't be recovered. Tell the reporter to remove the wrong tag by hand, or add a `bm untag` command as a separate ticket.