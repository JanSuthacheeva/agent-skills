I couldn't reproduce SHOP-312, so I haven't written a fix plan.

**What the ticket says:** adding a bookmark with double quotes in the title, e.g. `bm add https://example.com 'The "best" tools'`, corrupts the bookmarks file and bm stops working.

**What I tried** (Node v22.23.1, a throwaway bookmarks file via `BM_FILE`, now deleted):
- The exact command from the ticket printed `added 1` and exited 0. The file is valid JSON and the title is stored as `"The \"best\" tools"`. `bm list` shows it correctly.
- Variations: mixed `"`, `'` and `\` in one title, quotes split across several arguments, running through `npm run bm --`, tagging a quoted bookmark, `list --tag`, and adding more bookmarks afterwards. All of these worked and `JSON.parse` read the file without errors.
- `src/store.ts` has always written the file with `JSON.stringify`, from the first commit on. That escapes quotes correctly, so no version in the history should corrupt the file this way.

**Something else I found while testing.** Adding any bookmark wipes the tags off every existing bookmark. After `bm tag 1 tools` then `bm add https://c.com 'after tag'`, `bm list --tag tools` printed nothing. The cause is that `add()` saves through `toRecord()` (`src/store.ts:27`), which leaves out `tags`. This doesn't corrupt the file, but bookmarks seemingly disappearing from tag lists could feel like "bm stops working". It may be what the reporter actually ran into.

**What would help:**
1. The broken bookmarks file itself, or the exact error bm printed afterwards.
2. The reporter's bm version or commit, Node version, OS and shell, plus how they ran it (a shell alias or a different wrapper could mangle the quotes before bm sees them).
3. Whether they had tagged bookmarks and noticed tags vanishing. If so, I'd treat the tag-wiping bug as the real issue, either under SHOP-312 or as a new ticket, and diagnose that.

Do you want me to diagnose the tag-wiping bug now, or wait for more detail from the reporter? Nothing in the working tree has changed.