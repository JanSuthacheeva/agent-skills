I couldn't reproduce SHOP-312 on the current code (`0a23742`). I did find a separate bug that loses data, plus one that could explain the "bm stops working" part.

**Quotes work.** `bm add https://example.com 'The "best" tools'` writes valid, correctly escaped JSON (`"The \"best\" tools"`), and `list` shows it back unchanged. I also tried backslashes, mixed escapes, and adding more bookmarks after one with quotes, and none of them broke the file. The store has always written the file with `JSON.stringify` (`src/store.ts`), so there's no hand-built JSON in the history that could have caused this. Quotes in a tag are rejected as `invalid tag` (exit 2), which is the intended behaviour, not corruption.

**What I did find:**

1. **Adding a bookmark erases every tag.** `toRecord()` in `src/store.ts` doesn't include `tags`, and `save()`, which `add()` uses, writes through it. Only `tag()` puts tags back in. To reproduce: `add A` → `tag 1 work` → `add B` → `list --tag work` returns nothing, and the file has no tags left. If the reporter tagged things, they might have described this as the file being "corrupted". That's a guess, but this bug is real either way.
2. **A malformed file crashes bm with a raw stack trace.** If the file isn't valid JSON (for example, someone hand-edited it and typed `"The "best" tools"` without escaping), `load()` throws an unhandled `SyntaxError` with a stack trace on every command. That would look exactly like "bm stops working". bm can't produce that file itself, but it should fail with a clear message and an exit code instead of crashing.

**Suggested next steps:**
- Ask the reporter for their bm version or commit, the exact error, and a copy of the bad file. My guess is it was hand-edited, written by an older build, or they're actually seeing the tag loss in point 1.
- Fix point 1 by including `tags` in `toRecord`. Then the special case in `tag()` goes away and it can just call `save()`. Add a regression test for add-after-tag.
- Optionally, turn parse failures in `load()` into an error class that the CLI maps to a clean message.

Should I fix point 1, and file it as its own ticket or under SHOP-312?