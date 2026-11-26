The HTML export had an XSS bug, and I've fixed it. One related security gap is still open because closing it changes how a command behaves, so it needs your decision.

**Fixed**
- **XSS in the exported page.** Titles were escaped for `& < >` but not for quotes, and URLs weren't escaped at all. A title in a shared file like `x" onmouseover="alert(1)` added a script handler to the page. Rendering the page with that title showed the handler in the output. `escapeHtml` now also escapes `"` and `'`, and the URL goes through it too. I wrote the tests first and watched them fail before the fix (da11878).
- **Missing test.** The plan says `bm export` with no file prints a usage message and exits 2, but nothing tested that. I added the test and checked that it fails when the check is removed (4a12925).

**Open**
- **`javascript:` links.** `bm add` saves URLs without the check that `import` uses, so `bm add 'javascript:alert(1)'` becomes a clickable script link in the export. Escaping can't stop this. You can fix it in either of two places:
  - Make `add` check the URL the way `import` does (exit 2). I recommend this.
  - Have `renderPage` drop or disarm URLs that aren't http(s).
- **Failed writes.** If `export` can't write the file (bad path), it crashes with a stack trace. `import` does the same with a missing file, so I left it alone.

**Where to look**
1. `src/export.ts` `renderPage`: everything that goes into the HTML.
2. `src/cli.ts`: compare `add` and `import` to see which one checks URLs.

The CLI wiring and the tests are routine and can be skimmed.

**Checks**
- `npm test` passes, 23 of 23, at 4a12925. The project has no lint or type check set up.
- `/security-review` ran against the original branch head (abe0752) and found the same XSS. It didn't report it because my fix had landed by the time it finished, so it didn't check my new commits. It mentions two commits it didn't recognise: those are mine.
- A separate agent reviewed the fix and confirmed it closes the problem.

I also added a `## Review` section to `docs/plans/2026-11-25-bookmark-export.md` (803b996). Nothing has been pushed.