Bookmark tags are implemented as the plan describes, and `bm tag <id> <tag>` and `bm list --tag <tag>` both work. `npm test` passes (17 tests). I also ran `add`, `tag` and `list --tag` through `npm run bm` against a temp store file. The output was correct, and an unknown id exits 1 with `no bookmark 5` and an invalid tag exits 2 with `invalid tag: a b`.

I checked the plan's tasks off in `docs/plans/2026-10-14-bookmark-tags.md`. The work is in two commits:
- `ffeb430` adds `normalizeTag` and `InvalidTagError`.
- `f17c7b9` adds `tags` on `Bookmark`, the store methods and the CLI.

- **Commit skill:** the `/commit` skill isn't available in this session, so I committed with plain `git`.
- **Normalization:** the CLI normalizes the tag once to print it, and the store normalizes it again. Normalizing is idempotent, so this is harmless.
- **`list --tag` without a value:** this prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover that case, so I chose it.