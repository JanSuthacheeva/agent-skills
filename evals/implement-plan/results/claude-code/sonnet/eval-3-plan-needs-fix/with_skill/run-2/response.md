All five tasks are built and committed, and the full suite passes (21 tests). The repo has no lint or type-check script, so I ran neither. The `/commit` skill wasn't available, so I used plain git commits.

**Commits**
- `7ccc98e` - `normalizeTag` and `InvalidTagError`
- `ca68e3c` - `tags` on `Bookmark`; `load()` reads missing tags as `[]`
- `c55d6ba` - `BookmarkNotFoundError`, `BookmarkStore::tag` and `listByTag`
- `bc88aaf` - the `tag` command and `list --tag`
- `4b4eab1` - ticked the end-to-end check in the plan

**End-to-end check**
I ran the real `npm run bm` against a temp store file:
- **Tagging:** `tag 1 Work` printed `tagged 1 work` and exited 0, and tagging again was a no-op.
- **Filtering:** `list --tag work` printed only bookmark 1.
- **Errors:** an invalid tag printed `invalid tag: a b` and exited 2, and an unknown id printed `no bookmark 9` and exited 1.
- **Stored file:** it still holds a JSON array, now with a `tags` field.

**Deviations from the plan** (all in the plan file now)
- **`InvalidTagError.raw`:** the plan's `constructor(readonly raw: string)` is a parameter property, which `AGENTS.md` forbids. I used an explicit `raw` field instead.
- **`run` structure:** it now wraps a private `dispatch` and maps both errors to messages and exit codes in one place.
- **`list --tag` with no value:** I added `usage: bm list [--tag <tag>]` with exit 2, which the plan didn't specify. Without it the command silently listed everything. Say if you'd rather have different behaviour.
- **Task 3 tests:** I wrote the store tests together with the implementation, so I didn't see them fail first. The other tasks did fail first for the expected reason.

**How it works**
- **Entry point:** `main` calls `run`, which hands off to `dispatch`.
- **`tag`:** `dispatch` validates the id, calls `normalizeTag`, then `BookmarkStore::tag`. That loads the bookmarks, adds the tag if it is new, and saves.
- **`list --tag`:** `dispatch` normalizes the tag and calls `listByTag`, then prints each bookmark in the normal list format.
- **Errors:** `InvalidTagError` and `BookmarkNotFoundError` are caught in `run`.
- **Old store files:** `load()` fills in `tags: []`, so existing files need no migration.

Nothing is blocked, and I haven't pushed.