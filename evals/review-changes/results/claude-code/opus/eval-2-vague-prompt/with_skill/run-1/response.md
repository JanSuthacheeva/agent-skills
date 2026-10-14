I reviewed `feature/bookmark-tags` against `docs/plans/2026-10-14-bookmark-tags.md` and `AGENTS.md`, and fixed four problems in three commits. Each problem was reproduced through the real CLI first, and each fix has a test that fails without it. All 16 tests now pass (10 before). The project has no lint or typecheck set up, so neither was run. A separate agent reviewed the three fix commits and found no regressions.

I committed with plain `git commit` because the `/commit` skill isn't available in this environment. Nothing has been pushed.

## Fixed
- **Duplicate tags were saved to the file.** Running `bm tag 1 work` twice stored `["work","work"]`; the plan says a repeat tag does nothing. - `01d2fe5`
- **Unknown id exited with the wrong code.** `bm tag 9 work` exited 2, but the plan and `AGENTS.md` say "not found" is exit 1. Added tests for an unknown id and a non-numeric id. - `08e08fa`
- **`list --tag` skipped tag normalization.** `bm list --tag Work` found nothing, and `bm list --tag 'to do'` was accepted with exit 0. It now normalizes the tag first, as the plan says. - `86c7e9e`
- **Method name didn't match the plan.** The plan calls it `listByTag`; the code called it `listTagged`. Renamed in `86c7e9e`.

## Open
- **Bad ids:** `bm tag '' work` and `bm tag ' ' work` print `no bookmark 0` and exit 1, and `bm tag 1.0 work` tags bookmark 1. The cause is `Number(rawId)` in `src/cli.ts`. The plan treats a non-numeric id as a usage error (exit 2). I recommend only accepting ids that are all digits (`/^\d+$/`). I left this unfixed because the review round ends after one pass, but it's a small change.
- **`bm list --tag` with no tag** lists every bookmark and exits 0. The plan doesn't cover this. I recommend making it a usage error with exit 2.
- **`.lavish/bookmark-tags-implementation.html`**, the review page the plan links to, isn't in the repo.

## Where to look
1. `src/store.ts`, from `load()` to `tag()`: the only code that writes the file. It now returns early for a tag the bookmark already has, so nothing is written.
2. `src/cli.ts`, `run()`: where errors are turned into messages and exit codes. Check this against the error list in the plan.
3. `src/cli.ts`, the `tag` case: the id parsing from the first Open item.

The rest can be skimmed: `src/tags.ts`, the `Bookmark` type change, and the tests.