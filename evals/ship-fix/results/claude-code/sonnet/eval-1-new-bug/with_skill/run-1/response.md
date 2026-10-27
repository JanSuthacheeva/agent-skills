Diagnosis is done and the fix plan is written. I changed no code and committed nothing.

**Root cause:** `toRecord()` at `src/store.ts:25` doesn't write `tags`. `add()` (`src/store.ts:59`) calls `save()`, which rewrites every bookmark through `toRecord()`, so each `bm add` wipes the tags on all existing bookmarks. Commit 6d668ea introduced it. `list --tag` itself is fine.

**Evidence:** I reproduced it with the real CLI against a scratch `BM_FILE`:
- `add`, then `tag 1 work`, then `list --tag work` prints bookmark 1.
- After `add` of a second bookmark, `list --tag work` prints nothing, and the file has no `tags` key on either bookmark.
- It fails every run.

**Also affected:** `add()` is the only caller of `save()`, so no other writer drops tags. Tags already lost in users' files are gone for good.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It has two tasks: a regression test plus the fix in `toRecord()` (and simplifying `tag()`), then an end-to-end rerun of the reproduction.

**Open question:**
1. Should we repair the tags already lost? I recommend no, because the data can't be reconstructed. The MR would tell users to re-tag.

Do you approve the plan and my answer to the question? Once you do, I'll create the branch `SHOP-311`, commit the plan on it, and then ask you to run `/compact` and say "continue fixing".