I couldn't reproduce SHOP-312, so I haven't written a fix plan.

**Ticket:** "When I add a bookmark whose title has double quotes in it, like `bm add https://example.com 'The "best" tools'`, the bookmarks file gets corrupted and bm stops working." It gives no version, platform, file contents or error message.

**What I ran** (real CLI, scratch file via `BM_FILE=/tmp/bm-repro.json`, since removed):
- `bm add https://example.com 'The "best" tools'` printed `added 1` with exit 0. The file is valid JSON with `"title": "The \"best\" tools"`, and `bm list` shows `1  The "best" tools  https://example.com`.
- Variations all worked too:
  - a title with quotes plus a backslash (`say "hi" \ back`);
  - a title that is just `"`;
  - several adds in a row;
  - `tag` and `list --tag` alongside quoted titles.
- The store writes with `JSON.stringify` (`src/store.ts:77`), which escapes quotes correctly. The working tree is clean.

**What would help:**
1. The corrupted `.bookmarks.json` and the exact error `bm` prints.
2. The exact command, and the shell (zsh, bash, PowerShell or cmd). Windows shells handle quotes differently, so the title could arrive mangled.
3. The Node version and the repo commit they run.
4. Whether they edit the file by hand or use another tool alongside `bm`.

While reading the code I noticed something unrelated and unverified. `add` calls `save`, which uses `toRecord`, and `toRecord` omits `tags` (`src/store.ts:25`). Adding a bookmark after tagging another may therefore wipe existing tags. That isn't what SHOP-312 describes, but I can reproduce it and write it up separately if you want.