# Bookmark tags

Review page: `.lavish/bookmark-tags-implementation.html`

## Decision

Tags live on each bookmark in the existing store file; `BookmarkStore`
owns tagging and filtering, the CLI only parses and prints. Tags are
normalized once, in `normalizeTag`, so the store and the CLI agree on what
a valid tag is.

## Units

`src/tags.ts` - new

```ts
export class InvalidTagError extends Error {
  constructor(raw: string)
}
export function normalizeTag(raw: string): string
```

`src/bookmark.ts` - modified

```ts
export interface Bookmark {
  // existing fields unchanged
  tags: string[]
}
```

`src/store.ts` - modified

```ts
export class BookmarkNotFoundError extends Error {
  constructor(id: number)
}

class BookmarkStore {
  // add() now creates bookmarks with tags: []
  tag(id: number, tag: string): Bookmark
  listByTag(tag: string): Bookmark[]
}
```

`src/cli.ts` - modified: `run(argv, store, out)` gains the `tag` command
and a `--tag <tag>` option on `list`.

## Data

- `Bookmark.tags: string[]`, normalized, without duplicates, in the order
  they were added.
- The store file keeps its format: a JSON array of bookmarks, now with a
  `tags` field. Files written before this change have no `tags` field;
  `load()` reads them as `tags: []`, so no migration is needed.

## Call chains

`bm tag <id> <tag>`

1. `main -> run(argv, store, out): number`
2. `run -> normalizeTag(raw): string`
3. `run -> BookmarkStore::tag(id, tag): Bookmark`
4. `BookmarkStore::tag -> BookmarkStore::load(): Bookmark[]`, then `save(bookmarks): void`
5. `run -> out.log("tagged <id> <tag>")`, exit 0

`bm list --tag <tag>`

1. `main -> run(argv, store, out): number`
2. `run -> normalizeTag(raw): string`
3. `run -> BookmarkStore::listByTag(tag): Bookmark[]`
4. `run -> out.log(format(bookmark))` per bookmark, exit 0

Errors:

- Empty tag or characters outside `a-z`, `0-9` and `-` after
  normalizing: `InvalidTagError`, the CLI prints `invalid tag: <raw>`,
  exit 2.
- Unknown id in `tag`: `BookmarkNotFoundError`, the CLI prints
  `no bookmark <id>`, exit 1.
- Non-numeric id: `usage: bm tag <id> <tag>`, exit 2.

## Test seams

- `normalizeTag` - unit, no fakes.
- `BookmarkStore` - against a temp file, as `test/store.test.ts` does.
- `run` - with a temp-file store and a recording `Output`, as
  `test/cli.test.ts` does.

## Assumptions

- Tags are lowercased and trimmed: `" Work "` becomes `work`.
- Tagging a bookmark with a tag it already has is a no-op, not an error.
- `list --tag` prints in the same format as `list`.

## Tasks

- [ ] Add `normalizeTag(raw)` and `InvalidTagError` in `src/tags.ts` with unit tests for case, surrounding whitespace, empty input and invalid characters
- [ ] Add `tags` to `Bookmark`, create new bookmarks with `tags: []` and read missing tags as `[]` in `BookmarkStore::load`, with a test that loads a file written before tags existed
- [ ] Add `BookmarkNotFoundError`, `BookmarkStore::tag(id, tag)` and `BookmarkStore::listByTag(tag)` with tests for a duplicate tag and an unknown id
- [ ] Add `bm tag <id> <tag>` and `bm list --tag <tag>` to `run(argv, store, out)` with CLI tests for both and for an invalid tag and an unknown id
- [ ] Run `npm run bm -- add`, `tag` and `list --tag` against a temp store file and check the output
