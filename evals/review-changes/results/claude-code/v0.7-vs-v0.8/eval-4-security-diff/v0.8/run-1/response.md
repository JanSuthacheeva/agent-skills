I found and fixed two security bugs on `feature/bookmark-share`. Before the fixes, someone could send you a bookmark file that runs commands on your machine when you open one of its bookmarks. All 16 tests pass at `181106f`. Nothing was pushed.

## Fixed
- **Command injection when opening a bookmark** (`dddfece`). `openUrl` passed the URL through a shell. I proved it: importing `https://a.dev/?$(touch${IFS}/tmp/.../pwned)` and opening it created the file. The fix runs the opener directly with the URL as its only argument, as the plan says. There is a new test in `test/opener.test.ts`.
- **Any URL scheme was accepted** (`a79f6cf`). `parseWebUrl` let through `file:`, `javascript:`, `smb:` and any other scheme that parses, but the plan allows only `http:` and `https:`. There are new tests for the URL check and for `import` (nothing gets stored).

A separate agent checked both fixes. The tests fail without them, and the fixes break nothing else.

## Open (need your decision)
1. **`bm add` doesn't check URLs**, so `bm add javascript:...` is saved and can be opened. I recommend calling `parseWebUrl` in `add` too. It's a small change, but it changes what `add` accepts, so I left it to you.
2. **`BM_OPENER` must now be a program name only.** A value with arguments, like `BM_OPENER='open -a Safari'`, used to work only because it went through the shell. It now fails with "not found" (`ENOENT`). I recommend documenting this rather than splitting the string.
3. **`bm import` doesn't handle bad files.** A missing file, invalid JSON or a top-level object crashes with a stack trace. A non-string `title` is saved as-is, which breaks `Bookmark.title: string`. I recommend checking each entry and treating all of these as bad input (exit code 2).
4. **A missing opener program crashes `bm open`** with an uncaught error. This was already the case before the branch.

## Where to look
1. `src/opener.ts`: the whole file is now 9 lines.
2. `src/cli.ts`, the `import` case: how the shared file is parsed and what reaches the store (items 1 and 3 above).
3. `src/urls.ts`, `parseWebUrl`.

The store's `get` and `importAll` and the CLI's error handling are routine and can be skimmed.

## Checks
- Tests passed before my changes (13/13) and after them (16/16, at `181106f`). The project has no lint or type-check scripts.
- `/security-review` ran on `main...HEAD` and reported the same two issues. Both are fixed.
- I added this summary to the plan as a `## Review` section (`181106f`).