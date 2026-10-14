I couldn't run the tests here (`npm test` needed approval), so I wrote this from the diff and the plan in `docs/plans/2026-10-14-bookmark-tags.md`. The branch name has no ticket ID, so the title uses the scoped-commit format.

---

**Title:** `bm: tag bookmarks and filter list by tag`

**Description:**

```markdown
## What

Adds tags to bookmarks:

- `bm tag <id> <tag>` adds a tag to a bookmark
- `bm list --tag <tag>` shows only bookmarks with that tag

Plan: `docs/plans/2026-10-14-bookmark-tags.md`

## How

- `src/tags.ts` (new) - `normalizeTag(raw)` trims and lowercases the input, and only accepts `a-z`, `0-9` and `-`. Anything else throws `InvalidTagError`.
- `src/bookmark.ts` - `Bookmark` has a new field, `tags: string[]`.
- `src/store.ts`
  - `add()` creates bookmarks with `tags: []`.
  - `load()` reads a missing `tags` field as `[]`. Existing `.bookmarks.json` files work as they are, with no migration.
  - New: `tag(id, tag)`, `listTagged(tag)` and `BookmarkNotFoundError`.
- `src/cli.ts`
  - `run()` now wraps a new `dispatch()`. It turns `InvalidTagError` into `invalid tag: <raw>` and `BookmarkNotFoundError` into `no bookmark <id>`, both with exit code 2.
  - A non-numeric id or a missing tag prints `usage: bm tag <id> <tag>` and exits with 2.

## Data

The store file format is the same: a JSON array of bookmarks, which now has a `tags` field. Older files load without changes.

## Testing

- `test/tags.test.ts` - normalizing, plus rejecting empty and invalid tags
- `test/store.tags.test.ts` - loading a file written before tags existed, and tag then `listTagged`
- `test/cli.tags.test.ts` - tag then `list --tag`, and an invalid tag exits with 2

## Review guide

1. Start with `src/tags.ts`. It is the only place that decides what a valid tag is.
2. `src/store.ts` - check the backward-compatible `load()` and the new `tag()` and `listTagged()`.
3. `src/cli.ts` - check that the `run()`/`dispatch()` split maps errors to exit codes correctly.
```

---

The plan's tasks are all ticked off, but the code doesn't match the plan in several places. Things to fix before opening the MR:

1. **Duplicate tags are stored twice.** The plan says tagging a bookmark with a tag it already has does nothing. `BookmarkStore.tag` (`src/store.ts:50`) adds the tag again anyway, and no test checks for a duplicate tag.
2. **Unknown id gives the wrong exit code.** The plan says it should exit with 1, but `src/cli.ts:20` exits with 2. Neither the store tests nor the CLI tests try an unknown id.
3. **`list --tag` skips `normalizeTag`.** So `bm list --tag Work` finds nothing, and `bm list --tag "to do"` shows an empty list instead of `invalid tag`. The store test only passes because it filters on `'work'`, already lowercase.
4. **`bm list --tag` with no value shows every bookmark** instead of a usage error.
5. **Name differs from the plan.** The plan calls the method `listByTag`; the code calls it `listTagged`. Either rename it or update the plan.

Once these are fixed, the "Testing" section needs updating. Want me to fix them, with tests, and then update the description?