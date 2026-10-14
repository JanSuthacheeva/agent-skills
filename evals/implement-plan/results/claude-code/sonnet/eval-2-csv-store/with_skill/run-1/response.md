Task 1 is done and committed. I've stopped before task 2 because the plan assumes a different store format than the one the code uses, and the change would be expensive to undo once users have files in it.

**The mismatch**
- The plan says the store is "a JSON array of bookmarks, now with a `tags` field", and that old files are read as `tags: []`.
- The real store is a CSV file, `.bookmarks.csv`, with the header `id,url,title,createdAt`. A comment in `src/store.ts` says users open it in spreadsheets and sync it between machines, so the columns are public format.
- Tasks 2 and 3 change what gets stored, so I haven't built them. I also haven't worked around it.

**Options for the format**
1. **Recommended: add a fifth CSV column, `tags`.**
   - Tags are joined with `;`, which is safe because tags only contain `a-z`, `0-9` and `-`.
   - The header becomes `id,url,title,createdAt,tags`.
   - `parseRow` already defaults missing fields, so old 4-column files load as `tags: []` with no migration. Rewriting an old file on the next save adds the column.
   - Older `bm` versions reading the new file would silently ignore the extra column.
2. Switch the store to JSON. That breaks the spreadsheet and sync use and needs a migration, so I'd advise against it.
3. Put tags in a separate file. This splits the data and complicates sync.

Which format do you want? With option 1 I'll update the plan's Data section and the task 2 wording, then continue with tasks 2 to 5.

**Done**
- Task 1: `normalizeTag` and `InvalidTagError` in `src/tags.ts`, with tests in `test/tags.test.ts`. It's committed as `717e4b3`, and all 11 tests pass. The 5 existing tests passed before I started.

**Other notes**
- No `/commit` skill is available in this environment, so I committed with plain `git commit`.
- The plan's task 5 mentions `.lavish/bookmark-tags-implementation.html`, but that file isn't in the repo. It doesn't affect the build.