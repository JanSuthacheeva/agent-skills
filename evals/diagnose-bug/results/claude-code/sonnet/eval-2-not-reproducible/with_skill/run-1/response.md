I couldn't reproduce SHOP-312, so I haven't written a fix plan.

**What I tried**, using a scratch file via `BM_FILE=/tmp/bm-scratch.json` and not your real data:
- I ran the exact command from the ticket, `bm add https://example.com 'The "best" tools'`. It exited 0 and printed `added 1`.
- The file contained valid JSON with the quotes escaped: `"title": "The \"best\" tools"`.
- `bm list` printed `1  The "best" tools  https://example.com` and exited 0.
- I also ran `bm tag 1 work` on that bookmark, then added `say "hi"` and a title that is just `"`. All exited 0, `list` showed all three correctly, and the file still parsed as JSON.

The write path in `src/store.ts` goes through `JSON.stringify`, which escapes quotes, so I see no way for a double quote in a title to corrupt the file. I left the working tree unchanged and deleted the scratch file.

**What would help:**
1. The exact error or output when `bm` "stops working", and the exit code.
2. The corrupted `.bookmarks.json`, or at least the line that is broken.
3. Your shell and how you typed the command. Quoting differs between shells, such as Windows `cmd` or PowerShell, and can split or mangle the argument before `bm` sees it.
4. Whether `bm` is the one in this repo or an installed or older version. Git history has only three commits, and none of them touch quoting.
5. Whether anything else edits the file, such as a sync tool or a script that writes it by hand.

If you can send the broken file or the error text, I'll pick it up from there.