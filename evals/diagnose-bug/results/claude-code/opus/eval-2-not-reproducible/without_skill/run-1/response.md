## SHOP-312 doesn't reproduce

**The quote bug:** I ran the exact command from the ticket against a temp `BM_FILE`, `bm add https://example.com 'The "best" tools'`. I also tried a title with both quotes and a backslash. Both were saved with correct escaping (`"The \"best\" tools"`), listed correctly, and the file stayed valid JSON through later commands.

That matches the code. `src/store.ts` has always written the file with `JSON.stringify` and read it with `JSON.parse`, including in the first commit, so no version of `bm` could have written broken quotes. If the reporter's file really is broken, it was probably edited by hand or by another tool. Asking them for the file contents, or the exact error `bm` prints, would settle it.

**A different bug I found while testing:** adding a bookmark erases every existing tag.
- `add()` calls `save()`, and `save()` uses `toRecord()` (`src/store.ts:27`), which doesn't include `tags`.
- So every `bm add` rewrites the file without tags. In my test, bookmark 1 was tagged `dev`. After one more `add`, the tag was gone from the file and `bm list --tag dev` returned nothing.

This could be what the reporter saw as "bm stops working" if they were using tags. The fix is small: have `toRecord` include `tags`, and drop the workaround in `tag()` that adds them back separately. A regression test would cover tagging a bookmark and then adding another one.

Should I make that fix, and file it as its own ticket or as part of SHOP-312?