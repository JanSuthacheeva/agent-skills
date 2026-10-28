I couldn't reproduce SHOP-312, and I haven't changed any code.

**What I tried**
- I ran `bm add https://example.com 'The "best" tools'` through `npm run bm` and through `node src/main.ts` directly.
- The file stays valid JSON, and the title is stored as `"The \"best\" tools"`.
- `bm list` reads it back correctly.
- `store.ts` writes with `JSON.stringify`, which escapes quotes, so the store can't produce this corruption on its own.

**What the report might mean**
- The reporter may be on an older version or a different code path, or the shell may have mangled their quoting. The ticket doesn't say what they saw. It gives no error message, no file contents and no `bm` version. I'd ask them for the corrupted file and the exact error.
- I did find a different bug while testing. `save()` calls `toRecord()`, which drops `tags`. After `bm tag 1 foo`, the next `bm add` rewrote the file without the tag. The `.bookmarks.json` file stays valid, but the tag data is lost. That may not be what the reporter hit, but it is a real data-loss bug in `src/store.ts`.

Do you want me to fix the tag loss? I can also add a regression test for quoted titles.