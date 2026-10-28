SHOP-311 is fixed: tags now survive adding a new bookmark. All 16 tests pass, and the exact steps from the ticket now list the tagged bookmark.

**The cause wasn't `list --tag`.** That command worked fine; the tags had already been deleted from the file before it ran. `add` was erasing them:

- `toRecord()` in `src/store.ts` turns a bookmark into the shape that gets saved to the file, and it was leaving out `tags`.
- `add()` saves every bookmark through `toRecord()`. So each new bookmark rewrote the whole file with no tags on any existing bookmark.
- `tag()` didn't have the problem because it added `tags` back itself before writing, so the issue only showed up after tagging and then adding.

I reproduced this with the CLI: the tag was in the file before the `add` and gone after it.

**Changes:**
- **`src/store.ts`:** `toRecord()` now includes `tags`, and `tag()` saves through the normal `save()` path instead of its own workaround.
- **`test/store.tags.test.ts`:** new test, "adding a bookmark keeps existing tags", which tags a bookmark, adds another, and checks the tag is still there. It failed before the fix. The existing tests always tagged after the last `add`, which is why they missed this.

**Note for the reporter:** this stops tags from being lost from now on, but tags already erased from their bookmarks file can't be recovered. They'll need to tag those bookmarks again.

I haven't committed anything or updated the ticket.