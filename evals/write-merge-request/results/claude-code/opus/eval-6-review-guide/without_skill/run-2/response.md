The MR description is below, but I'd fix the branch before opening it. All five tasks in the plan are ticked, yet the code doesn't do everything the plan says. I couldn't run `npm test` because the permission prompt blocked it, so these come from reading the code:

1. **Tagging twice adds the tag twice.** `BookmarkStore.tag` (`src/store.ts:50`) always appends, so running `bm tag 1 work` twice stores `["work", "work"]`. The plan says a repeat tag does nothing. The duplicate-tag test the plan asks for is also missing.
2. **Wrong exit code for an unknown id.** `bm tag 9 work` exits with 2, but both the plan and `AGENTS.md` say "not found" exits with 1 (`src/cli.ts:21`). Neither the store nor the CLI has a test for an unknown id, though the plan asks for both.
3. **The filter skips tag cleanup.** `bm list --tag Work` finds nothing because it compares the raw text against stored lowercase tags, and `list --tag "to do"` doesn't report an invalid tag (`src/cli.ts:53`). The plan's steps for this command include cleaning up the tag first.
4. **A missing value falls back silently.** `bm list --tag` with no value prints every bookmark instead of a usage error.
5. **A method was renamed.** The plan calls it `listByTag`; the code calls it `listTagged`. Either update the plan or rename the method.
6. **The review page doesn't exist.** The plan links to `.lavish/bookmark-tags-implementation.html`, which isn't in the repo.

Want me to fix 1-5 first? Some of the description would change after that.

---

**Title:** `bm: tag bookmarks and filter list by tag`

(The branch name has no ticket ID, so the title uses the `<scope>: <description>` format.)

```markdown
## What

Adds tags to bookmarks:

- `bm tag <id> <tag>` adds a tag to a bookmark
- `bm list --tag <tag>` lists only bookmarks with that tag

Tags are lowercased and trimmed, and may only contain `a-z`, `0-9` and `-`.
Plan: `docs/plans/2026-10-14-bookmark-tags.md`

## How

- `src/tags.ts` (new): `normalizeTag` and `InvalidTagError` - the single place that decides what a valid tag is.
- `src/bookmark.ts`: `Bookmark` gets `tags: string[]`.
- `src/store.ts`: `BookmarkNotFoundError`, `BookmarkStore.tag(id, tag)` and `BookmarkStore.listTagged(tag)`. New bookmarks start with `tags: []`.
- `src/cli.ts`: `run` now wraps a `dispatch` function and maps `InvalidTagError` and `BookmarkNotFoundError` to error messages and exit codes. Adds the `tag` command and `list --tag`.

## No migration

The store file format is unchanged apart from the new `tags` field. `load()` reads older files without `tags` as `tags: []`, and the next save writes the field.

## Review guide

Suggested order, smallest to largest:

1. `src/tags.ts` + `test/tags.test.ts` - the tag rules.
2. `src/store.ts` + `test/store.tags.test.ts` - the backward-compatible `load()` and the tagging logic.
3. `src/cli.ts` + `test/cli.tags.test.ts` - argument parsing and error-to-exit-code mapping.

Worth a close look:

- The `try/catch` in `run`: every error not listed there is rethrown, so it still crashes the process as before.
- `load()` casts `Partial<Bookmark>` back to `Bookmark` after filling in `tags`. The other fields are trusted, as they were before.

## Testing

- `npm test`
- Manual, against a temporary store:
  ```sh
  export BM_FILE=$(mktemp -d)/bookmarks.json
  npm run bm -- add https://a.dev A
  npm run bm -- tag 1 Work      # tagged 1 work
  npm run bm -- list --tag work # 1  A  https://a.dev
  npm run bm -- tag 1 "to do"   # invalid tag: to do, exit 2
  ```
```