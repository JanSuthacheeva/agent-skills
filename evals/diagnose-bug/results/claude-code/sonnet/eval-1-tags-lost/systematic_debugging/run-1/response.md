SHOP-311 is fixed: adding a bookmark no longer wipes the tags on the existing ones. All 16 tests pass, including a new regression test.

`list --tag` wasn't the problem. `toRecord()` in `src/store.ts` never wrote the `tags` field. `add()` reloads every bookmark and saves them through `save()`, so each `add` rewrote the file without tags. `tag()` only appeared to work because it wrote its own records with tags added back. I reproduced this with the CLI: after `tag 1 work` and then `add`, the JSON file had no tags.

**Changes**
- `toRecord()` now includes `tags`.
- `tag()` now calls `this.save(all)` instead of building its own records.
- I added `adding a bookmark keeps existing tags` to `test/store.tags.test.ts`. It failed before the fix and passes now.

I haven't re-run the CLI reproduction against the fixed code. The new test covers the same path.

Bookmarks that lost their tags before this fix don't get them back, so they need re-tagging.

I didn't update the ClickUp ticket or commit anything.