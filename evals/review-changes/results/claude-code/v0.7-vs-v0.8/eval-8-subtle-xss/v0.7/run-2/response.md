I reviewed `feature/bookmark-export` against `main` and found a real XSS hole in the exported page. I fixed it, added a missing test, and an independent agent checked the fix. All 23 tests pass; the project has no lint or type check set up.

**Fixed**
- **XSS through bookmark titles (969f6ad).** `escapeHtml` didn't escape quotes, and the title goes inside `title="…"`. A shared bookmark titled `" onmouseover="alert(1)` added a working event handler to the link; I reproduced this. The URL was also written into `href` without escaping, and `bm add` saves URLs exactly as typed. Both are now escaped, quotes included, and three new tests fail without the fix. I updated the plan to match.
- **Missing test (73b814d).** Nothing tested `bm export` without a file, which should print the usage line and exit 2. The test is added, and I checked it fails when that check is removed.

**Open, for you to decide**
- **`bm add` accepts any URL.** After `bm add 'javascript:alert(1)'`, the exported page has a clickable `javascript:` link. Escaping can't block this because the URL contains nothing to escape. This was already true before your branch, but export now puts it in a page people share. I'd do two things: check URLs with `parseWebUrl` in `add`, as `import` already does, and show non-http(s) URLs as plain text in `renderPage` so bookmarks already saved are covered too. I didn't make either change because both change what users see.
- **A failed write crashes the CLI.** If the export file can't be written (missing folder, no permission), you get a stack trace instead of a message. `import` already does the same when it can't read a file, so it's minor.

**Where to look:** first `renderPage` in `src/export.ts`, checking that every value placed in the HTML goes through `escapeHtml`. Then compare `add` and `import` in `src/cli.ts`, since only `import` validates URLs. The rest of the CLI wiring is routine.

The review is also recorded as a `## Review` section in `docs/plans/2026-11-25-bookmark-export.md` (c764fdf). Nothing was pushed.

**One mistake on my side:** while testing, I ran `bm add` once without setting `BM_FILE`, so it wrote to your real `~/.bookmarks.json`. When I checked, my test entry wasn't in the file: something else had rewritten it moments later, so there was nothing to remove. You may want to check that the file contains what you expect. Every run after that used a temp file.