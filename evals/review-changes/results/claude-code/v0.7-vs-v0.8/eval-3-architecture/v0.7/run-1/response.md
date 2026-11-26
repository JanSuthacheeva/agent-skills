I found and fixed three problems on `feature/bookmark-tags`; the worst could wipe out all your bookmarks. Each fix has a test that fails without it, and all 17 tests now pass. Nothing has been pushed.

## Fixed
- **Data loss** (`245c3b0`): if the store file was corrupt, `load()` quietly returned an empty list, so the next `bm add` replaced every bookmark with just the new one. I reproduced this from the command line. Now the error surfaces and the file is left untouched.
- **Store bypassed** (`af295bd`): `bm tag` did the tagging itself and saved the file directly, which breaks the AGENTS.md rule that only the store touches the file. That left `BookmarkStore::tag` unused. The store also printed a duplicate-tag warning straight to `console` instead of going through `Output`. The CLI now calls `store.tag`, and re-adding a tag the bookmark already has does nothing, silently. I also added the duplicate-tag and unknown-id tests the plan asked for, which were missing.
- **Bad arguments accepted** (`a43bf4f`):
  - `bm tag '' work` said `no bookmark 0` and exited 1. The plan says a non-numeric id is a usage error with exit 2.
  - `0x1` and `1e0` were accepted as ids.
  - `bm list --tag` with no tag listed every bookmark.

  All of these are now usage errors with exit 2, and I added the new `list` error to the plan.

## Open
- **A corrupt file now crashes with a raw `SyntaxError` stack trace and exit 1.** That is how `main` already behaved, so it isn't a regression, but it's rough, and exit 1 already means "not found". I'd add a `StoreCorruptError` that prints something like `cannot read <path>` with its own exit code. Picking that code is your call, so I didn't change it.

## Where to look
1. `src/store.ts`, from `load()` to `save()`: make sure a failed read can never lead to a save.
2. `src/cli.ts`, the `tag` and `list` cases in `dispatch()`: the argument checks.

The rest (`tags.ts`, `bookmark.ts`, the tests) is routine and can be skimmed.

A separate agent reviewed the three fixes and found no regressions; the only thing it flagged was the open item above. I also wrote this summary into the plan as a `## Review` section (`3b5d264`). The project has no lint or type-check script, so the tests are the only automated check.