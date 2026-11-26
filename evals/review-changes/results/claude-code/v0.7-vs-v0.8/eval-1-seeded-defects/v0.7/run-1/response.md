I reviewed `feature/bookmark-tags` against the plan and fixed four bugs, each in its own commit with a test written first. The branch's original 10 tests had all passed, but none of them covered these cases. A separate agent then reviewed the four fixes: all of them work, and each new test fails without its fix. Nothing was pushed.

## Fixed
- **Tagging twice stored the tag twice.** Running `bm tag 1 work` and then `bm tag 1 Work` saved `["work","work"]` to the file. The plan says a repeat tag does nothing, and now it does (`6a9508d`). I also added the store tests for a duplicate tag and an unknown id, which the plan's task list said existed but didn't.
- **Wrong exit code for an unknown bookmark.** `bm tag 9 work` exited with 2; the plan and AGENTS.md both say 1 (`e6e6ec0`).
- **`list --tag` didn't clean up the tag first.** `--tag Work` found nothing, and `--tag 'to do'` exited 0 instead of printing `invalid tag: to do` and exiting 2. The same commit renames the store method `listTagged` to `listByTag`, the name the plan uses (`79f5f96`).
- **Bad ids were accepted.** `bm tag "" work` printed `no bookmark 0`, and `bm tag 0x1 work` tagged bookmark 1. Ids must now be plain digits; anything else prints the usage line and exits 2 (`2d5ea3e`).

## Open
- `bm list --tag` with no tag after it lists every bookmark and exits 0. The plan doesn't cover this. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2. I didn't change it because it changes what users see.

## Where to look
1. In `src/store.ts`, follow `load()` → `tag()` → `save()` to see how files written before tags existed are read and written back.
2. In `src/cli.ts`, `run()` decides the message and exit code for each error.
3. In `src/cli.ts`, the `tag` and `list` cases read the command-line arguments.

`src/tags.ts` and the tests are routine and can be skimmed.

## Checks
All 16 tests pass at `2d5ea3e`. The project has no lint or type-check step. I added this summary to the plan as a `## Review` section and committed it (`a770ae8`).