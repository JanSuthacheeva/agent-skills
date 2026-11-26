I found four problems on `feature/bookmark-tags` and fixed them in three commits. All 15 tests pass, and a separate reviewer agent rechecked the fixes and found no issues. Nothing has been pushed.

## Fixed
- **Duplicate tags were saved:** tagging bookmark 1 with `work` twice stored `["work","work"]`. The plan says re-tagging should do nothing, and now it does (`879715b`).
- **Wrong exit code for a missing bookmark:** `bm tag 9 work` exited 2 instead of 1. Both the plan and AGENTS.md say 1 means "not found" (`29b99f6`).
- **`list --tag` didn't clean up the tag:** it skipped `normalizeTag` (the lowercase-and-trim step), so `list --tag Work` found nothing and `list --tag "to do"` exited 0 instead of rejecting the tag (`29b99f6`).
- **Method name didn't match the plan:** `listTagged` is now `listByTag` (`abc6f69`).

Each fix comes with a test that fails without it. Two required tests the branch was missing are now added: tagging twice and an unknown id.

## Open (I didn't change these because they alter command-line behaviour)
- **`bm list --tag` with no value** silently lists every bookmark. I'd make it print a usage error and exit 2.
- **`bm tag "" work`** treats the empty id as 0 and prints `no bookmark 0` (exit 1) instead of the usage message. I'd reject an empty id in the CLI.

## Where to look
1. `tag()` in `src/store.ts`: the only code that writes the file (load, skip duplicates, save).
2. `run()` in `src/cli.ts`: how errors become exit codes.
3. The `list` case in `src/cli.ts`: how `--tag` is read.

`src/tags.ts`, `src/bookmark.ts` and `load()` filling in an empty tag list for older files are routine.

## Checks
- Tests pass at `abc6f69`. The project has no lint or type checker, so neither was run.
- I added this summary to the plan as a `## Review` section (`1ae62d8`).