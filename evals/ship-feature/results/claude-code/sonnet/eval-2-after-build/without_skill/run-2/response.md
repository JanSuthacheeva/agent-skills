The bookmark tags feature is now finished. Every plan task was already checked off, but running the CLI end to end showed three bugs that the existing tests didn't catch. I fixed them and committed. All 16 tests pass, and I re-ran the end-to-end check against the CLI to confirm.

- **Duplicate tags:** tagging a bookmark with `work` twice stored `work` twice. Re-tagging is now a no-op, as the plan says.
- **Case in `list --tag`:** `list --tag WORK` found nothing. The tag is now normalized before filtering.
- **Exit code for an unknown id:** `bm tag 9 x` exited 2. It now exits 1, as the plan and `AGENTS.md` specify.

I also renamed the store method from `listTagged` to `listByTag` to match the plan. I added tests for each fix, plus invalid tags in `list --tag` and a non-numeric id.

The fixes are in one commit, `bm: fix tag no-op, list --tag normalizing and not-found exit`, on `feature/bookmark-tags`. I haven't pushed or opened a merge request. Say the word and I'll run `review-changes` or `write-merge-request`.