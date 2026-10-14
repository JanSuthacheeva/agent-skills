I couldn't run the tests or the CLI because those commands needed permission. So the description below comes from reading the diff, the plan in `docs/plans/2026-10-14-bookmark-tags.md` and `AGENTS.md`. The branch name has no ticket ID, so the title uses a scope and description.

---

**Title:** `bm: add bookmark tags`

## Summary

Adds tags to bookmarks:

- `bm tag <id> <tag>` puts a tag on a bookmark.
- `bm list --tag <tag>` lists only the bookmarks with that tag.

Tags are saved on each bookmark in the existing `.bookmarks.json` file. `BookmarkStore` handles tagging and filtering, and the CLI only parses arguments and prints. All tag checking goes through `normalizeTag`: it trims and lowercases the tag, and only allows `a-z`, `0-9` and `-`.

Plan: `docs/plans/2026-10-14-bookmark-tags.md`

## Changes

- `src/tags.ts` (new): `normalizeTag(raw)` and `InvalidTagError`.
- `src/bookmark.ts`: `Bookmark` gets a `tags: string[]` field.
- `src/store.ts`:
  - New bookmarks start with `tags: []`.
  - `load()` reads old files that have no `tags` field as `tags: []`, so no migration is needed.
  - Adds `BookmarkNotFoundError`, `tag(id, tag)` and `listTagged(tag)`.
- `src/cli.ts`:
  - `run` now wraps a new `dispatch` function and turns `InvalidTagError` and `BookmarkNotFoundError` into error messages and exit codes.
  - Adds the `tag` command and the `--tag` option on `list`.
- Tests: `test/tags.test.ts`, `test/store.tags.test.ts`, `test/cli.tags.test.ts`.

## How to test

```sh
npm test
cd "$(mktemp -d)"
npm run bm --prefix <repo> -- add https://a.dev A
npm run bm --prefix <repo> -- tag 1 " Work "   # tagged 1 work
npm run bm --prefix <repo> -- list --tag work  # 1  A  https://a.dev
npm run bm --prefix <repo> -- tag 1 "to do"    # invalid tag: to do, exit 2
```

## Review guide

Start with `src/tags.ts`, then `src/store.ts`, then `src/cli.ts`. In several places the code doesn't match the plan or `AGENTS.md`, and these should be fixed before merging:

1. **Adding the same tag twice stores it twice.** `BookmarkStore::tag` always appends the tag (`src/store.ts:50`). The plan says tagging with an existing tag should do nothing, and nothing tests this.
2. **An unknown id exits with 2 instead of 1.** `src/cli.ts:20` returns 2. `AGENTS.md` and the plan both say "not found" should exit with 1.
3. **`list --tag` doesn't normalize the tag.** `src/cli.ts:53` passes the raw value to `listTagged`, so `bm list --tag Work` finds nothing and `bm list --tag "to do"` returns an empty list instead of an error. The plan says this path should call `normalizeTag`.
4. **`list --tag` with no value lists everything.** If the tag value is missing, it quietly falls back to listing all bookmarks instead of printing a usage error.
5. **Method name differs from the plan.** The plan calls it `listByTag`, the code calls it `listTagged`. One of them should be changed so they match.
6. **Tests the plan asked for are missing.** There's no test for a duplicate tag, an unknown id (in the store or the CLI), or a non-numeric id.
7. **`docs/plans/...` has all tasks ticked**, including the manual CLI check, even though points 1-6 are still open.

`tag` normalizes the tag in both the CLI and the store. That's harmless, but only one of the two is needed.

---

Do you want me to fix points 1-6 on this branch before the MR is opened? Then the review guide would only need the parts about the design.