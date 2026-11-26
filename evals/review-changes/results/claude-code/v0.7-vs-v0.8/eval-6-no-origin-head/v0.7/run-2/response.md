I reviewed `feature/bookmark-share` against `origin/main` and found two security holes in the new import/open feature. Both are fixed and committed. There was no `origin/HEAD`, so I picked `origin/main` as the target; local `main` also has the plan commit but is otherwise the same. A separate reviewer re-checked both fixes.

## Fixed
- **Any URL scheme got through `import`.** The plan allows only `http:`/`https:` to be imported, but `parseWebUrl` also accepted `javascript:`, `file:` and `ftp:`. The plan's test for a rejected scheme was missing too. Commit `0548282`.
- **Shell injection on `bm open`.** `openUrl` built a shell command from the URL. A URL in a shared file like `https://a.dev/$(touch$IFS/tmp/x)` passes URL cleanup, and opening it ran the command; I confirmed this by having it create a file. It now starts the opener with the URL as its only argument and no shell, as the plan says, with a test. Commit `23ea061`.

## Open (left for you)
- **A badly formed shared file isn't handled.** A file that isn't a list, a `null` entry, or a missing or unreadable file crashes with a stack trace. A `title` that isn't text, such as an object, gets saved as-is and `list` then prints `[object Object]`. I'd check the file's shape in `import` and reject the whole file with exit 2, the same as for a bad URL. I left it because it means choosing new error messages.
- **`BM_OPENER` can no longer take arguments.** A value like `open -a Firefox` now fails with "ENOENT". `opener.ts` is new on this branch, so nothing already shipped breaks. I'd document this, or point the variable at a wrapper script.
- **`bm add` doesn't check URLs, and `bm open` doesn't check them again.** A locally added `javascript:` URL still reaches the browser opener. It is no longer an injection risk, but I'd add the same check to `add`.

## Where to look
1. `src/cli.ts`, the `import` case: how a shared file's contents are trusted before they are saved (this is where the first open item lives).
2. `src/opener.ts`: the whole security boundary is these few lines.
3. The store changes (`get`, `importAll`) and the tests are routine and can be skimmed.

## Checks
`npm test` passes 15 of 15 at `23ea061`. The project has no lint or type check set up. I also added a `## Review` section to the plan with this summary (`58debf3`). Nothing has been pushed.