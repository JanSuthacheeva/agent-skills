The fix for SHOP-311 is built and reviewed, and the branch is ready for a merge request. The review left one open item, and that needs your decision first.

**What the build did** (branch `fix/SHOP-311-tags-lost`):
- `7de33ad` store: keep tags when saving bookmarks. I wrote the regression test first, and it failed just as the plan said it would: `[]` came back instead of `['work']`. Then I changed `toRecord()` so it saves `tags`.
- `ed3563c` store: save tags through save() like add(). `tag()` now saves through `save(all)`, so there is only one way the file gets written.
- `6af9fbd` ticks the end-to-end check. I ran the ticket's reproduction again, and the last `list --tag work` now prints `1  A  https://a.example`.
- All 17 tests pass. The project has no lint or type-check script.
- Nothing differs from the plan. One small thing to know: bookmarks without tags are now stored with `tags: []`. That's what `tag()` already wrote before this fix, and bookmarks saved without the field still load.

**Review** (`5d18229`, run by a separate agent that didn't see this conversation): it found nothing to fix in the code.

**The open item:** tags that `bm add` already deleted are gone from users' files and can't be recovered. The reviewer recommends no code change, and saying this plainly in the merge request and release notes so users know to tag their bookmarks again.

Should I put that warning in the merge request (my recommendation)? Or do you want something else, like a recovery step? Once you decide, I'll draft the merge request title and description for you to look at. I won't push anything until you say so.