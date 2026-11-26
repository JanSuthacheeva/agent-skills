# Bookmark sharing

## Decision

Colleagues share bookmark lists as JSON files. `bm import <file>` adds a
shared list to the store and `bm open <id>` opens a bookmark in the
browser. A shared file comes from someone else, so everything in it is
untrusted: only `http:` and `https:` URLs are accepted, and a URL is
never interpreted by a shell.

## Units

`src/urls.ts` - new

```ts
export class InvalidUrlError extends Error {
  readonly raw: string
  constructor(raw: string)
}
// Returns the normalized URL; throws InvalidUrlError unless it parses
// and its protocol is http: or https:.
export function parseWebUrl(raw: string): string
```

`src/opener.ts` - new

```ts
// The command in BM_OPENER, else `open` on macOS and `xdg-open` elsewhere.
export function defaultOpener(): string
// Runs the opener with the URL as its only argument, without a shell.
export function openUrl(url: string, opener?: string): void
```

`src/store.ts` - modified

```ts
export class BookmarkNotFoundError extends Error {
  readonly id: number
  constructor(id: number)
}

class BookmarkStore {
  get(id: number): Bookmark
  importAll(entries: { url: string; title: string }[]): Bookmark[]
}
```

`src/cli.ts` - modified: `run(argv, store, out, open = openUrl)` gains the
`import` and `open` commands; `open` is a parameter so tests do not start
a browser.

## Call chains

`bm import <file>`

1. `main -> run(argv, store, out): number`
2. `run -> readFileSync(file)`, `JSON.parse`
3. `run -> parseWebUrl(entry.url)` for every entry, before anything is
   stored
4. `run -> BookmarkStore::importAll(entries): Bookmark[]`
5. `run -> out.log("imported <n>")`, exit 0

`bm open <id>`

1. `main -> run(argv, store, out): number`
2. `run -> BookmarkStore::get(id): Bookmark`
3. `run -> open(bookmark.url)`, exit 0

Errors:

- A URL that does not parse or is not `http:`/`https:`:
  `InvalidUrlError`, the CLI prints `invalid url: <raw>`, exit 2, and
  nothing from the file is imported.
- Unknown id in `open`: `BookmarkNotFoundError`, the CLI prints
  `no bookmark <id>`, exit 1.

## Tasks

- [ ] `src/urls.ts`: `parseWebUrl` with tests for http, https and a
      rejected scheme
- [ ] `src/opener.ts`: `openUrl` and `defaultOpener`
- [ ] Store: `get`, `importAll`, `BookmarkNotFoundError`, with tests
- [ ] CLI: `import` and `open`, with tests for both and their errors
