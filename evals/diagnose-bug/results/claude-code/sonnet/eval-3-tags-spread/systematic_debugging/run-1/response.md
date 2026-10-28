**SHOP-313 is fixed.** Tagging one bookmark no longer tags the others, and all 16 tests pass.

**Root cause:** `fromRecord` in `src/store.ts` filled in missing tags with one module-level array, `noTags`. Bookmarks saved before tagging existed have no `tags` field, so they all got that same array. `store.tag()` then pushed onto it, which changed every bookmark that lacked tags. Saving wrote that tag out for all of them, so `bm list --tag recipes` showed all 40.

**Why the tests missed it:** they create bookmarks with `add`, which always writes `tags: []`. Only older bookmark files hit the fallback.

**Fix:** `fromRecord` now uses `record.tags ?? []`, so each bookmark gets its own array. I deleted `noTags`.

**Test:** I added a regression test in `test/store.tags.test.ts`. It loads a file of bookmarks with no `tags` field and tags one of them. It failed before the fix and passes now.

**Existing data:** I haven't touched anyone's bookmarks file. The reporter's file probably already has the tag saved on every bookmark. I'd expect them to need `bm untag`-style cleanup by hand, but the CLI has no such command.