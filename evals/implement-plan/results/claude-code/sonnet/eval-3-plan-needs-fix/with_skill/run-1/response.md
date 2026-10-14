All five tasks are done and committed, and `npm test` passes (22 tests). The repo has no lint or type-check scripts, so I ran neither. I didn't push.

**Commits**
1. `Add normalizeTag and InvalidTagError`
2. `Store tags on bookmarks, read missing tags as empty`
3. `Add BookmarkStore tag and listByTag`
4. `Add bm tag and bm list --tag`
5. `Tick end-to-end check in plan`

**End-to-end check:** I ran `npm run bm` against a temp store file.
- `add` twice, then `tag 2 " Work "` printed `tagged 2 work` with exit 0.
- `list --tag work` printed only bookmark 2.
- `tag 2 "a b"` printed `invalid tag: a b` with exit 2.
- `tag 9 x` printed `no bookmark 9` with exit 1.
- The store file now has `"tags": []` on new bookmarks.

**Deviations from the plan (the plan file is updated to match)**
- `InvalidTagError` now declares `raw` as a normal field. The plan used `constructor(readonly raw: string)`, a parameter property, which AGENTS.md forbids because Node's type stripping can't handle it.
- I added a usage error for a malformed `--tag`, such as a missing value or extra arguments: `usage: bm list [--tag <tag>]`, exit 2. It is in the plan's error list.
- `bm list` with stray arguments, for example `list foo`, now also prints that usage error and exits 2. Before, it ignored them and listed everything.
- `BookmarkStore.tag` and `listByTag` also call `normalizeTag`, on top of the CLI doing so. It is harmless and means the store enforces valid tags by itself.

**Process slips**
- In task 2 a failed `sed` left a test import missing, so the first commit had a failing test. I fixed the import and amended that commit before moving on.
- In task 3 I wrote the tests and the implementation together, so I never saw those tests fail first.

**How it works**
- `main.ts` calls `run(argv, store, out)` in `cli.ts`, which dispatches `tag` and `list --tag` to small helpers.
- The helpers call `normalizeTag` in `tags.ts`, then `BookmarkStore.tag` or `listByTag`.
- The store reads the JSON file with `load()` (a missing `tags` field becomes `[]`), changes it, and writes it back with `save()`.
- The CLI prints the result. `fail()` turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1.

Nothing is blocked or open.