I reviewed `feature/bookmark-tags` against its plan and `AGENTS.md` and found three bugs, all confirmed by running the CLI against a temp store. I fixed each one with a test that fails without the fix. All 15 tests pass now; there's no lint or type-check setup in the repo, so tests were the only check I could run. A separate agent reviewed the three fix commits and found no problems.

## Fixed
- **Duplicate tags were saved:** running `bm tag 1 work` and then `bm tag 1 Work` stored `["work","work"]`. The plan says re-adding a tag should do nothing. Commit `d64dd63`.
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited 2. The plan and `AGENTS.md` say "not found" exits 1. Commit `4d83593`.
- **`list --tag` skipped tag cleanup:** the tag wasn't lowercased or checked, so `bm list --tag Work` printed nothing and an invalid tag was silently accepted. The method is also now called `listByTag`, as the plan names it (it was `listTagged`). Commit `3910dff`.

I also added the tests the plan asked for but the branch didn't have: a duplicate tag, and an unknown id in both the store and the CLI.

The `/commit` skill isn't installed in this environment, so I committed with plain `git commit` in the repo's `bm: ...` message style. Nothing is pushed.

## Open
- **`bm list --tag` with no tag after it lists everything without complaint.** The same goes for `bm list foo`, where the extra argument is ignored. The plan doesn't say what should happen. I recommend printing a usage error and exiting 2, but that changes what users see, so I left it for you to decide.
- **`bm tag "" work` is read as id 0** and reports `no bookmark 0` (exit 1) instead of the usage message. I recommend rejecting an empty or non-positive id as bad input, alongside the item above.
- **Duplicate tags already on disk:** only someone who ran this branch before the fix could have them, and nothing cleans them up when the file is loaded. It's probably not worth handling unless the branch has been used on real data.

## Where to look
1. `src/store.ts`, from `load()` to `tag()`: how old files without tags are read in, and the duplicate check before saving.
2. `src/cli.ts`, `run()`: how each error maps to its message and exit code, then the argument parsing in the `tag` and `list` cases.

The rest is routine and can be skimmed: `src/tags.ts`, the new `tags` field on `Bookmark`, and the test files.