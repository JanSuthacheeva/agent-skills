I reviewed `feature/bookmark-share` against `main` and fixed two security bugs. Both ignored rules your plan states, and together a shared bookmark file could run any command on a colleague's machine. All 15 tests pass at `780108e`. There's no lint or type-check configured, so none ran.

## Fixed
- **Shell command injection in `bm open`** (`780108e`): `openUrl` built a shell command with the URL pasted inside quotes. A URL like `https://a.dev/$(touch$IFS/tmp/x)` survives URL parsing unchanged. I put it through `openUrl`, the function `bm open` calls, and it created the file. `openUrl` now runs the opener directly with the URL as its only argument, with no shell. A new test checks this.
- **Only web links should be accepted** (`13ffac8`): `parseWebUrl` accepted `javascript:` and `file:` URLs, so imports let them through. It now accepts only `http:` and `https:`, and I added the "rejected scheme" test the plan asked for.

A separate reviewer agent checked both fixes with edge cases (uppercase schemes, `data:`, `blob:`, quotes and backticks) and found no problems.

## Open (left for you, because each changes what users see)
- **`bm add` doesn't check URLs, and `bm open` launches whatever was stored.** I added `file:///etc/passwd` and `--help` and both were saved, so `bm open` would hand them to the browser launcher. Without a shell this can't run commands any more, but it can still open local files or pass options to the launcher. I'd recommend checking URLs in `add`, or at least in `open`.
- **`import` crashes with a stack trace** on a missing file, invalid JSON or a file that isn't a list. I'd recommend an error message and exit code 2.
- **`import` stores titles that aren't text as they are.** A title like `{"x":1}` is saved to your bookmarks file and shows in `list` as `[object Object]`. I'd recommend rejecting those entries or converting the title to text.
- **`BM_OPENER` must now be a single program name.** A value with arguments, such as `firefox --private`, no longer works. That follows from the plan's "no shell" rule, but it may surprise anyone already using it.

## Where to look
1. `src/cli.ts`, the `import` case: everything from the shared file is untrusted, and the three `import` issues above are here.
2. `src/cli.ts`, the `open` case, then `src/opener.ts`: what reaches the opener.
3. `src/store.ts`, `importAll`: `add` now goes through it. That's routine and its tests cover it.

The rest (`get`, the error classes, the error-to-exit-code mapping) is routine and can be skimmed. I added this summary to the plan as a `## Review` section (`4a7ce88`). Nothing is pushed.