**Title**
```
bm: tag bookmarks and filter the list by tag
```

**Description**
```
Bookmarks could not be grouped. This adds tags: `bm tag <id> <tag>` attaches a normalized tag to a bookmark, and `bm list --tag <tag>` lists the bookmarks that carry it.

- Tags are stored on each bookmark in the existing store file, so there is no migration. `load()` reads files written before this change as `tags: []`.
- `normalizeTag` (trim, lowercase, `a-z0-9-` only) is the single definition of a valid tag, shared by the CLI and the store.
- An unknown bookmark id exits with 2, not 1 as the plan says.

Review:
1. `bm tag` from `run()` in `src/cli.ts` through `BookmarkStore::tag` in `src/store.ts`. Check the write path (load, push, save), the error mapping in `run()` and the exit codes.
2. `BookmarkStore::load` and `listTagged`. Check that old store files still load and that the tag filter matches what `tag` stores.
3. `src/tags.ts` and its test.
Skim: the tests, and the checkbox updates in `docs/plans/2026-10-14-bookmark-tags.md`.

Plan: `docs/plans/2026-10-14-bookmark-tags.md`
```

Before you open this, check four places where the code differs from the plan. I left them out of the description because they look like bugs, not decisions.
- **Duplicate tags:** `store.tag` pushes without checking, so tagging twice stores the tag twice. The plan says a repeat should do nothing.
- **Tag filter not normalized:** `list --tag Work` does not normalize its argument, so it finds nothing. The plan has `run` call `normalizeTag` first, and an invalid tag should exit 2.
- **Missing id:** an unknown id exits 2, and the plan says 1. I listed this one in the description as a decision, but I can't tell whether it was intended. Remove that bullet if it wasn't.
- **Name:** `listTagged` is `listByTag` in the plan.

I haven't pushed or created anything. Once you've settled these, tell me to push and create the MR. No open MR exists for this branch yet, and `glab` is available.