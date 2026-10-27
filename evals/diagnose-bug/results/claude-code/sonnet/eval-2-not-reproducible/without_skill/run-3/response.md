I couldn't reproduce SHOP-312. Titles with double quotes work fine here, and I haven't changed any code.

**What I tried**
- I ran `bm add https://example.com 'The "best" tools'` against a scratch file (`BM_FILE=/tmp/bm-test.json`).
- The file came out as valid JSON, with the title stored as `"The \"best\" tools"`.
- `bm list` read it back correctly.
- A second add with `x "y"` also worked.

The store writes through `JSON.stringify` and reads with `JSON.parse` (`src/store.ts`), so quotes are escaped correctly. I don't see a way for them to corrupt the file.

**A different bug I found along the way**
- `save()` goes through `toRecord()`, which leaves out `tags`.
- Any `add` therefore wipes the tags on every existing bookmark. I tagged bookmark 1 with `foo`, then added bookmark 2, and the tag was gone.
- `tag()` avoids this because it writes the tags itself.
- This might be what the reporter actually saw, but it loses tags rather than corrupting the file.

**Next steps**
- Ask the reporter for their bm version or commit, the exact shell command, and the corrupted file. The shell is a likely factor: quoting differs between shells, especially on Windows `cmd`. Also ask whether the file was edited by hand or by another tool.
- Want me to fix the tag-loss bug, with a regression test? It's a one-line change to `toRecord`. I'd file it as a separate ticket rather than under SHOP-312.