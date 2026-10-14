The review has finished, and it left two items open that need your decision.

The reviewer, working in a fresh context, found and fixed three bugs. Tests went from 10 to 15 and all pass:
- **Duplicate tags:** tagging a bookmark with a tag it already had added the tag again. It now does nothing (`7954891`).
- **Wrong exit code:** `bm tag` on an unknown id exited 2 instead of 1 (`1841e35`).
- **`list --tag` didn't clean up the tag:** it skipped `normalizeTag`, so `--tag Work` found nothing and an invalid tag exited 0. The same commit renames the store method from `listTagged` to `listByTag`, the name the plan uses (`7410730`).

**Open:**
1. **`bm list --tag` with no value** lists every bookmark and exits 0. The plan doesn't cover this case. The reviewer recommends printing `usage: bm list [--tag <tag>]` and exiting 2, like the other commands.
2. **`bm tag "" work`** reads the empty id as 0 and prints `no bookmark 0` (exit 1) instead of the usage message. The reviewer recommends rejecting any id that isn't a positive whole number, so it prints `usage: bm tag <id> <tag>` and exits 2.

I agree with both. They're small, and each makes the CLI behave the same way it already does for other bad input. If you approve, I'll add them as two new tasks in the plan, build them, have a second review check the new commits, and then write the merge request.

Should I do both as recommended?