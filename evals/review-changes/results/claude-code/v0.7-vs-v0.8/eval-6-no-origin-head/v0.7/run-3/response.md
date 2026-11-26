I found two security bugs on `feature/bookmark-share` and fixed both. Several smaller issues are still open for you to decide. All 16 tests pass.

## Fixed
- **Command injection in `bm open`** (b57f2da): `openUrl` ran the URL through a shell. I imported a shared file containing `https://a.dev/$(touch$IFS<dir>/pwned)`, ran `bm open 1`, and the file was created. So anyone who sends you a bookmark file could run commands on your machine. It now uses `execFileSync(opener, [url])`, which never involves a shell. A new test in `test/opener.test.ts` checks this.
- **Any URL scheme was accepted** (ffbdb19): `parseWebUrl` let `javascript:` and `file:` URLs through, although the plan allows only `http:` and `https:`. It now rejects other schemes, with tests in `urls.test.ts` and `cli.share.test.ts`.

A second agent re-checked both fixes. Each new test fails when its fix is reverted. Upper-case schemes and URLs containing quotes or backticks are handled correctly.

## Open (my recommendation for each)
- **`bm add` doesn't check URLs, and neither does the store file.** So `bm open` can still pass `javascript:`, `file:` or `-n`-style values to the opener. I'd call `parseWebUrl` in `add` and again in `open`. I left this alone because it changes what `add` accepts, and the plan doesn't cover that.
- **A missing, malformed or non-array import file crashes with a stack trace** and exits 1. I'd add an error class and map it to exit 2 ("bad input" under the AGENTS.md convention).
- **Titles from imported files are stored without checks.** `{"x":1}` is saved as an object. I'd require a string.
- **`BM_OPENER` can no longer include arguments**, such as `open -a Safari`, now that there's no shell. This matches the plan; either document it or split the value on whitespace.
- **`bm open ''` prints `no bookmark 0`** instead of the usage message. This is minor.

## Where to look
1. From `src/cli.ts` `import` to `src/store.ts` `importAll`: how untrusted file contents get validated before they're saved.
2. `src/opener.ts` together with `open` in `src/cli.ts`: what reaches the opener, including values added through `add`.
3. `store.add` now goes through `importAll`; the ids it assigns haven't changed. The test files and plan checkboxes are routine and can be skimmed.

## Checks
`npm test` passes 16/16 at b57f2da. The project has no lint or type checker set up. I added the summary above to the plan as a `## Review` section (108fe0d). Nothing was pushed.

**Your real `~/.bookmarks.json` was changed:** while testing, the reviewing agent ran `bm add` without `BM_FILE` set and added two entries (ids 2 and 3) to it. It says it removed them straight away and kept only your original entry. Please check that file.