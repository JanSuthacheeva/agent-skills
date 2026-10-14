I've finished task 1 and stopped there, because the plan describes the store file wrongly.

**Done:** I added `normalizeTag` and `InvalidTagError` in `src/tags.ts`, with unit tests in `test/tags.test.ts` covering case, whitespace, empty input and invalid characters. All 10 tests pass. I ticked the task off in the plan and committed it as `d296cf2`. The `/commit` skill isn't available in this session, so I made the commit with git directly.

**The problem:** The plan says the store is "a JSON array of bookmarks" and that it can gain a `tags` field without changing format. It's actually a CSV file, `~/.bookmarks.csv`, with columns `id,url,title,createdAt`. A comment in `src/store.ts` says people open it in spreadsheets and sync it between machines, so the columns are a public format. Adding tags therefore changes that format, which the plan's review didn't cover. The `.lavish` review page it links to isn't in the repo either.

**My recommendation:** Add a fifth `tags` column at the end, with tags separated by spaces (e.g. `work to-read`).
- Valid tags can only contain `a-z`, `0-9` and `-`, so a space can never appear inside a tag and no extra escaping is needed.
- Files from before this change only have four columns, so `load()` reads the missing column as no tags. No migration is needed, the same as the plan intended.
- Spreadsheets just show one more column on the right. The existing four columns don't change.

**The catch:** If an older `bm` on another synced machine saves the file, it will silently drop all tags. The only fixes are updating `bm` on every machine or keeping tags in a separate file. A separate file avoids touching the public format but splits a bookmark's data across two files that are synced separately, so I prefer the extra column.

Should I go ahead with the trailing space-separated `tags` column? If yes, I'll update the plan's Data section to match and then do tasks 2-5 as written.