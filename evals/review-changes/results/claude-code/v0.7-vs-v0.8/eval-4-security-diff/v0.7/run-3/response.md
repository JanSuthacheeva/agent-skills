I found two security bugs on `feature/bookmark-share` and fixed both. `npm test` passes, 15 of 15. The project has no lint or type check to run.

## Fixed
- **`bm open` could run shell commands** (`src/opener.ts`). `openUrl` put the URL into a shell command. A valid `https:` URL in a shared file, such as `https://a.dev/$(touch$IFS/tmp/x)`, ran that command when opened. I reproduced it before fixing. It now uses `execFileSync(opener, [url])`, so no shell is involved. Commit `08658da`, with a test that uses a stand-in opener.
- **`parseWebUrl` accepted any scheme** (`src/urls.ts`), including `javascript:` and `file:`. The plan allows only `http:` and `https:`. Commit `186f684`, with a test.

A second agent reviewed both fixes and found them sound. Both new tests fail without the fixes.

## Open (left for you to decide, since they change what users see)
- **`bm add` does not check URLs.** It stores `javascript:` or `file:` URLs, and `bm open` then passes them to the browser. Bookmarks saved before this branch are not checked either. I recommend calling `parseWebUrl` in `add`, and in `open` before calling the opener.
- **`bm import` handles bad files poorly.** A missing file, invalid JSON or a file that isn't a list crashes with a stack trace. An entry without a `url` prints `invalid url: undefined`, and `title` is never checked. I recommend a new error class for bad import files, shown as an error message with exit code 2.
- **`BM_OPENER` can't include arguments any more.** Something like `firefox --private` now fails because there is no shell to split it. This matches the plan's wording, but it is worth mentioning in the merge request.

## Where to look
1. `src/opener.ts`: the only place a URL is handed to another program.
2. The `import` case in `src/cli.ts`: everything read from the shared file is untrusted.
3. The `add` case in `src/cli.ts`: unlike `import`, it stores URLs without checking them.

`get` and `importAll` in `src/store.ts` are routine and can be skimmed.

I also added this summary to the plan as a `## Review` section (commit `e16447a`). Nothing has been pushed.