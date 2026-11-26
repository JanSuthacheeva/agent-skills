I fixed two security bugs on `feature/bookmark-share`. Both broke promises the plan makes. All 16 tests now pass at `5174a2e`. The project has no lint or type-check script, so none was run.

## Fixed
- **A shared file could run commands on your machine.** `openUrl` built a shell command with the URL pasted in. A URL like `https://a.dev/?$(touch${IFS}/tmp/x)` survives URL cleanup, and `bm open` would run what's inside it. I reproduced this: the file got created. It now passes the URL to the opener directly, with no shell (`5174a2e`). One side effect: `BM_OPENER` must now be a single command, so something like `firefox --new-tab` no longer works.
- **Any kind of URL was accepted.** `parseWebUrl` let `javascript:` and `file:` URLs through, though the plan allows only `http:` and `https:`. It now rejects everything else (`52ac0a6`). The plan listed a test for a rejected scheme as done, but none existed; I added one.

Each fix came with a test that failed before it. A separate reviewer agent then checked both fixes (uppercase schemes, extra whitespace, URLs starting with `-`) and found no problems.

## Open (your call)
- **Broken import files aren't handled.** I tried each of these:
  - A file that isn't a JSON list, invalid JSON, or a missing file each crash with a stack trace.
  - An entry with no `url` prints `invalid url: undefined`.
  - A title that isn't text, such as `42`, gets saved into your bookmarks as is.

  I suggest making these clean errors with exit code 2, and checking that each title is text before saving. I left this alone because it means new user-facing error messages.
- **`bm add` doesn't check URLs,** and `bm open` opens whatever is saved. The plan only requires checks on import. I'd add the same check to `add`, but that changes what `add` accepts, so I didn't.

## Where to look
1. `src/opener.ts`: the only place the tool starts another program.
2. `src/cli.ts`, the `import` command: the path from reading the file to saving the entries.

The rest (`store.ts`, the error-to-exit-code mapping) is routine and can be skimmed.

I also added this summary to the plan as a `## Review` section (`a9e9d85`). Nothing is pushed.