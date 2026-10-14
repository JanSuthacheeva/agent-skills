The review is done and it has open items, so the flow stops here for your decision.

**Fixed by the reviewer:** `bm tag "" x` read the empty id as 0 and printed `no bookmark 0` with exit 1. The plan says a non-numeric id should print the usage line with exit 2, and it now does. The fix has a test (`fd3e8f3`) and all 18 tests pass. The reviewer re-read its own fix instead of getting a fresh agent to check it, and the plan's review section says so.

**Open, needs your decision:**
1. **`list` with a missing or misspelled flag:** `bm list --tag` with no value, or `bm list --tagg work`, currently lists every bookmark and exits 0. This is the same gap I flagged in the build summary, and the plan doesn't cover it. The reviewer recommends a usage error with exit 2 for any `list` argument other than `--tag <tag>`. I agree, because a silent unfiltered list looks like a filter that matched everything. It would add a task to the plan and one more build pass, followed by a second review of the new commits.
2. **Corrupt store file:** `load()` throws on one, as it did before this branch, and nothing gets overwritten. The reviewer treats this as a note, not a defect, and I recommend leaving it.

Should I add a task for the `list` usage error (item 1) and build it, leaving item 2 alone?