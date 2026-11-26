I reviewed `feature/bookmark-share` against `main` and the bookmark-sharing plan, and fixed two security holes. A shared bookmark file could run shell commands on your machine, and the import let through URLs the plan forbids. All 16 tests pass at `81eb0eb`; the project has no lint or type-check script.

## Fixed
- **`bm open` ran shell commands from imported URLs.** The URL was dropped into a shell command line. I imported `https://a.dev/?$(touch${IFS}pwned)` in a temp dir, ran `bm open 1`, and the `pwned` file was created. `src/opener.ts` now passes the URL as the only argument, without a shell. Commit `81eb0eb`.
- **Import accepted any URL scheme.** `javascript:`, `file:` and `ftp:` URLs were all imported, though the plan allows only `http:` and `https:`. Commit `e3cfacc`.

Each fix has a test that fails without it. A separate agent reviewed both fixes, confirmed they hold, and tried variants (uppercase schemes, `data:`, `blob:`, backticks, quotes).

**Behaviour change:** `BM_OPENER` must now be a single program path. A value with arguments, like `firefox --new-tab`, now fails. This matches the plan's "URL as its only argument, without a shell".

## Open (left for you: each needs new error messages or changes existing behaviour)
1. **`bm add` doesn't check URLs, so `bm open` still opens whatever is stored.** This is the most important one. After `bm add 'file:///etc/passwd'` or `bm add '-a Calculator'`, `bm open` passes the value to the opener. A value starting with `-` is read as an option. I'd call `parseWebUrl` in `add` and also in `open`, to cover a hand-edited bookmarks file.
2. **Malformed shared files crash with a stack trace and exit 1.** This happens for a missing file, invalid JSON, a non-array, or `[null]`. Your `AGENTS.md` says bad input exits 2, so I'd add an error class that prints a message and exits 2.
3. **Titles aren't type-checked.** `"title": {"x":1}` gets saved, and `list` then prints `[object Object]`. I'd require a string.
4. **A missing or failing opener crashes `bm open` with a stack trace.** This was already the case before the branch.
5. **Importing the same file twice adds its entries twice.** You need to decide whether that's acceptable.

## Where to look
1. `src/opener.ts`, the whole file (it's short).
2. The `import` case in `src/cli.ts`: everything it reads comes from someone else's file.
3. `src/urls.ts`.

The store changes (`get`, `importAll`, and `add` now going through `importAll`) are routine and can be skimmed.

I also wrote this summary into the plan as a `## Review` section (commit `1699ed1`). Nothing was pushed.