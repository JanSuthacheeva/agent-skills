I can't reproduce SHOP-312 on the current code, so I haven't changed anything.

**What I tried** (each in a fresh `BM_FILE`):
- The exact command from the ticket, `bm add https://example.com 'The "best" tools'`. The file is valid JSON with the quotes escaped (`"The \"best\" tools"`), and `bm list` prints the title correctly.
- Harder titles with quotes, an apostrophe and a backslash, plus several adds in a row and a `tag` call. The file stayed valid every time and `list` worked.
- `npm test` passes.

**Why it doesn't happen:** `src/store.ts` writes the whole file with `JSON.stringify` and reads it with `JSON.parse`, and it has done so since the first commit. Quotes in a title can't break that, so this code can't produce the corruption the ticket describes.

Possible explanations, none of them confirmed:
- The reporter edited `.bookmarks.json` by hand.
- Their shell handled the quoting differently. Windows `cmd`, for example, doesn't treat `'…'` as quotes.
- They were on a different build of bm.

To go further we need the actual broken file and the error `bm` printed. I'd ask the reporter for both before touching the code.

**A separate bug I found and reproduced:** adding a bookmark deletes all existing tags. `save()` goes through `toRecord()` (`src/store.ts:27`), which leaves out `tags`, and `add()` calls `save()`. Steps: `add` → `tag 1 work` → `add` again, and bookmark 1's tag is gone from the file. A user could easily see that as "bm broke my file", but it has nothing to do with quotes. It's a one-line fix plus a regression test. Should I fix it, either under SHOP-312 or as its own ticket?