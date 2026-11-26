I reviewed `feature/bookmark-share` against `main` and the plan, and fixed two things. All 18 tests pass at `19ec3e7`. The project has no lint or type checks. Nothing was pushed.

## Fixed
- **Missing tests:** two plan behaviours had no tests: importing a file with a non-web URL like `file:///etc/passwd`, and running `bm import` with no file. Both already behaved correctly; the tests now cover them (`31a76b0`).
- **Wrong error for some ids in `bm open`:** `bm open ''`, `' '` or `-1` printed `no bookmark 0` and exited with 1. A bad id should give the usage error and exit with 2. The id now has to be a plain number (`19ec3e7`). A separate agent checked this fix; it now rejects ids like `+1` or `0x1`.

## Open (I recommend handling these, but each one changes stored data or what the user sees)
- **Broken shared file crashes `import`:** the command dies with a stack trace and exit 1 if the file isn't valid JSON, isn't a list, has a `null` entry, or doesn't exist. Nothing gets written. Recommend a proper error: `invalid import file: <file>`, exit 2.
- **Wrong title type gets stored:** if a shared file's `title` isn't text, it's saved as-is, and `list` prints `[object Object]`. Recommend rejecting the entry or using the URL as the title.
- **Terminal control codes pass through:** imported titles, and the raw URL in the `invalid url:` message, are printed unfiltered. A shared file can use this to inject terminal control codes. Recommend stripping them before printing.
- **Missing or failing browser opener crashes `open`:** for example, `xdg-open` isn't installed. Recommend a clear error message.
- **Minor:** `bm add` doesn't check URLs, and `open` will open anything already in the store. Importing the same file twice adds every entry twice.

## Where to look
1. `src/cli.ts`, the `import` case: what an untrusted file can put into your store.
2. `src/opener.ts` and `src/urls.ts`: the URL is always http(s) and never goes through a shell. I tested this and it holds.

The rest is routine: `add` now goes through `importAll`, and error handling sits in `run`.

## Checks
- **Security review:** it ran and found no vulnerabilities. It noted the control-code issue but its rules don't count it as one.
- **Plan:** I added this summary as a `## Review` section in `docs/plans/2026-11-20-bookmark-share.md` (`55e5eb1`).