I reviewed `feature/bookmark-tags` against `main` and its plan (`docs/plans/2026-10-14-bookmark-tags.md`) and fixed three problems. I reproduced each one by running the CLI against a temp store file, then wrote a failing test before fixing it. `npm test` now passes 16 of 16, and the add, tag and `list --tag` flow behaves as the plan says. The repo has no lint or type checker set up, so neither was run. The `/commit` skill isn't available in this session, so I committed with plain git in the branch's `bm: ...` style. Nothing is pushed.

## Fixed

- **A corrupt store file was wiped:** `load()` caught JSON parse errors and returned `[]`. A truncated `.bookmarks.json` followed by `bm add` replaced every bookmark with just the new one. It now throws again, as it does on `main`. - `2664011`
- **The CLI bypassed the store:** `bm tag` loaded the bookmarks, changed them and called `store.save` itself, so `BookmarkStore.tag` was never called outside tests. `store.tag` also printed a `console.warn` on a duplicate tag, which is the store doing output, and the plan says a duplicate should do nothing. The CLI now calls `store.tag`, and the warning is gone. I also added the tests the plan asks for: duplicate tag, unknown id, and non-numeric id. - `646145a`
- **`list --tag` checked the tag only when bookmarks existed:** `bm list --tag "to do"` exited 0 on an empty store but 2 on a non-empty one, because the tag was checked inside the filter. It is now checked once, in the CLI, as the plan's call chain says. - `9e12962`

A second agent that hadn't seen the fixes reviewed the three commits. The second and third are fine. It had one objection to the first, listed below.

## Open

- **A corrupt file still ends in a Node stack trace:** the data is safe now, but the parse error isn't turned into a message and exit code. `AGENTS.md` says the CLI should map errors that way. JSON that isn't an array, such as `{}`, also crashes with a `TypeError`. **Recommendation:** have `load()` throw a `CorruptStoreError` (bad JSON or not an array) and have `run()` print something like `store file is corrupt: <path>`. I left it because it's new user-visible output and the plan doesn't cover it.
- **`bm list --tag` with no value, or `bm list --anything`, quietly lists every bookmark.** **Recommendation:** make these a usage error with exit 2. I left it because it changes command behaviour the plan doesn't cover.

## Where to look

1. `src/store.ts` `load()` to `save()`: what happens to a corrupt or non-array file. This is the only place that touches stored data.
2. `src/cli.ts` `run()` catch block: which errors are mapped and which get through as stack traces.
3. `src/cli.ts` `list` case: how `--tag` is parsed.

`src/tags.ts`, `src/bookmark.ts` and the tests are routine and can be skimmed.