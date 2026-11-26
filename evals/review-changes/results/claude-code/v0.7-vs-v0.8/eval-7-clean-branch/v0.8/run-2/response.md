I reviewed `feature/bookmark-share` against `main` and fixed two problems, both in `bm import` and `bm open`. All 27 tests pass, up from 15; the new ones cover the fixes and the error paths the plan lists. Nothing is pushed.

**Fixed**
- **Bad data from shared files reached the store and the terminal (ce2e800).** A file entry like `{"title": {"x":1}}` was saved into the store as an object, though titles should be text. Text with escape codes or line breaks was also printed as-is by `bm list` and by the `invalid url:` error, so a shared file could change what your terminal shows. I reproduced both from the command line. Now a title that isn't text falls back to the URL, and those invisible characters are removed.
- **`bm open` with a bad id (9231597).** `bm open ''`, `bm open ' '` and `bm open -1` said "no bookmark" and exited 1, which is the not-found code. They now print the usage line and exit 2, the code for bad input.

A second agent reviewed both fixes and confirmed them. It found the two small gaps listed under the last open point.

**Open, for you to decide**
- **Broken import files crash.** A file that isn't valid JSON, is missing, isn't a list or has a `null` entry crashes with a stack trace and exit 1. So does a failing browser launcher. I'd add one error that prints `invalid file: <path>` and exits 2, plus a short message when the launcher fails. I didn't, because that adds new messages users will see.
- **Importing twice duplicates every bookmark.** Decide whether `import` should skip URLs that are already stored.
- **Small gaps in the fix:**
  - Right-to-left override characters (U+202E) and line separators in titles are not removed.
  - A title made only of escape codes ends up blank instead of falling back to the URL.
- **`bm add` accepts any URL**, and `open` will then launch it. That's your own input, but it's looser than `import`, which only takes http and https.

**Where to look**
1. `src/cli.ts`, the `import` branch and `stripControl()`: everything from the shared file passes through here before it is stored.
2. `src/opener.ts` together with `open` in `src/cli.ts`: what reaches the browser launcher. It runs without a shell and gets the URL as one argument.
3. `src/store.ts`, `importAll()`: `add` now goes through it too. It behaves the same as before.

`src/urls.ts` and the tests are routine and can be skimmed.

**Checks:** tests pass at 9231597. The project has no lint or type check set up. The `/security-review` command ran and reported nothing at or above its confidence threshold; below it, it flagged the same escape-code issue fixed above. I also added this summary as a `## Review` section at the end of `docs/plans/2026-11-20-bookmark-share.md` (commit e9d0028).