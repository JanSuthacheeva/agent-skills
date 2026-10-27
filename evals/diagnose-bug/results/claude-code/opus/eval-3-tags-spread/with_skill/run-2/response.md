I found the cause of SHOP-313 and wrote a fix plan. No code is changed and nothing is committed.

**Root cause:** The tag command does use the id, so the reporter's guess is wrong. When a saved bookmark has no `tags` field, `fromRecord()` at `src/store.ts:39` gives it the module-level `noTags` array. Every bookmark saved before the update therefore shares that one array, so when `tag()` (`src/store.ts:76`) adds a tag to one of them, all of them get it, and `save()` writes it to every record. This came in with 058b645, the commit that added tags.

**Evidence:**
- **Reproduction:** I created three bookmarks with the pre-tags version (8dd82b9), then ran `bm tag 2 recipes` with the current one. `bm list --tag recipes` listed all three, and all three records in the file got `"tags": ["recipes"]`. This happened every run.
- **Control:** with bookmarks created by the current version, only #2 is listed.
- **Proof of the shared array:** a scratch script loading two old bookmarks showed `a.tags === b.tags` is `true`, and adding a tag to one showed up on the other.
- **Why the tests missed it:** the existing "saved before tags" test creates its bookmark with the current `add()`, which already writes `tags: []`, so it never loads an old-format bookmark.

**Damaged data:** For anyone who tagged after updating, the first tag they applied was written to every bookmark that existed before the update. That first save added a `tags` field to every bookmark, so later tags only reach the one you name. Bookmarks added after the update are fine. The fix stops new damage but doesn't repair files already written. I found no other code with the same mistake.

**Fix:** `fromRecord()` should give each bookmark its own array (`record.tags ?? []`), and `noTags` goes away.

**Plan:** `docs/plans/2026-10-27-fix-tag-applies-to-all.md`. It starts with a regression test that loads two bookmarks with no `tags` field. The exact failure message in the plan is my prediction, not from a real run.

**Open question:**
1. Should we repair files that are already damaged? Nothing records which tags the bug added, so any automatic repair would be a guess. I recommend no automatic repair: tell users a tag may have landed on all their older bookmarks. Removing it needs a `bm untag` command, which doesn't exist yet, so that would be a separate ticket.

The only change in the working tree is the new `docs/` folder holding the plan.