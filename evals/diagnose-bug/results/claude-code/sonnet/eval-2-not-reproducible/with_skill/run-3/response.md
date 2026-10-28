I couldn't reproduce SHOP-312, so I haven't written a fix plan and changed no code.

**What the ticket says:** `bm add https://example.com 'The "best" tools'` corrupts the bookmarks file and `bm` stops working. The ticket has no version, platform, file contents or error message.

**What I ran:** the real CLI, via `npm run bm`, with `BM_FILE` pointing at a scratch file.
- `bm add https://example.com 'The "best" tools'` printed `added 1` and exited 0. The file held valid JSON with the title stored as `"The \"best\" tools"`. `bm list` printed `1  The "best" tools  https://example.com`.
- I also tried a title that is only `"quoted"`, a title mixing a backslash and quotes (`back\slash "q"`), and `bm tag` on the quoted-title bookmark followed by `bm list`. All of them exited 0 and the file stayed valid JSON.
- `src/store.ts` writes the file with `JSON.stringify`, which escapes quotes correctly, so I don't see a way for quotes to corrupt it.
- The working tree is unchanged.

**What would help:**
1. The exact command and shell. Quoting differs between shells, and the title may not have reached `bm` as typed.
2. The corrupted file's contents, or the error `bm` prints afterwards.
3. Which `bm` version or commit they ran, and whether `BM_FILE` was set.
4. Whether the file was edited by hand or written by another tool, or whether several `bm` processes ran at once.

**Unrelated finding:** `save()` in `src/store.ts` uses `toRecord`, which drops `tags`. So `bm add` after `bm tag` looks like it would erase existing tags. I read this in the code and haven't run it. I can diagnose it as a separate bug if you want.

Can you get the reporter's file or error message?