I found and fixed one bug on this branch. The bigger problem is a shell injection in `feature/bookmark-share`, which this branch is built on. I reproduced it but didn't fix it there.

## Fixed
- **Removing an id that doesn't exist reported success** (`f51bfa0`). `bm remove 9` printed `removed 9`, exited 0 and rewrote the file. The plan says it should print `no bookmark 9`, exit 1 and leave the file alone. The store now throws `BookmarkNotFoundError` before it saves anything. I added the store tests the plan lists, plus a command-line test for an unknown id; two of them fail without the fix. A separate agent checked the fix and found no problems.

## Open
- **Must fix, on `feature/bookmark-share`: shell injection in `bm open`.** `src/opener.ts:8` runs `execSync(\`${opener} "${url}"\`)`, so the URL goes through a shell. URL clean-up encodes the quotes, but `$(...)` gets through and still runs. A shared file containing `https://x.dev/$(touch$IFS/tmp/bmprobe/pwned)` created that file when opened. Use `execFileSync(opener, [url])` instead.
- **Same branch: any URL scheme is accepted.** `parseWebUrl` (`src/urls.ts:11`) lets `file:` and `javascript:` URLs through, though the sharing plan allows only http and https. Fix both on that branch and rebase this one onto it.
- **Minor: an empty id gives the wrong error.** `bm remove ""` (and `bm open ""`) read the id as 0, so they print `no bookmark 0` with exit 1 instead of the usage error with exit 2. Both commands share this parsing, so I'd fix them together in a later change.

## Where to look
1. `src/opener.ts` `openUrl`, together with `src/urls.ts` `parseWebUrl`: an untrusted URL going from an imported file to a shell.
2. `src/store.ts` `remove()`: nothing may be saved unless the bookmark was found.

The command-line wiring and tests for `remove` are routine and can be skimmed.

## Checks
- All 18 tests pass at `356783f`. The project has no lint or type-check setup, so only the tests ran.
- The security review ran on this branch's changes only and found nothing new in them; the two base-branch problems above came from it.
- The plan now ends with a `## Review` section, committed in `356783f`. Nothing was pushed.
- **Your real bookmarks file was touched.** The agent that checked my fix ran the command line once without `BM_FILE` set, which added one entry to `~/.bookmarks.json`. It says it removed that entry and checked the file matches what was there before (ids 2 and 3). You may want to glance at the file.