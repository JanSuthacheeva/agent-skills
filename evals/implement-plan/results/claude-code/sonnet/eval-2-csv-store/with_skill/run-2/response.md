Task 1 is done and committed (`7c86f78`). I've stopped before task 2 because the plan is wrong about the storage format, and I need your decision.

**The conflict**
- The plan says the store file is "a JSON array of bookmarks", and that `load()` reads old files without a `tags` field as `tags: []`.
- The real store (`src/store.ts`) is CSV with the header `id,url,title,createdAt`.
- A comment there says users open the file in spreadsheets and sync it between machines, so the columns are a public format.
- Adding tags means changing that format, and that is expensive to undo. I haven't built any workaround.

**Options**
1. **Recommended: add a fifth `tags` column to the CSV.**
   - Tags are stored joined with a separator such as `;`, which normalized tags can never contain.
   - `parseRow` reads a missing column as `[]`, so old 4-column files still load. `save()` rewrites them with the new header.
   - The cost is that older `bm` versions reading a new file will ignore or mis-handle the extra column.
2. **Keep the CSV untouched and store tags in a separate sidecar file.** The spreadsheet format is unchanged, but the sync story gets worse: two files that can drift apart.
3. **Switch the store to JSON, as the plan says.** This is a larger migration of a public format, and I wouldn't do it.

If you pick option 1, I'll update the plan's Decision, Data and task 2 text to match, then continue with tasks 2 to 5. The plan's `src/bookmark.ts`, `BookmarkNotFoundError`, `tag` and `listByTag` designs don't change.

Which option do you want?