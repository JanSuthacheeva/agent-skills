The build and review are done. The flow is now stopped on two open review items, and these decisions are yours.

**Where it stands**
- **Build:** all 5 tasks are done and committed as `7fbc6b2`, `cd57b24`, `c769ffb` and `d8a667d`. I re-ran the tests myself and all 18 pass. The build added one thing the plan didn't cover: `bm tag 1` or `bm list --tag` with no tag now prints the usage line and exits 2.
- **Review:** a separate agent that hadn't seen the build checked the branch. It found no defects and changed no code. It wrote its notes into the plan (`1549705`).

**Open items**
1. **Unexpected arguments are silently ignored.** A typo like `bm list --tags work` lists every bookmark and exits 0. An unquoted `bm tag 1 to do` saves the tag `to` and drops `do`. `list` already ignored extra arguments before this branch, but `--tag` makes this kind of typo more likely.
   - The reviewer recommends rejecting any argument `list` or `tag` doesn't expect, with the usage line and exit 2.
   - **I recommend fixing it.** It's a small change, and failing loudly is clearly better than quietly giving a wrong result.
2. **The store accepts tags that haven't been cleaned up.** `store.tag(1, 'Work')` would save `Work` as-is, uppercase included. The CLI is the only code that calls the store and it always cleans the tag first, so users can't hit this today.
   - The reviewer recommends leaving it until other code starts calling the store.
   - **I lean towards a small fix:** call `normalizeTag` inside `BookmarkStore.tag` and `listByTag`, and have the CLI stop calling it. Tags would then be cleaned in exactly one place, and the store couldn't save a bad tag whoever calls it. This changes the plan's call chains a little.

Also, the plan links a review page at `.lavish/bookmark-tags-implementation.html` that isn't in the repo. I'd remove that line from the plan.

What do you want for items 1 and 2? I'll write your decisions into the plan as new tasks, start a new build, then run a second review before the merge request.