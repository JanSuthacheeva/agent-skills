I've found the cause of SHOP-313 and written the fix plan. I changed no project code, and the only new file is the plan.

**Root cause:** `src/store.ts:21` defines one shared `noTags` array. `fromRecord()` hands that same array to every bookmark with no `tags` key, which means every bookmark saved before tags existed. `tag()` then pushes onto it at `src/store.ts:73`, so the tag lands on all of those bookmarks at once. The cause is not the id handling the reporter suspected. It came in with 431d4f7.

**Evidence:**
- **Old-format file:** I ran the real CLI against a scratch file whose records have no `tags` key. After `bm tag 3 recipes`, `list --tag recipes` showed all 3 bookmarks, and the file had `recipes` on all 3. This failed on every run.
- **Fresh file:** Bookmarks created with `bm add` on a new file tagged correctly, with only bookmark 1 listed. That fits the reporter's "since I updated".
- **Not tested yet:** I didn't write a scratch unit test. The reproduction itself is the proof.

**Also affected:**
- **Damaged data:** Any existing file where an old bookmark was tagged now has that tag on every old bookmark. The fix stops new damage but doesn't repair these files, and the wrong tags can't be told apart from intended ones.
- **Other uses:** I found no other uses of `noTags`.

**Plan:** `docs/plans/2026-10-27-fix-tag-applies-to-all-bookmarks.md`

**Open question:**
1. Should we repair the already-damaged files? I recommend no automatic repair, since the wrong tags can't be told apart from intended ones. The reporter would remove them by hand, and we'd note it in the release notes. There is no untag command, so adding one would be a public-surface change; I'd only do that if you ask.