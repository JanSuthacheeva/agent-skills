All five plan tasks are done and committed, and the full suite passes (17 tests). The project has no lint or type-check script, so I only ran `npm test`. I did not push.

**Commits**
- `bab28b9`: `normalizeTag` and `InvalidTagError`
- `1277c11`: `tags` on `Bookmark`; legacy files load with `tags: []`
- `aacd23d`: `BookmarkNotFoundError`, `BookmarkStore.tag` and `listByTag`
- `3aeda97`: `bm tag` and `bm list --tag`
- `c7bf4fa`: tick the end-to-end check in the plan

**End-to-end check**
I ran the real CLI against a temp store file:
- `tag 1 " Work "` printed `tagged 1 work`, and tagging again was a no-op with exit 0.
- `list --tag work` showed only bookmark 1.
- A bad tag printed `invalid tag: bad!` with exit 2.
- An unknown id printed `no bookmark 9` with exit 1.
- A non-numeric id printed the usage line with exit 2.

**Deviations (the plan is updated for the first)**
- `InvalidTagError` uses an explicit `raw` field instead of `constructor(readonly raw)`. AGENTS.md forbids parameter properties so Node can strip the types. The public shape is unchanged.
- `run` now wraps a new `dispatch` function and maps `InvalidTagError` (exit 2) and `BookmarkNotFoundError` (exit 1) in one place. This is internal only, and the plan does not name it.
- The plan didn't cover `list` with extra arguments, or `--tag` with no value. I made both print `usage: bm list [--tag <tag>]` with exit 2. `list --tag ""` prints `invalid tag: ` with exit 2. This is the only user-visible behaviour the plan didn't specify, so tell me if you want it different.
- The `/commit` skill isn't available here, so I used plain `git commit`.

Nothing is blocked.

**How it works**
`main.ts` calls `run(argv, store, out)`, which passes the command to `dispatch`. For `tag` and `list --tag`, `dispatch` calls `normalizeTag`, then `BookmarkStore.tag` or `listByTag`. `tag` does `load()`, finds the bookmark (or throws `BookmarkNotFoundError`), adds the tag if it's new, then `save()`. `load()` reads a missing `tags` field as `[]`, so old store files keep working. Errors reach `run`'s catch block, which prints the message and returns the exit code.