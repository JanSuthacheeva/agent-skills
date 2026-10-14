Review finished. It fixed three bugs, each with a test that fails without the fix:

- Tagging a bookmark twice with the same tag stored it twice. It now does nothing.
- `bm tag` on an unknown id exited 2 instead of 1.
- `bm list --tag` used the tag as typed. So `--tag Work` found nothing, and an invalid tag printed nothing and exited 0 instead of exiting 2. The store method is also renamed to `listByTag`, the name the plan uses.

All 16 tests pass and the working tree is clean.

**Stop: three open review items need your decision**

1. **`bm list --tag` with no value** currently lists every bookmark without saying anything. The reviewer recommends printing `usage: bm list [--tag <tag>]` and exiting 2. I agree: an option without its value is bad input, and quietly ignoring it hides typos.
2. **The id in `bm tag` is parsed loosely.** `""` is read as id 0 and `0x1` as id 1. The reviewer recommends accepting digits only (`/^\d+$/`) and printing the usage message with exit 2 otherwise. I agree, because the plan already says a non-numeric id should get the usage message.
3. **The tag is cleaned up twice**, once in the CLI and again in `BookmarkStore::tag`. The reviewer recommends keeping it: running it twice gives the same result, and it keeps the store safe for other callers. I agree, so no change.

My recommendation: fix 1 and 2, keep 3. If you approve, I'll add 1 and 2 to the plan as tasks, commit, run a fresh build agent and then a second review. After that I'll write the merge request.