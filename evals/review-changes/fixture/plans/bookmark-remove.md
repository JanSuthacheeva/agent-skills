# Remove bookmarks

## Decision

`bm remove <id>` deletes one bookmark. The store owns the deletion; the
CLI only parses and prints. Builds on the sharing branch, which added
`BookmarkStore::get` and `BookmarkNotFoundError`.

## Units

`src/store.ts` - modified

```ts
class BookmarkStore {
  // Throws BookmarkNotFoundError for an unknown id; saves nothing then.
  remove(id: number): Bookmark
}
```

`src/cli.ts` - modified: `run` gains the `remove` command.

## Call chains

`bm remove <id>`

1. `main -> run(argv, store, out): number`
2. `run -> BookmarkStore::remove(id): Bookmark`
3. `BookmarkStore::remove -> load()`, then `save(bookmarks)` without it
4. `run -> out.log("removed <id>")`, exit 0

Errors:

- Unknown id: `BookmarkNotFoundError`, the CLI prints `no bookmark <id>`,
  exit 1, and the file is unchanged.
- An id that is not an integer: `usage: bm remove <id>`, exit 2.

## Tasks

- [ ] Store: `remove`, with tests for a known and an unknown id
- [ ] CLI: `remove`, with tests for removal and its errors
