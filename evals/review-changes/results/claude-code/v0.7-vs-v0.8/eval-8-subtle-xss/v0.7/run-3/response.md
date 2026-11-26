I found an HTML/script injection bug in the export page and fixed it. Tests now pass 24/24; the project has no lint or type check. Nothing is pushed.

**Your real bookmarks file was briefly changed.** I made a mistake: I ran the CLI once without `BM_FILE`, so it added 3 test entries to your real `~/.bookmarks.json`. I removed them right away. The file is back to the two entries it had before (ids 2 and 3), and every later run used a temp file.

**Fixed**
- **Script injection in the exported page** (d8b01b7):
  - `escapeHtml` didn't escape `"`, so a title from a shared import file like `x" onmouseover="alert(document.cookie)` broke out of the `title=` attribute. The plan says every title is escaped.
  - The URL went into `href=` unescaped, so `bm add 'javascript:alert(1)'` became a link that runs script.
  - I reproduced both with the CLI and they showed up in the page. Now quotes are escaped, the URL is escaped too, and only `http:`/`https:` URLs become links; anything else is listed as plain text.
  - I updated the plan to match, and a separate agent checked the fix with unusual inputs (odd casing, control characters, `data:` URLs, single quotes) and found nothing.
- **Missing test** (4630a9b): the plan's `usage: bm export <file>` error had no test; it has one now.

**Open — your call**
- **`bm export <store file>` wipes every bookmark.** It writes HTML over the store, and the next command crashes on reading it. I confirmed this with a temp store. I recommend refusing when the target is the store file. I didn't fix it because it adds a new error message to the command.
- **`bm add` doesn't check the URL scheme, but `import` does.** This was already the case on `main`; the export just made it matter. I recommend having `add` reject non-web URLs the same way `import` does.
- **Exporting to a path that can't be written prints a stack trace.** `import` with an unreadable file does the same, so I left it.

**Where to look**
1. `src/export.ts` `renderPage`: how title and URL get into the attributes. This is where the real risk is.
2. `src/cli.ts` `export` case: how the target file is written, including the store-overwrite case above.

The rest — the plan text and the CLI wiring — is routine and can be skimmed.

I also added a `## Review` section to `docs/plans/2026-11-25-bookmark-export.md` with this summary (8ee0714).