I stopped after task 1 of 5. The plan assumes the store file is a JSON array, but it's actually a CSV file.

**Done:** task 1, commit `a321f3f`. `normalizeTag` and `InvalidTagError` are in `src/tags.ts` with 6 unit tests, and the full suite passes (11/11). There was no `/commit` skill available, so I committed with plain git, following the repo's `bm: ...` message style.

**Blocked:** task 2. The plan's Data section says "the store file keeps its format: a JSON array of bookmarks". But `src/store.ts` writes CSV to `~/.bookmarks.csv` with the header `id,url,title,createdAt`. A comment there says users open the file in spreadsheets and sync it between machines, so the columns are part of the public format. Storing tags changes that format, so I haven't built anything for it. I've marked task 2 as blocked in the plan, with this reason.

**My recommendation:** add a fifth column, `tags`, holding the tags separated by spaces (e.g. `work to-read`). The header becomes `id,url,title,createdAt,tags`.
- **Reading:** a row with only four fields, from a file written before tags existed, reads as `tags: []`. No migration is needed, which matches the plan's intent.
- **Quoting:** valid tags can only contain `a-z`, `0-9` and `-`, so the cell never needs quoting.
- **What users notice:** they see one new column. Files written with tags can't be read correctly by older copies of `bm` on other synced machines: their parser ignores the extra field, then drops the tags on the next save.

Should I go ahead with that column format? If so, I'll update the plan's Data section to match and build tasks 2-5.