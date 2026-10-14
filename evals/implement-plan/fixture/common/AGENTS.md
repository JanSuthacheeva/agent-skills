# bm

A command line bookmark manager. TypeScript run directly by Node 22, no
dependencies and no build step.

- `npm test` runs the tests (node:test). `npm run bm -- <args>` runs the CLI.
- `src/cli.ts` parses arguments and prints; `src/store.ts` owns the file.
  The CLI never touches the file directly.
- Errors are classes extending `Error`; the CLI maps them to messages and
  exit codes (1 for not found, 2 for bad input).
- Imports use the `.ts` extension. No parameter properties or enums, so
  Node can strip the types.
