I fixed SHOP-311 on the branch `fix/SHOP-311-tags-lost-on-add`, but there's no merge request yet: permission to push the branch was denied. The text for it is below.

**Root cause:** `list --tag` works fine, so the ticket's guess is wrong. The bug is in `toRecord()` at `src/store.ts:26`, which never wrote `tags` to the file. `add()` saves every bookmark through it, so each new bookmark wiped the tags from all the others. `tag()` only worked because it patched the tags back on in its own write. This came in with 2e73a90, the commit that added tags.

**Evidence:** I ran the ticket's steps with the real CLI on a scratch file. `list --tag work` printed the tagged bookmark until the next `add`, then printed nothing. The file had lost every `tags` key at that point.

**What changed:**
- `toRecord()` now writes `tags`, and there's a regression test for it. Before the fix the test failed with `[]` instead of `['work']`.
- `tag()` now saves through `save()`, the same path as `add()`, instead of patching tags back on.
- The reviewer agent found that the test for files written before tags existed no longer covered them, so it rewrote it. Without that, removing the fallback for old files would have made `bm list --tag` crash on them with every test still passing.

All 16 tests pass. Re-running the ticket's steps now prints `1  A  https://a.example`. The plan, with a review section, is in `docs/plans/2026-10-27-fix-tags-lost-on-add.md`.

**Decision for you:** anyone who added a bookmark after tagging has already lost those tags, and the file can't bring them back. I'd tell affected users to tag them again; the description says so.

If you allow the push, I'll push and create the MR. Or you can run `git push -u origin fix/SHOP-311-tags-lost-on-add` yourself and open it with:

**Title:** `SHOP-311 Tags disappear`

```
Adding a bookmark erased the tags of every bookmark, so `bm list --tag work` came back empty after any `add`. `list --tag` was fine; `toRecord()` never wrote `tags`, and `add()` saves through it. It now writes them, and `tag()` saves through the same path instead of patching tags back on.

- Tags already lost to an earlier `add` cannot be recovered from the file; affected users have to tag those bookmarks again.
- Files written before tags existed still load with no tags (`fromRecord()`'s `?? []`); the test for that now builds such a file by hand, since `add()` writes `tags` now.

Review:
1. `src/store.ts` `toRecord()` / `fromRecord()`: the single rule for how a bookmark is stored.
2. `BookmarkStore.add()` and `tag()`: both write through `save()`.
Skim: `test/store.tags.test.ts`, the plan in `docs/plans/`.

Refs: SHOP-311
```