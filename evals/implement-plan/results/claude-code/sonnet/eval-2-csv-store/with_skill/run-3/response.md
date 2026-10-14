Task 1 is done and committed (`47cb484`). I've stopped before task 2 because the plan's storage assumption doesn't match the code.

**Task 1.** `normalizeTag` and `InvalidTagError` are in `src/tags.ts`, with five tests in `test/tags.test.ts`. They failed first because the module was missing, then passed. The full suite passes with 10 tests, and I ticked the task in the plan.

**Blocked: tasks 2 to 5.** The plan says the store file "keeps its format: a JSON array of bookmarks" and that `load()` reads old files as `tags: []`. In fact the store is CSV (`.bookmarks.csv`, header `id,url,title,createdAt`). A comment in `src/store.ts` says users open it in spreadsheets and sync it between machines, so the columns are a public format. Adding tags changes what is stored, and I'm not going to pick a format without you.

Options:
1. **Add a `tags` column to the CSV.** This is my recommendation.
   - The header becomes `id,url,title,createdAt,tags`, and tags are joined with `;`. That is safe because tags are limited to `a-z`, `0-9` and `-`.
   - Old files with four columns load as `tags: []` through the existing default in `parseRow`. This matches the plan's "no migration" intent, and spreadsheets and sync keep working.
   - The extra column is a small format change that older `bm` versions would ignore or choke on, depending on their parser.
2. **Store tags in a separate sidecar file.** The CSV stays byte-identical. The cost is two files that can drift apart, and it breaks syncing a single file.
3. **Switch the store to JSON, as the plan literally says.** I advise against it. It breaks the spreadsheet and sync use the code comment promises.

If you pick option 1, I'll update the plan's Decision and Data sections to say CSV and continue with tasks 2 to 5. Which option do you want?