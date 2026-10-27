SHOP-311 is fixed: tags now survive a `bm add`. All three tasks in the plan are done and committed on `fix/SHOP-311-tags-lost`, and all 17 tests pass (15 before I started). The project has no lint or type-check scripts, so none were run.

**End-to-end check:** I ran the plan's reproduction against a fresh `BM_FILE`. After the second `add`, `list --tag work` printed `1  A  https://a.example` and exited 0. The file still has `"tags": ["work"]` on bookmark 1.

**Commits**
1. `6bf30a6 bm: keep tags when saving bookmarks` adds the test "adding a bookmark keeps existing tags", which failed with `[]` instead of `['work']` before the fix. The fix makes `toRecord()` copy `tags`.
2. `9780c4f bm: write tags through save() like add()` makes `tag()` call `this.save(all)` instead of building its own records, and adds the test "tagging two bookmarks keeps both tags".
3. `335fdf2 docs: tick the SHOP-311 end-to-end check` ticks the last checkbox in the plan.

**Deviations and side effects**
- The task 2 test passed before the change. That's expected: the change is a refactor, because `tag()` already added tags back by hand. The test checks that the behaviour stays the same; it doesn't reproduce a bug.
- Every record in the file now gets a `tags` field, so untagged bookmarks are written as `"tags": []` where the field used to be missing. Older files still load, because `fromRecord()` treats a missing field as `[]`.

**Still open**
- Tags already removed from users' files can't be recovered and have to be added again, as the plan says. It may be worth saying so on the ticket.
- Nothing has been pushed and no merge request is open.

**How it works now:** `bm add` and `bm tag` both go through `BookmarkStore.save()`, which writes every bookmark with `toRecord()`. That's the only way the file gets written. `bm list --tag` reads it back through `load()` and `fromRecord()` into `listTagged()`.