The review is finished, and it left two open items. I'm stopping here for your decision before the merge request.

**Fixed by the reviewer** in commit `cad1609`. The tests pass (16) and the working tree is clean.
- Tagging a bookmark twice stored the tag twice. It is now a no-op, as the plan says.
- An unknown id exited 2. It now exits 1.
- `list --tag Work` found nothing because the filter wasn't normalized. It is now.
- `listTagged` is renamed to `listByTag`, as in the plan.
- Tests were added for each of these. The reviewer reports that five of them failed before the fixes.

**Open items, for you to decide**
1. **`bm list --tag` with no value** currently lists every bookmark without complaint. I recommend a usage error, `usage: bm list [--tag <tag>]`, with exit 2. If you agree, I'll add it as a task in the plan and run another build and review pass.
2. **A corrupt store file** still throws a raw `SyntaxError`. This was already the case before this branch, and the file is never overwritten. I recommend leaving it alone.

One more thing: the plan's last task, the manual `npm run bm` check, was ticked, yet the duplicate-tag and exit-code bugs would have shown up in it.

Do you want the usage error for item 1? If you say no, I'll move straight to the merge request description. Nothing is pushed until you approve it.