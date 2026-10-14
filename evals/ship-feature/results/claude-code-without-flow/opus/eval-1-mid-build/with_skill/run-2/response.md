Tasks 2-5 are built (4 commits) and all 17 tests pass. A separate agent reviewed the branch and fixed nothing, but it left two open items. The flow stops here for your decision:

1. **`list` and `tag` silently ignore arguments they don't recognise.** A typo like `bm list --tags work` prints every bookmark and exits 0, so you never learn the filter wasn't applied. `bm tag 1 work extra` adds `work` and drops `extra`.
   - Reviewer's fix: anything other than `list` or `list --tag <tag>` prints `usage: bm list [--tag <tag>]` and exits 2. Extra arguments to `tag` get the same treatment.
2. **The store accepts tags that aren't normalized.** `store.tag(1, ' To Do ')` saves `" To Do "` as is. Only the CLI calls `normalizeTag`, so the CLI is safe today, but every future caller would have to remember to.
   - Reviewer's fix: `tag()` and `listByTag()` call `normalizeTag` themselves.

I recommend taking both. They are small, and both make bad input fail loudly instead of being accepted quietly. The first changes what users see, which is why the reviewer left it to you.

Once you decide, I'll add the chosen items to the plan as tasks, build them, run a second review on the new commits and then move on to the merge request. Should I take both, one, or neither?