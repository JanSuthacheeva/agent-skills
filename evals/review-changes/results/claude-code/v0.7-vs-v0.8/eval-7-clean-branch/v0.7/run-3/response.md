I reviewed `feature/bookmark-share` against its plan and fixed one problem. Three smaller issues need a decision from you. All tests pass (22/22).

## Fixed
- **`bm import` broke on a badly formed shared file.** A file that wasn't valid JSON, wasn't a list, had a `null` entry or couldn't be read crashed with a stack trace and exit 1. A title that wasn't text (an object, say) was saved into the store and `list` showed it as `[object Object]`. I reproduced all of these from the command line. Now each prints `invalid file: <reason>`, exits 2 and imports nothing. The check lives in a new `src/share.ts`, and I added the new error to the plan. Commit `ab5ad73`.
- A separate agent checked that fix and found it also rejected `"title": null`, which used to fall back to the URL. I restored the fallback and added a test. Commit `8f8fdc6`. That follow-up wasn't independently reviewed.

## Open (each changes how the tool behaves for users, so I left it to you)
1. **Imported titles can contain terminal control codes.** A shared file's titles go into the store as-is, and `list` prints them raw. I showed a shared file can recolour the terminal or add fake lines to the `list` output. I'd recommend rejecting control characters in titles during import.
2. **`open` launches any stored URL.** Only `import` checks URLs, so something added with `bm add` (a `file:` URL, or a value starting with `-`) goes straight to the system's `open`/`xdg-open`. I'd recommend checking the URL in `open` itself, or in `add` as well.
3. **A missing or broken opener crashes with a stack trace.** This happens with a bad `BM_OPENER`, for example. I'd recommend printing a message and exiting 1.

## Where to look
1. `parseSharedFile` in `src/share.ts`: what a shared file is trusted to contain.
2. `src/opener.ts`: the URL is passed as a single argument and never goes through a shell. There's a test for this and it's correct.
3. How `run` in `src/cli.ts` turns errors into messages and exit codes.

You can skim `get` and `importAll` in `src/store.ts`; they're routine.

## Checks
Tests pass at `8f8fdc6`. The project has no lint or type check set up. I added this summary to the plan as a `## Review` section (`41a69d0`). Nothing is pushed.