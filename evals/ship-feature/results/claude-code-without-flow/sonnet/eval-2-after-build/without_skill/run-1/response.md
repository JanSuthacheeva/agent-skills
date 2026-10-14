The bookmark tags feature now matches the plan and the fixes are committed, but nothing is reviewed or pushed yet. All 15 tests pass, and I re-ran `add`, `tag` and `list --tag` against a temp store file.

The earlier "done" state had real bugs that the unit tests missed. Running the CLI showed:
- **Duplicate tags:** tagging twice stored the tag twice. It's now a no-op, as the plan says.
- **Unknown id:** it exited 2 instead of 1. It now exits 1 and prints `no bookmark 9`.
- **`list --tag`:** it never normalized its input, so `--tag WORK` found nothing. It now normalizes, and an invalid tag exits 2.
- **Method name:** `listTagged` didn't match the plan's `listByTag`, so I renamed it.

The plan required tests for a duplicate tag, an unknown id and the CLI error cases, and they were missing. I added them, but I wrote them in the same pass as the fixes, so I never saw them fail first.

The commit is `c0d42d4` on `feature/bookmark-tags`.

Next I'd run `review-changes` on the branch and then `write-merge-request`. Opening the MR means pushing the branch, so I'll wait for your go-ahead on that.