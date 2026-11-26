I found two security holes on `feature/bookmark-share` and fixed both. Together they let a shared bookmark file run commands on your machine. All 17 tests pass at `e97c4e6`.

**Fixed**
- **URLs with other schemes were accepted** (`ae6cb72`). `parseWebUrl` let through `javascript:` and `file:` URLs, although the plan allows only http and https. I confirmed it by running `parseWebUrl` on both. It now rejects them, and new tests in `test/urls.test.ts` and `test/cli.share.test.ts` cover this.
- **`bm open` passed the URL through a shell** (`e97c4e6`). A shared file containing `https://a.dev/$(touch$IFS/tmp/bm-pwned)` imported fine, and `bm open 1` then created `/tmp/bm-pwned`. `openUrl` now runs the opener with the URL as its only argument and no shell. A new `test/opener.test.ts` checks that nothing gets executed, and the same exploit no longer works.

A fresh agent reviewed both fixes. It found that each closes its hole, and that each fix's tests fail without it.

**Open (left for you to decide)**
- **`bm add` still doesn't check URLs.** So `bm open` can pass a non-web URL, or one starting with `-` that the opener would read as an option. I'd have `open` (or `add`) run the URL through `parseWebUrl`, but that changes what users see, so I left it.
- **`BM_OPENER` must now be a single program.** A value with arguments, like `open -a Firefox`, no longer works. That follows from the plan's "without a shell", but it may need a docs note.
- **Bad import files crash with a stack trace.** That covers an unreadable file, invalid JSON, or JSON that isn't a list. An entry with no `url` prints `invalid url: undefined`. Nothing gets saved in either case, but I'd add a proper error that exits with code 2.
- **`bm open ""`** prints `no bookmark 0` instead of the usage message. Minor.

**Where to look:** `src/opener.ts`, then `src/urls.ts`, then the `open` case in `src/cli.ts`. That's the path untrusted data takes to a running program. The store and test changes are routine.

**Checks:** The project has no lint or type-check scripts, so the tests are the only check. `/security-review` didn't run: the repo has no `origin/HEAD`, which the command needs. I added this summary to the plan as a `## Review` section (`c50b3ef`). Nothing was pushed.