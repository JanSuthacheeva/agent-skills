I couldn't reproduce SHOP-312, so I haven't changed any code.

**What I tried:** I ran the exact command from the ticket, `bm add https://example.com 'The "best" tools'`, plus titles with mixed quotes, apostrophes and backslashes, against a throwaway file (`BM_FILE`). Every write produced valid JSON with the quotes escaped correctly (`"The \"best\" tools"`), and `bm list` read them back fine. `npm test` passes.

**Why the code can't cause it:** the file is only ever written in one place, `src/store.ts:89`, and that line uses `JSON.stringify`, which escapes quotes. Git history shows it has always been written that way; no version ever built the JSON by hand. A title from the command line can't produce a broken file through this path.

**What's needed to move forward:**
- The broken bookmarks file itself (by default `~/.bookmarks.json`), or at least the error `bm` prints when it "stops working".
- Their shell, OS and `bm` version. The cause may be outside `bm`, such as someone editing the file by hand, a wrapper script, or a different install.

**A different bug I found while testing:** adding a bookmark erases the tags on all existing bookmarks. I tagged bookmark 1, added bookmark 3, and the tag was gone from the file. The cause is that `add()` saves through `toRecord()` (`src/store.ts:27`), which doesn't include `tags`; only `tag()` writes them. Nothing ends up corrupted, but users lose data silently. Someone might report that as "bm stops working", though it doesn't match the quotes description. I'd file it as its own ticket. Want me to write a failing test and fix it?