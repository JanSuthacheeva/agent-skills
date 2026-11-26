I reviewed `feature/bookmark-tags` against its plan (`docs/plans/2026-10-14-bookmark-tags.md`) and fixed four problems, one commit each. All 15 tests pass, and a separate agent checked the fixes and agreed with them.

## Fixed
- **Duplicate tags were saved to the store file.** Running `bm tag 1 work` twice gave `"tags": ["work","work"]`. The plan says tagging again should do nothing. Commit `5f8688e`.
- **Unknown id used the wrong exit code.** `bm tag 9 work` exited 2. The plan and AGENTS.md both say "not found" exits 1. Commit `462fdfb`; its test is in `5b10bf0`.
- **`list --tag` didn't clean up or check the tag.** `list --tag Work` found nothing for a bookmark tagged `work`, and `list --tag 'to do'` exited 0 instead of rejecting the tag. Commit `5b10bf0`.
- **Method name didn't match the plan.** The store method was called `listTagged`; the plan calls it `listByTag`, so I renamed it. Commit `62b9414`.

I also added the tests the plan asked for but the branch didn't have: tagging twice, an unknown id in the store and in the CLI, and `list --tag`.

## Open (not fixed: these change how the CLI behaves, which the plan doesn't cover)
- **`bm list --tag` with no tag**, or an unknown option like `list --foo`, quietly lists every bookmark and exits 0. I'd recommend printing `usage: bm list [--tag <tag>]` and exiting 2.
- **Loose id parsing.** Ids like `0x1`, `1e0` or ` 1 ` are all read as 1. It's harmless for now; if you want it strict, only accept plain digits.
- **Old duplicates stay.** Duplicates written before the fix aren't removed when the file loads. This only matters if you used the branch on a real bookmarks file.

## Where to look
1. `src/store.ts` `tag()`: the only new code that writes to the file (load, change, save).
2. `src/cli.ts` `run()`: how errors map to exit codes, and how `list` reads its options.
3. `src/store.ts` `load()`: files from before tags existed load with an empty tag list. A corrupt file still throws an error, the same as on `main`.

`src/tags.ts`, `src/bookmark.ts` and the tests are routine and can be skimmed.

**Checks:** all 15 tests pass at `62b9414`; the project has no lint or type-check set up. I also added this summary to the plan as a `## Review` section (commit `7b68184`). Nothing has been pushed.