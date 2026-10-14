I finished task 1 and stopped before task 2. The plan assumes the wrong storage format, and fixing that means changing a file format users rely on, which you should decide.

**Done:** `src/tags.ts` now has `normalizeTag` and `InvalidTagError`, with unit tests for case, whitespace, empty input, invalid characters and keeping the raw input. All 11 tests pass. I committed it as `b8f9759` and ticked the task in the plan. There's no `/commit` skill in this session, so I committed with plain `git`.

**The problem:** the plan says the store file is "a JSON array of bookmarks" and that it "keeps its format". It's actually a CSV, `~/.bookmarks.csv`, with the header `id,url,title,createdAt`. `src/store.ts` says the columns are a public format because users open the file in spreadsheets and sync it between machines. So tags can't be stored without changing that format, which the plan says won't happen. (The review page `.lavish/bookmark-tags-implementation.html` isn't in the repo either.)

**Options:**

1. **Recommended: add a `tags` column at the end.** The header becomes `id,url,title,createdAt,tags`, and tags in a row are separated by spaces, e.g. `work to-read`. Spaces are safe because valid tags can't contain them. Rows without the column load as `tags: []`, so old files need no migration, as the plan intended. Spreadsheets and scripts that read columns by position keep working.
   - The catch: an older copy of `bm` on another synced machine ignores the extra column, and the next time it writes the file it deletes everyone's tags. If that matters, a version check would need adding.
2. **Keep tags in a separate file next to the CSV.** The CSV doesn't change at all. But there are two files to keep in step and sync, and nothing is gained if users never use older versions.
3. **Switch the store to JSON, as the plan describes.** This breaks the spreadsheet use and needs an actual migration. I don't recommend it.

Should I go ahead with option 1 for tasks 2 to 5? I'd also update the plan's "Data" section to describe the CSV column.