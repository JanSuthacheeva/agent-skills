I fixed and committed (`4946d03`) three bugs that an end-to-end run of the CLI turned up. The tests that were already there passed despite them. All 15 tests pass now, and I re-ran the CLI against a temp store file to confirm.

- **Duplicate tags:** tagging a bookmark with a tag it already had stored the tag twice. It is now a no-op, as the plan says.
- **Unknown id:** `bm tag 9 x` exited 2. It now exits 1.
- **`list --tag`:** it didn't normalize its argument, so `--tag WORK` matched nothing and an invalid tag was never rejected. It now normalizes the tag and exits 2 with `invalid tag: <raw>` on a bad one.

I also renamed `listTagged` to `listByTag` to match the plan. I added tests for the duplicate tag, the unknown id (store and CLI), the non-numeric id and `list --tag`.

The branch has not been reviewed or pushed, and no merge request exists yet. Next would be `/review-changes`, then `/write-merge-request`. Say if you want me to run them.