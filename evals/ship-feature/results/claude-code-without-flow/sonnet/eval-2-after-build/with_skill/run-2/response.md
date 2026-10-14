The review left open items, so I'm stopping to ask you about them.

**Review result:** four bugs were fixed in `cab5262`, with failing tests written first:
- `bm tag` on an unknown id now exits 1 instead of 2.
- Tagging a bookmark twice no longer stores the tag twice.
- `list --tag Work` now normalizes and validates the tag.
- `listTagged` is renamed `listByTag`, as the plan names it.

The review notes are in the plan (`a225044`). The reviewer re-read its own fixes, but no independent agent did.

**Open items and my recommendations:**
1. **`bm list --tag` with no value** silently lists every bookmark. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2. This is a user-visible behaviour change that the plan doesn't cover.
2. **A corrupt store file** throws a raw `SyntaxError`. This predates the branch. I recommend leaving it out of this MR and tracking it as a separate change.
3. **The last plan task (the end-to-end `npm run bm` run)** is ticked, but nothing on the branch shows it was done. I recommend I run it myself now, after item 1.

Should I add items 1 and 3 as tasks, build them, and then run a second review over the new commits? Item 2 would stay out of this MR. Or would you decide differently on any of them?