The review is finished, and it left one decision for you before I can write the merge request.

It fixed five problems itself, one commit each, and the tests went from 10 to 16, all passing:
- **Duplicate tags:** tagging a bookmark with a tag it already had stored it twice.
- **Wrong exit code:** `bm tag` on an unknown id exited 2 instead of 1.
- **`list --tag` matching:** `bm list --tag Work` found nothing for a bookmark tagged `work`, and an invalid tag there was not reported as `invalid tag: <raw>`.
- **Method name:** the store method was called `listTagged` instead of the plan's `listByTag`.
- **Bad ids accepted:** ids like `""`, `0x1` and `1e0` were accepted instead of printing the usage message.

**Open item:** `bm list --tag` with no value lists every bookmark, and `list` ignores any other argument it's given. The plan doesn't say what should happen here.

Options:
1. **Reject it (reviewer's and my recommendation):** print `usage: bm list [--tag <tag>]` and exit 2. Today a typo silently shows the wrong result.
2. **Leave it as it is** and ship.

Which do you want? If you pick 1, I'll add it as a task to the plan, build it, and run a second review on the new commits.