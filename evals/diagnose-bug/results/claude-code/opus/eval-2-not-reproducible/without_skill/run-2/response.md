I couldn't reproduce SHOP-312. I didn't change any code.

**What I tried:** I used a temp `BM_FILE` and ran the ticket's exact command, `bm add https://example.com 'The "best" tools'`, plus a few other titles with double quotes. Every add worked and `bm list` showed the titles correctly. The file stayed valid JSON with the quotes escaped (`"The \"best\" tools"`). The test suite passes.

**Why it shouldn't happen in this code:** `src/store.ts` writes the file with `JSON.stringify` and reads it with `JSON.parse`, which handle quotes on their own. The git history shows it has always worked this way, so no older version builds the JSON by hand.

**Possible causes on the reporter's side:**
- **Shell quoting:** if the quotes were nested differently (for example `"The "best" tools"`), the shell would split or strip the arguments before `bm` sees them. That gives a wrong title, though, not a broken file.
- **Hand-editing:** someone may have edited `~/.bookmarks.json` directly and left an unescaped `"` in it. `JSON.parse` would then throw on every command, which matches "bm stops working".
- **An older or different install** than this repo.

I'd ask the reporter for the exact command, the error message `bm` prints, and a copy of the broken file.

**A different bug I found while testing:** adding a bookmark erases the tags on all existing bookmarks. In my run, bookmark 1 was tagged `foo`, and after the next `bm add` the tag was gone from the file. The cause is that `toRecord` in `src/store.ts:26` leaves out `tags`, and `save()`, which `add()` calls, writes every record through it. Only `tag()` puts the tags back. This might be what the reporter actually ran into, but it loses data rather than corrupting the file. Should I fix it under a new ticket, or attach it to this one?