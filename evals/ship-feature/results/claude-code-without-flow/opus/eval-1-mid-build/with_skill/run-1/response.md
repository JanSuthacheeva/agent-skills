The build and review are done, and I need your decision on two review items before the merge request.

**Build:** tasks 2-5 are in 4 commits (`dc82acb`..`f435ba0`). I checked the repository myself: all boxes are ticked and 19/19 tests pass. There are no lint or type checks in the repo, so none ran. The build agent also added two usage errors the plan hadn't covered: `tag <id>` with no tag and `list --tag` with no value. Both exit 2.

**Review:** the reviewer worked in a separate context. It added one missing test, showing tags accept digits and dashes (`60c4680`). It wrote its findings into the plan as a `## Review` section (`8963f11`). It left two items open because they change what users see:

1. **`bm list` ignores arguments it doesn't recognise.** `bm list --tag=work` or `bm list -t work` prints every bookmark with exit 0, so the filter is silently lost. `main` already behaved this way.
2. **`bm tag 1 work extra` silently drops `extra`.**

**Recommendation:** fix both. Reject anything unexpected with the usage message (`usage: bm list [--tag <tag>]` or `usage: bm tag <id> <tag>`) and exit 2. Item 1 matters most: a user who types `--tag=work` would think the list was filtered when it wasn't.

Options:
- **A:** Fix both (recommended).
- **B:** Fix only item 1.
- **C:** Leave both as they are and go to the merge request.

Which do you want? If you pick A or B, I'll add the fixes as tasks in the plan, run another build and a second review, then write the merge request.