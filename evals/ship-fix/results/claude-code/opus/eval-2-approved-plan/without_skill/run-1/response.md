SHOP-311 is fixed: adding a bookmark no longer removes existing tags. I built all three tasks in the plan, and nothing changed from what it described.

**Commits** (on `fix/SHOP-311-tags-lost`, not pushed):
1. `bb8ee7c` **store: keep tags when saving bookmarks.** Adds the regression test "adding a bookmark keeps existing tags". Before the fix it failed exactly as the plan predicted, giving `[]` instead of `['work']`. The fix makes `toRecord()` copy `tags`.
2. `7b27af6` **store: save tags through save() like add().** `tag()` now calls `this.save(all)` instead of writing its own records, so there is one way to write the file. Adds the test "tagging two bookmarks keeps both tags". That test would also have passed before this commit; it's there to check the cleanup didn't break tagging.
3. `ac135c2` **docs: tick the SHOP-311 end-to-end check.** Only ticks the last box in the plan.

**End-to-end check:** I ran the reproduction from the plan against a temporary bookmarks file. After the second `bm add`, `list --tag work` printed `1  A  https://a.example` with exit code 0. In the file, bookmark 1 has `"tags": ["work"]`. All 17 tests pass. The project has no lint or type-check step, so tests are the only automated check.

**How it works now:** `main.ts` → `run()` in `cli.ts` → `BookmarkStore.add()` or `tag()` → `save(all)` → `toRecord()` → file. Tags now go through `toRecord()` like every other field, so any write keeps them.

**Still open:**
- Every bookmark written from now on has a `tags` field, as `"tags": []` if it has no tags. Older files without the field still load fine.
- Tags that earlier `bm add` runs already deleted can't be recovered and have to be added again. The ticket should probably tell users this.