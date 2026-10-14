I finished task 1 and stopped at task 2. The plan assumes something about the store file that isn't true, and the fix changes a public file format, so I need your decision first.

**Done**
- Task 1: `normalizeTag` and `InvalidTagError` in `src/tags.ts`, with 6 unit tests. All 11 tests pass; nothing was failing before I started. Committed as `9186844`. The `/commit` skill isn't available in this repo, so I committed with plain git in the existing `bm: ...` style.

**Blocked: task 2 (and so tasks 3-5)**
The plan says the store file is "a JSON array of bookmarks" that just gains a `tags` field. It's actually CSV (`~/.bookmarks.csv`, header `id,url,title,createdAt`). A comment in `src/store.ts` says users open it in spreadsheets and sync it between machines, so the columns are part of the public format. Tags can't be added without changing that format.

Options:
1. **Add a fifth `tags` column** holding the tags joined by spaces, e.g. `work to-read`. Old files have no fifth field and load as `tags: []`, so no migration is needed. It still opens cleanly in a spreadsheet. A valid tag can only contain `a-z`, `0-9` and `-`, so a space separator never clashes with a tag and the column never needs quoting.
2. **Switch the file to JSON**, as the plan assumed. This breaks the spreadsheet use, needs a migration for existing `.csv` files, and probably a new file name.
3. **Keep tags in a separate file**. This keeps the CSV untouched but splits one record across two files that sync separately.

I recommend option 1. It keeps the "no migration" property the plan wanted, and a bookmark stays one row. The cost: a machine running the old version that saves the file will drop the column, and tags with it. If that's acceptable, I'll update the plan's Data section to match and carry on with tasks 2-5 as written.

I've noted the block under task 2 in the plan.