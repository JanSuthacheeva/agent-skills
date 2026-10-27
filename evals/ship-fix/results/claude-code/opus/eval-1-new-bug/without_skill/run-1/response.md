The fix is done, reviewed and committed on `fix/shop-311-tags-disappear`, but nothing is pushed yet. I'm holding back on pushing and creating the MR until you've seen the description, because pushing publishes the branch.

**Cause:** the ticket blames `list --tag`, but that command works. The real problem is that every `bm add` erased all tags in the bookmarks file. `toRecord()` (`src/store.ts:26`) didn't copy `tags`, and `add()` saves through it. Commit 59a6d9d introduced this: it worked around the gap inside `tag()` instead of fixing `toRecord()`. I reproduced it with the real CLI: the file had `"tags": ["work"]` after `bm tag` and none after the next `bm add`.

**Fix:** `toRecord()` now writes `tags`, and `tag()` saves through `save()` like `add()` does. A regression test failed for the expected reason (`[]` vs `['work']`) before the fix. After the fix, the reproduction prints `1  A  https://a.example` from `bm list --tag work`, and all 17 tests pass. A separate agent reviewed the branch. It found no problems in the code and added two missing tests: one for loading files saved before tags existed, and one CLI-level regression test.

**Tags already lost can't be recovered.** Anyone who ran `bm add` since 59a6d9d has lost all their tags and has to re-tag. I've said this in the MR description; tell me if you'd handle it another way.

Draft MR (GitLab, `shop/shop`, into `main`):

```
SHOP-311 Tags disappear

Every `bm add` rewrote the bookmarks file without tags, so `bm list --tag`
found nothing afterwards. `toRecord()` never copied `tags`; `tag()` had
worked around it instead of fixing it. Records now always carry `tags`, and
`tag()` saves through `save()` like `add()`, so there is one write path.

- Untagged bookmarks are now stored with `"tags": []`. Files without the key
  still load, since `fromRecord()` defaults it to `[]`.
- Tags erased by `bm add` since 59a6d9d cannot be recovered from the file;
  affected users have to re-tag.

Review:
1. `src/store.ts` `toRecord()` / `fromRecord()`: the stored record format,
   the only data change.
2. `src/store.ts` `tag()`: now writes via `save()`, the same path as `add()`.
Skim: the new tests and the fix plan in `docs/plans/`.

Refs: SHOP-311
```

Should I push the branch and create the MR?