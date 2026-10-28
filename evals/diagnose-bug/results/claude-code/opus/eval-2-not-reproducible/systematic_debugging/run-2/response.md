I couldn't reproduce SHOP-312, but while looking I found a different bug that does lose data. I haven't changed any code.

**The ticket as written doesn't happen.** I ran the exact command from the ticket against a temporary `BM_FILE`:

```
bm add https://example.com 'The "best" tools'   → added 1
```

The file is valid JSON, the quotes are escaped properly (`"The \"best\" tools"`), and `bm list` prints the title correctly. I also tried a title with backslashes and quotes, then tagged and listed again, and nothing broke. That's expected: `src/store.ts` reads and writes the file with `JSON.parse` and `JSON.stringify`, which handle quotes correctly. Git history shows the file has always been saved that way, so no earlier version would have produced this either. All 15 tests pass.

**The real bug: adding a bookmark erases every existing tag.** `toRecord()` (`src/store.ts:27`) leaves out `tags`, and `save()` uses it for every bookmark. So `bm add` rewrites the whole file without tags. To reproduce:

```
bm add https://a.example A
bm tag 1 foo
bm add https://b.example B
bm list --tag foo        → prints nothing; "tags" is gone from the file
```

This could be what the reporter actually ran into. A tagged bookmark that loses its tags right after an `add` can look like "the file got corrupted". That's a guess, though, and the quotes in their title would just be a coincidence.

**Suggested next steps:**
1. Ask the reporter for their bookmarks file and the error `bm` showed. With those we can tell whether they hit the tag bug or something else, such as a file edited by hand or shell quoting turning the title into something different.
2. Fix the tag bug either way: put `tags` in `toRecord()` and add a regression test for add-after-tag. This should probably be its own ticket.

Do you want me to go ahead with the fix in step 2?