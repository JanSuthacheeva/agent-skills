I've implemented the bookmark tags plan: all 5 tasks are done and ticked in the plan, each in its own commit. The 21 tests pass. The repo has no lint or type-check step (Node runs the TypeScript directly), so the tests are the only automated check.

**Commits**
1. `80b4cf6` - `normalizeTag` and `InvalidTagError` in `src/tags.ts`
2. `7121568` - `tags` on `Bookmark`; files saved before this change load with `tags: []`
3. `66eaf09` - `BookmarkNotFoundError`, `BookmarkStore.tag` and `BookmarkStore.listByTag`
4. `c28332d` - `bm tag <id> <tag>` and `bm list --tag <tag>`
5. `9e355d6` - final checkbox ticked after the end-to-end run

**End-to-end check:** I ran `npm run bm` against a temp store file that started with a bookmark saved before tags existed.
- `tag 1 ' Legacy '` printed `tagged 1 legacy`.
- Adding a tag a bookmark already has did nothing, as the plan says.
- `list --tag RUNTIME` printed only the bookmarks tagged `runtime`.
- Errors gave the planned messages and exit codes:
  - unknown id: `no bookmark 9`, exit 1
  - non-numeric id: `usage: bm tag <id> <tag>`, exit 2
  - bad tag: `invalid tag: to read`, exit 2
- The saved file had the `tags` arrays in the right order, including on the old bookmark.

**Deviations from the plan (all recorded in the plan file)**
- **`InvalidTagError` constructor:** the plan wrote it as `constructor(readonly raw: string)`, but AGENTS.md forbids that shorthand because Node can't strip it. `raw` is now a regular field set in the constructor; the class works the same for callers.
- **Error handling in the CLI:** I moved the commands into a private `dispatch` function, and `run` now handles the two new errors in one place.
- **Usage errors:** two cases the plan didn't cover now print the existing usage-message style:
  - a missing id or tag on `tag` prints `usage: bm tag <id> <tag>`
  - an unknown option on `list` prints `usage: bm list [--tag <tag>]` (new user-facing text, exit 2)

  The second is the one to look at if you'd rather handle it another way.

Nothing is blocked or left open.

**How it works:** `main.ts` calls `run(argv, store, out)`, which passes the command to `dispatch`.
- **`tag`:** checks the id, cleans up the tag with `normalizeTag` (trim, lowercase, only `a-z`, `0-9` and `-`), then calls `BookmarkStore.tag`. That loads the file, finds the bookmark, adds the tag if it isn't already there, and saves.
- **`list --tag`:** cleans up the tag the same way and prints `BookmarkStore.listByTag`, which filters the loaded bookmarks.

`load()` fills in `tags: []` for older records, so no migration is needed. Invalid tags exit with 2 and unknown ids with 1.

Nothing has been pushed.