**Title:** `bookmarks: add tags to bookmarks`

There is no ticket ID in the branch name, so I used a scoped-commit title. I didn't run the test suite because the command needed approval, so the description below makes no claim that tests pass.

---

## What

Bookmarks can now be tagged. This adds `bm tag <id> <tag>` and `bm list --tag <tag>`. Tags are stored on each bookmark in the existing `.bookmarks.json`.

Plan: `docs/plans/2026-10-14-bookmark-tags.md`

## How

- `src/tags.ts` (new): `normalizeTag` trims and lowercases, and accepts only `a-z`, `0-9` and `-`. Anything else throws `InvalidTagError`.
- `src/bookmark.ts`, `src/store.ts`: `Bookmark` gains `tags: string[]`. New bookmarks start with `tags: []`. `load()` reads a missing `tags` field as `[]`, so old store files keep working with no migration.
- `src/store.ts`: `BookmarkStore.tag(id, tag)` and `listTagged(tag)`. `tag` throws `BookmarkNotFoundError` for an unknown id.
- `src/cli.ts`: `run` now wraps a new `dispatch` function and turns `InvalidTagError` and `BookmarkNotFoundError` into messages and exit codes.

## Review guide

Start with `src/store.ts`. `tag()` and `listTagged()` hold the behavior, and that is where the differences from the plan below sit.

## Differences from the plan

The plan's tasks are all ticked, but the code differs from it in these places:

1. **Duplicate tags are not a no-op.** The plan says tagging with an existing tag does nothing. `BookmarkStore.tag` does `tags.push(...)` without checking, so `bm tag 1 work` twice stores `["work", "work"]`. No test covers this, although the plan's task list asks for one.
2. **`list --tag` does not normalize its argument.** The plan's call chain runs `normalizeTag` before the lookup. Here `listTagged` compares the raw string, so `bm list --tag Work` finds nothing, and an invalid tag returns an empty list instead of exit 2.
3. **Unknown id exits with 2, not 1.** The plan specifies exit 1 for `BookmarkNotFoundError`. `run` returns 2 for both error types. No CLI test covers the unknown-id case.
4. **Naming.** The plan calls the lookup `listByTag`. The code calls it `listTagged`.
5. **Double normalization.** The CLI calls `normalizeTag` and then `store.tag` calls it again. This is harmless but redundant.
6. **No test for `BookmarkNotFoundError`.** The plan's store task asks for one. Neither the store tests nor the CLI tests include it.

I'd suggest fixing 1 to 3 before merge, or updating the plan to match what was built if the current behavior is intended.

## Testing

- New unit tests: `test/tags.test.ts`, `test/store.tags.test.ts`, `test/cli.tags.test.ts`.
- The last plan task (a manual `npm run bm -- add`, `tag` and `list --tag` run) is ticked, but its output isn't recorded here.