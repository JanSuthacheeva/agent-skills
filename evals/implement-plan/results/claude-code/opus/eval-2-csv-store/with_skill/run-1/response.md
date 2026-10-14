I built Task 1 and committed it. I stopped before Task 2 because the plan's design for storing tags doesn't fit the code.

**Done**
- Task 1: added `normalizeTag(raw)` and `InvalidTagError` in `src/tags.ts`, with tests for case, whitespace, empty input, invalid characters and the error message. Commit `9bf273c` (`bm: add tag normalization`), with the box ticked in the plan.
- All 10 tests pass. The 5 that existed before also passed when I started. There's no lint or type-check setup.
- The `/commit` skill isn't available in this session, so I committed with git using the repo's `bm: ...` message style.

**Blocked: Task 2, how tags are stored**

The plan says the store file is a JSON array and that tags are just a new field on each object. In fact the store is CSV: `.bookmarks.csv` with the header `id,url,title,createdAt`. `src/store.ts:9` says users open it in spreadsheets and sync it between machines, so its columns are a public format. Storing tags means changing that format, which is hard to undo once shipped, so I'm not choosing it on my own.

**My recommendation:** add a fifth column, `tags`, with the tags separated by spaces, e.g. `3,https://nodejs.org,Node,2026-10-14T...,work read-later`.
- Tags can only contain `a-z`, `0-9` and `-`, so a space can never be part of a tag. The field never needs CSV quoting and stays readable in a spreadsheet.
- Old files with the 4-column header load as `tags: []`, so the plan's "no migration" still holds.
- **Risk:** if a synced machine still runs the old version of bm, it ignores the fifth column and drops it the next time it saves. Tags written on the new version would disappear without any error. I think that's acceptable for a local tool, but you should decide.

**Alternatives**
- Switch the file to JSON as the plan says. This breaks the spreadsheet use and the public format, and would need a real migration.
- Keep tags in a separate file next to the CSV. The CSV stays untouched, but there are two files to keep in sync.

If you agree with the extra column, I'll update the plan's Data section to match and build Tasks 2-5.