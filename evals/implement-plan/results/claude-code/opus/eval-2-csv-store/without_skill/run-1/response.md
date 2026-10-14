I finished task 1 and stopped before tasks 2 to 5, because the plan's description of the store file doesn't match the code.

**Done:** `normalizeTag` and `InvalidTagError` are in `src/tags.ts`, with tests for case, whitespace, empty input and invalid characters. All 10 tests pass. I ticked the task in the plan and committed it as `tags: add normalizeTag and InvalidTagError`.

**The problem:** The plan says "The store file keeps its format: a JSON array of bookmarks, now with a `tags` field". The store is actually a CSV file (`.bookmarks.csv`) with the header `id,url,title,createdAt`. `src/store.ts:9` says the columns are part of the public format, because users open the file in spreadsheets and sync it between machines. So tags can't be stored without changing that public format. The plan treated this as a non-change, so I don't think I should decide it alone.

**Recommendation:** Add a trailing `tags` column, with the tags joined by spaces (e.g. `work to-read`).
- Old files have no `tags` field, so they load as `tags: []`. That keeps the plan's "no migration" promise.
- Spaces can't appear in a valid tag, so splitting is unambiguous and the field doesn't need quoting. It also reads cleanly in a spreadsheet.
- Existing columns keep their positions, so spreadsheet formulas and imports keyed on them still work.
- **Cost:** the header changes. A machine still running an older `bm` would drop the tags the next time it saves a file it got through sync. I'd note this in the commit body and correct the plan's Data section to match.

**Alternative:** Keep tags in a separate file next to the store, so the public CSV stays exactly as it is. But then tags would no longer sync with the CSV, and the store would have two files to keep consistent. I think that's worse.

Should I go ahead with the trailing `tags` column?