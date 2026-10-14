I'm writing the description from the diff and the plan doc. Running the tests needs approval, so I'm skipping that and will say so in the description.

**Title:** `tags: add bookmark tags and list --tag filter`

(The branch name has no ticket ID, so this uses the Scoped Commits format.)

**Description:**

## What

Bookmarks can now carry tags. This adds `bm tag <id> <tag>` and `bm list --tag <tag>`, following `docs/plans/2026-10-14-bookmark-tags.md`.

## How

- `src/tags.ts` is new. `normalizeTag` trims and lowercases, and accepts only `a-z`, `0-9` and `-`. Anything else throws `InvalidTagError`.
- `Bookmark` gets `tags: string[]`. New bookmarks start with `tags: []`. `BookmarkStore.load()` reads a missing `tags` field as `[]`, so existing store files work without a migration.
- `BookmarkStore` gets `tag(id, tag)` and `listTagged(tag)`. It also gets `BookmarkNotFoundError`.
- `run` is split into `run` and `dispatch`. `run` catches `InvalidTagError` and `BookmarkNotFoundError` and prints the error with exit code 2.

## Review guide

Start with `src/store.ts` and `src/cli.ts`. The rest is small.

Differences from the plan, which I'd like a decision on:

- **Duplicate tags are not a no-op.** The plan says tagging with a tag the bookmark already has does nothing. `BookmarkStore.tag` currently pushes it again, so `bm tag 1 work` run twice gives `["work", "work"]`.
- **`list --tag` does not normalize its argument.** The plan's call chain normalizes it. Right now `list --tag Work` finds nothing, even though `tag 1 Work` stores `work`.
- **Unknown id exits with 2.** The plan says 1.
- **Method name.** The store method is `listTagged`. The plan calls it `listByTag`.

Test gaps against the plan:

- There is no test for a duplicate tag.
- There is no test for an unknown id, in the store or the CLI.
- There is no test for `list --tag` with an invalid tag.
- The plan's tasks are all ticked, including the manual `npm run bm` check. I haven't verified that it was done.

## Testing

I did not run the test suite while writing this description. New tests are in `test/tags.test.ts`, `test/store.tags.test.ts` and `test/cli.tags.test.ts`.

---

I haven't fixed the four differences from the plan. Do you want me to fix them before you open the MR, or should the description say they are intentional?