Bookmark tags are implemented and all 18 tests pass; the project has no lint or type-check script, so I ran neither. The tests were green before I started (4 of 4).

**Tasks and commits**
1. `normalizeTag` and `InvalidTagError` in `src/tags.ts`: "Add normalizeTag and InvalidTagError".
2. `Bookmark.tags`, new bookmarks created with `tags: []`, and `load()` reading missing tags as `[]`: "Store tags on bookmarks, reading missing tags as empty".
3. `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`: "Add BookmarkStore tag and listByTag".
4. `bm tag <id> <tag>` and `bm list --tag <tag>`: "Add bm tag and list --tag".
5. The end-to-end check, with the plan ticked: "Tick end-to-end check in bookmark tags plan".

**End-to-end check.** I ran `npm run bm` against a temp store file:
- `tag 2 " Work "` printed `tagged 2 work`, and tagging it again was a no-op with exit 0.
- `list --tag work` printed only bookmark 2.
- An invalid tag printed `invalid tag: a b` with exit 2.
- An unknown id printed `no bookmark 9` with exit 1.
- A non-numeric id printed `usage: bm tag <id> <tag>` with exit 2.
- The store file holds `tags` on every bookmark.

**Deviations**
- In task 3 I wrote the tests and the implementation together instead of watching the tests fail first. The tests pass and cover the duplicate tag and unknown id cases the plan names.
- The plan doesn't say what `list --tag` with no value should do. It runs the value through `normalizeTag`, so it prints `invalid tag: ` with exit 2. I added a test for this.
- `/commit` isn't available in this environment, so I used plain `git commit`.
- I added a private `withTagErrors` helper in `src/cli.ts` that maps the two error classes to messages and exit codes.

Nothing is blocked and I haven't pushed.

**How it works**
- `main` calls `run(argv, store, out)` in `src/cli.ts`.
- For `tag` and `list --tag`, `run` calls `normalizeTag`, then `BookmarkStore::tag` or `listByTag`, inside `withTagErrors`.
- `BookmarkStore::tag` loads the bookmarks, adds the tag if it isn't already there, saves, and returns the bookmark. `load()` fills in `tags: []` for files written before this change.
- `run` prints the result through `out`.