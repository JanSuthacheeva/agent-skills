Checked the branch, its plan and the diff. Here is the draft; I haven't pushed anything.

**Title**

```
bm: add bookmark tags with `tag` command and `list --tag`
```

**Description**

```
Bookmarks can now be tagged and filtered by tag. Tags are stored on each bookmark in the existing store file, and `normalizeTag` is the single place that decides what a valid tag is (trimmed, lowercased, only `a-z`, `0-9` and `-`).

- No migration: files written before this change have no `tags` field, and `BookmarkStore::load` reads them as `tags: []`. The file format stays a JSON array of bookmarks.
- `BookmarkStore` owns tagging and filtering; the CLI only parses, calls it and prints. Errors are reported by `run()`, which maps `InvalidTagError` and `BookmarkNotFoundError` to messages and exit codes.

Review:
1. `bm tag` from `src/cli.ts` `run()` through `normalizeTag` to `BookmarkStore::tag` - the write path. Check what is saved when a tag is added twice, and the exit codes.
2. `BookmarkStore::load` and `listTagged` in `src/store.ts` - the read path for old store files and the tag filter. Check that `list --tag` and `tag` treat the raw tag the same way.
3. `src/tags.ts` and its test - the tag rules.
Skim: `Bookmark.tags` in `src/bookmark.ts`, tests, ticked tasks in the plan.
```

Before you push, the diff differs from `docs/plans/2026-10-14-bookmark-tags.md` in four places. I couldn't find a reason for any of them in the commits or the plan, so I left them out of the description:

- **Duplicate tags:** the plan says re-tagging is a no-op. `BookmarkStore::tag` pushes the tag again, so a bookmark can end up with `work` twice.
- **Unknown id:** the plan says exit 1. `run()` returns 2.
- **Filter normalization:** `list --tag Work` passes the raw value to `listTagged`, so it won't match a stored `work`. The plan has `run` normalize it first.
- **Method name:** the plan calls it `listByTag`; the code has `listTagged`.

I'd fix the first three before opening the MR. If any is intentional, tell me why and I'll add it as a decision bullet.

Other things to know:
- The branch name has no ticket ID, so the title is scoped and there's no `Refs:` line.
- There are no deploy steps: no new environment variables, dependencies or migrations.
- No open MR exists for this branch.
- The working tree is clean.

Tell me to push and create it once the description is settled.