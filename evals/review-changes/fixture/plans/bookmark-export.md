# Export bookmarks as a web page

## Decision

`bm export <file>` writes the bookmarks as a static HTML page that can be
opened in a browser or shared. Rendering lives in `src/export.ts`; the CLI
only parses and writes the file. Many titles come from shared files, so
every title is escaped for HTML.

## Units

`src/export.ts` - new

```ts
export function escapeHtml(text: string): string
// One <li> per bookmark: a link to its URL, with the title as link text
// and as tooltip.
export function renderPage(bookmarks: Bookmark[]): string
```

`src/cli.ts` - modified: `run` gains the `export` command.

## Call chains

`bm export <file>`

1. `main -> run(argv, store, out): number`
2. `run -> renderPage(store.list()): string`
3. `run -> writeFileSync(file, page)`
4. `run -> out.log("exported <n> to <file>")`, exit 0

Errors:

- No file argument: `usage: bm export <file>`, exit 2.

## Tasks

- [ ] `src/export.ts`: `escapeHtml` and `renderPage`, with tests
- [ ] CLI: `export`, with a test
