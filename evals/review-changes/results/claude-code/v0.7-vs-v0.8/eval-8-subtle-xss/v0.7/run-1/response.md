I found one XSS bug in the HTML export and fixed it. A second problem needs your decision.

**Fixed** (commit `dc770da`)
- **Exported pages could run script.** `escapeHtml` didn't escape quotes, even though titles go into a `title="…"` attribute. URLs were written into `href` without escaping. `bm import` doesn't check titles, so a shared file with the title `x" autofocus onfocus="alert(1)` added an event handler to the exported page. I reproduced this before fixing it. Quotes in titles and URLs are now escaped, and four new tests fail without the fix. A separate agent checked the fix and found it complete. It also confirmed that normal URLs, such as ones with `&` in the query, still come out correctly.

**Open: your call**
- **`bm add` accepts any URL.** I ran `bm add javascript:alert(1)` and it was stored and exported as a clickable `javascript:` link; `bm open` would also pass it to the browser opener. Escaping can't stop this. This gap was already on `main`, but the export makes it worse because the page is meant to be shared. I recommend calling `parseWebUrl` in `add`, as `import` already does. I didn't make that change because `add` would start rejecting URLs it accepts today.

**Where to look**
1. `renderPage` in `src/export.ts`: every value written into the page has to go through `escapeHtml`.
2. The `add` and `import` commands in `src/cli.ts`: only `import` checks URLs.

The CLI wiring for `export` is routine and can be skimmed.

**Checks:** all 23 tests pass at `dc770da`. The project has no lint or type check set up. I added a `## Review` section to the plan with this summary (commit `82dd5af`). Nothing has been pushed.