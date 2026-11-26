I found two security bugs on `feature/bookmark-share`, proved both, and fixed both. Each fix has a test that fails without it.

**Fixed**
- **Any URL scheme got through:** `parseWebUrl` never checked the scheme, so a shared file with `javascript:` or `file:` URLs imported with exit 0. The plan requires `http:`/`https:` only, and now only those are accepted (`8901d90`).
- **Command injection on `bm open`:** `openUrl` ran the opener through a shell. Importing a shared file with the URL `https://a.dev/$(touch$IFS'PWNED')` and then opening it actually created a `PWNED` file. It now uses `execFileSync` with the URL as the only argument, as the plan says (`5ead330`).

A fresh agent reviewed both fixes and found no problems in them. It tried capitalised schemes like `HTTPS:` and `JaVaScript:`, URLs with spaces and quotes, and reverting each fix to make sure its test fails.

**Side effect from the reviewer agent:** while testing, it ran `bm add` without `BM_FILE` set, which wrote to your real `~/.bookmarks.json`. It says it removed the entry it added. The file now holds ids 2 and 3, but I can't confirm that matches what was there before, so please check it.

**Open (not fixed, because each changes error messages or behaviour you'd see)**
- **Malformed import file:** `bm import` on a missing file, invalid JSON or a non-array crashes with a stack trace and exit 1. I'd recommend a clear message and exit 2.
- **Non-string titles:** `bm import` saves a non-string `title` as-is, so an object can end up in your bookmarks file. I'd recommend rejecting it or using the URL as the title.
- **`bm add` doesn't check URLs:** any URL can be stored that way, including one starting with `-`, which `bm open` hands to the opener and which it may read as an option. I'd recommend calling `parseWebUrl` in `add`.
- **`BM_OPENER` changed:** it is now a single command name, so a value with arguments like `open -a Firefox` no longer works. That matches the plan's wording, but users would notice.

**Where to look**
1. `src/opener.ts` and `src/urls.ts`: the two security fixes, a few lines each.
2. The `import` case in `src/cli.ts`: what an untrusted file can do (the open items above).
3. `importAll` in `src/store.ts`: `add` now goes through it. It's routine and you can skim it.

**Checks:** `npm test` passes 16/16 at `53e6035`. The project has no lint or type-check scripts. The security review tool didn't run because the repo has no `origin/HEAD`. The plan now ends with a `## Review` section holding this summary. Nothing was pushed.