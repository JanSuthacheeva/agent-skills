**Root cause:** `list --tag` is not broken. `toRecord()` at `src/store.ts:22` leaves `tags` out of the stored record. `add()` (`src/store.ts:55`) rewrites the whole file through `save()`, so it wipes every existing bookmark's tags. Commit 0b70eb5 added tags but only patched `tag()` (`src/store.ts:68`), which re-adds them by hand.

**Evidence:** I ran the real CLI against a scratch file (`BM_FILE=/tmp/sc311.json`, removed afterwards).
1. I added two bookmarks and ran `bm tag 1 work`.
2. `bm list --tag work` printed bookmark 1.
3. After `bm add` of a third bookmark, `bm list --tag work` printed nothing, with exit code 0.
4. It fails every run.

I did not inspect the file contents after the add, so the loss is inferred from the empty list rather than read from disk.

**Also affected:**
- No other callers of `save()` in `src/`.
- Tags already lost from anyone's `.bookmarks.json` can't be recovered by code.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It's the only change in the tree, and nothing is committed.

**Open question:**
1. Should we repair the tags that were already lost? I recommend no, because they're unrecoverable. Mention in the release notes that users need to re-tag.

I assumed the regression test goes in the existing store tests.