Bookmark tags are implemented, and all five plan tasks are done and checked off. `npm test` passes (18 tests). I also ran `add`, `tag` and `list --tag` against a temp store file. They gave the expected output, including exit 1 for an unknown id and exit 2 for an invalid tag.

**Deviation from the plan:** the plan says the store is a JSON array, but `src/store.ts` is a CSV file, and its comment says users open it in spreadsheets and sync it. I kept the plan's intent and stored tags in a new trailing `tags` column, joined with `;`. That is safe because tags can only contain `a-z`, `0-9` and `-`.
- Old four-column files read as `tags: []` and need no migration.
- Older versions of the tool ignore the extra column when reading.
- The plan's "JSON array" wording is still in `docs/plans/2026-10-14-bookmark-tags.md`. You may want to correct it.

**Commits:**
- `Add normalizeTag and InvalidTagError`
- `Store bookmark tags in a trailing CSV column`
- `Add bm tag and list --tag`
- `docs: check off bookmark tags plan`

I used plain `git commit` because no `/commit` skill is available in this session.