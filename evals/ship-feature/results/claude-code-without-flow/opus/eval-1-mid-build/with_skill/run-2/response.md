I've finished building the bookmark tags feature, and an isolated review found no bugs. Before I write the merge request, you need to decide on the two points the review left open.

**Build:** the remaining four tasks of `docs/plans/2026-10-14-bookmark-tags.md` are done, one commit each:
- `84e28f8` bm: store tags on bookmarks
- `df3051f` bm: tag bookmarks and list them by tag
- `bd06767` bm: add tag command and list --tag
- `3176251` docs: check bookmark tags end to end

Tests went from 6 to 16 and all pass. The project has no lint or type check set up. I ran the real CLI against a store file written before tags existed. Output, exit codes and the saved file all matched the plan, including the error cases (`no bookmark 9` exits 1; an invalid tag and bad usage exit 2).

**One change from the plan:** the plan didn't say what happens with `bm tag <id>` without a tag, with `bm list --tag` without a value, or with an unknown `list` option. I made all three print a usage message and exit 2, matching the existing `add` usage error, and recorded this in the plan.

**Review:** it added one missing test, for an unknown `list` option (`c7f25e9`), so there are now 17 tests, all passing. It wrote its findings into the plan's `## Review` section (`d29388d`).

**Open items to decide:**
1. **Extra arguments are silently ignored.** For example, `bm tag 1 work extra` succeeds. The reviewer recommends leaving it unless the whole CLI should reject extra arguments, `add` included.
2. **The store trusts its caller to clean up tags.** `BookmarkStore::tag` and `listByTag` don't lowercase or check tags themselves; the CLI does it before calling them, as the plan says. The reviewer recommends also doing it in the store only if another caller is added.

I recommend leaving both as they are. With your OK I'll note that in the plan and go on to the merge request. If you want either one changed instead, I'll add it as a task, build it, and run another review first.