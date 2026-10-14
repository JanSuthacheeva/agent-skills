Build and review are done, and I need a decision from you on two open review items before the merge request.

**State:** the branch `feature/bookmark-tags` has all 5 plan tasks ticked and committed. The 17 tests pass and the tree is clean. The review found and fixed one bug: `bm tag "" work` reported `no bookmark 0` with exit 1, and now prints the usage error with exit 2 (`d4abd7c`). The reviewer did not run a second review of that one-line fix. It also noted it was not a fresh, isolated context.

**Open items:**
1. `bm list --bogus` ignores unknown options and lists everything. This was already the case before this branch and the plan doesn't cover it. The reviewer recommends rejecting unknown `list` options in a follow-up. I agree: leave it out of this merge request and don't add a task.
2. The CLI and `BookmarkStore` both normalize the tag. It's harmless and the plan allows it. I recommend leaving it.

**Options:**
- **A (recommended):** accept both as-is, and I go on to draft the merge request title and description. I'll show them to you and push only on your say-so.
- **B:** add tasks for either item, and I go back to Build, followed by a second review.

Which do you want?