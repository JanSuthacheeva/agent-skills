I couldn't reproduce SHOP-312 on the current code, so I haven't changed anything.

**What I ran** (against a scratch file via `BM_FILE`):
- `bm add https://example.com 'The "best" tools'` exited 0 and wrote valid JSON with the title stored as `"The \"best\" tools"`.
- `bm list` read it back correctly.
- `bm tag` on that bookmark also worked. A tag containing a quote (`a"b`) was rejected cleanly with exit 2 and the file was left untouched.
- `npm test` passed, 15 of 15.

**Why it shouldn't break:** the only code that writes the file is `#write` in `src/store.ts:84`, and it uses `JSON.stringify`, which escapes quotes. The only reader is `JSON.parse` at `src/store.ts:49`. Nothing hand-builds JSON, and there are no other writers.

**What could explain the report** (none of these are verified):
- The reporter ran an older build. The history is short (3 commits), and I didn't check whether an earlier version wrote the file differently.
- Their shell mangled the quoting, for example on Windows `cmd`, where single quotes aren't quote characters. The title would then arrive split into several arguments or with stray characters. That would be a different bug from the ticket's.
- Their bookmarks file was already corrupted or edited by hand before they added the bookmark.

I can't tell which from here. To go further I need the reporter's version or commit, their shell or OS, and the actual error message or the corrupted file. If you can get any of those, I'll pick it up from there. I can also add a regression test that round-trips a quoted title through the store, which would guard against this in future.