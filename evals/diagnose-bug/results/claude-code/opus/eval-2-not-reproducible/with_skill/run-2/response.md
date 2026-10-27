I couldn't make SHOP-312 happen on the current `main` (0b70eb5), so I haven't written a fix plan. I did find a different bug along the way that may be what the reporter actually ran into.

**What the ticket says:** running `bm add https://example.com 'The "best" tools'` corrupts the bookmarks file and bm stops working.

**What I tried** (each run used a throwaway file via `BM_FILE`, never your real one):
- The exact command from the ticket: it prints `added 1` and exits 0. The file is valid JSON and the title is stored correctly as `"The \"best\" tools"`. `list` then shows `1  The "best" tools  https://example.com`.
- Variations: double quotes, an apostrophe and a backslash in one title; curly quotes `“…”`; quotes inside the URL; going through `npm run bm --` instead of `node` directly; tagging a quoted bookmark and then adding more. Every run exited 0, `list` worked, and the file still parsed as JSON afterwards.
- Quotes can't break the file as written: `src/store.ts` saves with `JSON.stringify`, which escapes them.

**The other bug:** adding a bookmark wipes the tags from every bookmark already saved.
- Steps: `add https://a.com plain` → `tag 1 tools` → `add https://b.com other`. After that, `list --tag tools` prints nothing and the file has no `tags` field left.
- Cause: `add()` saves through `save()`, which uses `toRecord` (`src/store.ts:27`), and `toRecord` drops `tags`. Only `tag()` writes tags back.
- It came in with 0b70eb5 ("tag bookmarks and list by tag").
- From the reporter's side this looks like "I added a bookmark and things broke", so the quoted title may be a coincidence. That's a guess; I haven't checked it against what they saw.

**To pin SHOP-312 down, could you get from the reporter:**
1. A copy of the "corrupted" file and the exact error or output they got afterwards.
2. Their bm version or commit, Node version, and shell. On Windows `cmd`, single quotes don't quote anything, so the command arrives split differently.
3. What "stops working" means: a crash or JSON parse error, or bookmarks or tags missing from `list`.

If it turns out to be lost tags, I'll diagnose that and write the fix plan, either under SHOP-312 or a new ticket. The working tree is unchanged and nothing was committed.