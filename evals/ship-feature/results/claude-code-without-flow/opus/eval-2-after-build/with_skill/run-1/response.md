The review of `feature/bookmark-tags` is done, and it left two open items for you to decide before I build any more.

**What the reviewer fixed** (all 16 tests pass, nothing pushed):
- Tagging a bookmark twice saved the tag twice. The plan says a repeated tag should do nothing (`245e1ad`).
- Tagging an unknown bookmark id exited with 2 instead of 1 (`da08103`).
- `list --tag` didn't clean up the tag first, so `list --tag Work` found nothing and invalid tags weren't rejected (`e389e59`).

**Open items:**
1. `bm list --tag` with no tag after it quietly lists every bookmark. The reviewer recommends printing `usage: bm list [--tag <tag>]` and exiting with 2.
2. `bm tag '' work` treats the empty id as 0 and prints `no bookmark 0` with exit 1. The plan says this should be the usage error with exit 2. Ids like `0x1` and `1e0` are also accepted. The reviewer recommends accepting only plain digits (`/^\d+$/`).

I'd take both recommendations. Both bugs are cases of bad input that should get the usage error and exit 2, as the plan already says for bad ids.

Should I add both as tasks to the plan and build them? A second review would then cover the new commits.