SHOP-311 is fixed: tags no longer disappear when you add a bookmark. `bm list --tag work` was never broken. The tests pass (16 of 16), including a new one for this bug.

**Root cause:** `toRecord` in `src/store.ts` left `tags` out of what it wrote to disk. `add()` loads every bookmark and saves them all back through `toRecord`, so each `add` wiped the tags from all existing bookmarks. `tag()` avoided the problem only because it re-attached `tags` by hand when it wrote the file.

**Reproduction:** I ran `add`, `tag 1 work`, `add` and then `list --tag work`. The list was empty, and the file had no `tags` for bookmark 1.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now uses `all.map(toRecord)`, so the manual workaround is gone.

**Test:** I added "adding a bookmark keeps existing tags" to `test/store.tags.test.ts`. It failed before the fix and passes now.

I didn't re-run the CLI reproduction after the fix. Any bookmarks whose tags were already wiped from a real file are gone and would need re-tagging.