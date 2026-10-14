Flow status: the build is done and the review is done. The suite is green at 15 tests, and the branch has the review commit `6377bb9`. The review left three open items, so I'm stopping for your decision.

The review fixed four deviations from the plan in `cb9e68a`:
- `bm tag` on an unknown id now exits 1, not 2.
- Tagging a bookmark with a tag it already has is now a no-op.
- `list --tag` now normalizes its argument.
- `listTagged` is renamed to `listByTag`.

It also added the missing tests.

**Open items and my recommendations**
1. **Empty id:** `bm tag "" x` reports `no bookmark 0` instead of the usage line. I recommend a new task to reject an empty id with the usage message.
2. **End-to-end run:** task 5 is ticked but nothing on the branch records it. I recommend a new task to rerun it and record the output.
3. **Second look at `cb9e68a`:** the roughly ten lines of production fixes were reviewed only by the reviewer who wrote them. I recommend that the second review, after the new tasks, covers them. That happens automatically.

If you agree, I'll add items 1 and 2 as tasks under `## Tasks` in the plan, commit, and send a fresh build agent, then a second review. Or tell me to skip any of them and go straight to the merge request.