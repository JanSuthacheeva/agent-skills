I found and fixed one bug on the branch: the HTML export was open to cross-site scripting (XSS) through bookmark titles. A second problem, in `bm add`, is still open because fixing it changes how the command behaves. All 22 tests pass.

**Fixed**
- **Script injection through titles in the exported page** (cea8e52). `escapeHtml` escaped `&`, `<` and `>` but not quotes. A title from a shared file such as `x" onmouseover="alert(1)` broke out of the `title="…"` attribute and added an event handler to the link. I confirmed this by rendering that title. `/security-review` found the same bug on its own. Quotes are now escaped, and the URL in `href` is escaped too. I added three tests, which fail without the fix. A fresh agent reviewed the fix commit and found nothing wrong.

**Open**
- **`bm add` accepts any URL.** Unlike `import`, it doesn't run `parseWebUrl`, so `bm add 'javascript:alert(1)'` is saved and then exported as a clickable `javascript:` link. Only you can type that URL, so the risk is low, but the exported page is meant to be shared. I recommend validating in `add` the same way `import` does. I didn't change it because it changes what the command accepts.

**Something I did by mistake:** while proving the `add` issue I ran the CLI without `BM_FILE` set, so it wrote a test bookmark (id 4, `javascript:alert(1)`) into your real `~/.bookmarks.json`. I removed only that entry. Your two existing bookmarks (ids 2 and 3) are unchanged.

**Where to look:** `src/export.ts` `renderPage`, because it's where stored values go into the HTML. The `export` case in `src/cli.ts` is routine.

**Checks:** `npm test` passes 22/22 at cea8e52. The project has no lint or type check set up. I also added this review as a `## Review` section to `docs/plans/2026-11-25-bookmark-export.md` (94c0901). Nothing was pushed.