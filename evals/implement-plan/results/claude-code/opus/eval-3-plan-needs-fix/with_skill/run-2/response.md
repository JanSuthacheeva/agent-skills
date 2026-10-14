I've built all five tasks in the plan and ticked them all. The full suite passes (21 tests, up from 4), and the real `npm run bm` commands work against a temp store file.

**Commits**
1. `2f8bc7b` - `normalizeTag` and `InvalidTagError` in `src/tags.ts`
2. `81b88e3` - `Bookmark.tags`; new bookmarks start with `[]`, and `load()` reads files without tags as `[]`
3. `83ca082` - `BookmarkNotFoundError`, `BookmarkStore::tag` and `listByTag`
4. `5945b58` - `bm tag <id> <tag>` and `bm list --tag <tag>`
5. `32d7a0c` - the end-to-end check, and the plan updated to match what was built

**End-to-end check:** I added two bookmarks and tagged #2 with `" Work "`, which printed `tagged 2 work`. Tagging it `work` again changed nothing. `list --tag WORK` printed only `2  Deno  https://deno.com`. The error cases behaved as the plan says:
- an unknown id printed `no bookmark 9` (exit 1)
- an invalid tag printed `invalid tag: to do` (exit 2)
- a non-numeric id printed the usage line (exit 2)

A store file written before tags existed also loaded, could be tagged, and was filtered correctly through the CLI.

**Changes from the plan**
- **`InvalidTagError` constructor:** the plan used `constructor(readonly raw: string)`, but AGENTS.md doesn't allow that form because Node can't strip it. I declared `raw` as a normal field instead; it's still public and works the same. The plan's signature is updated.
- **Missing arguments:** the plan didn't say what happens if they're left out, so I chose:
  - `bm tag 1` with no tag prints the same usage line as a non-numeric id (exit 2).
  - `bm list --tag` with no tag prints `usage: bm list [--tag <tag>]` (exit 2).

  Both are now in the plan's Errors section. Tell me if you'd rather word or handle them differently.
- **Commits:** the `/commit` skill isn't available here, so I used plain `git commit` in the repo's existing `bm: ...` style.

Nothing is blocked. The repo has no lint or type-check setup, so the tests were the only checks I could run. Nothing is pushed.

**How it works**
- **Tagging:** `main` passes the arguments to `run(argv, store, out)` in `src/cli.ts`. For `tag`, `run` checks the id, cleans up the tag with `normalizeTag` (trim, lowercase, only `a-z0-9-` allowed), then calls `store.tag(id, tag)`. That loads the file, adds the tag if the bookmark doesn't have it yet, and saves.
- **Listing:** for `list --tag`, `run` cleans up the tag the same way, then prints `store.listByTag(tag)` in the normal `list` format.
- **Errors:** a small `guard` helper in `src/cli.ts` turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1. The store only ever receives cleaned-up tags, and the CLI never touches the file directly.