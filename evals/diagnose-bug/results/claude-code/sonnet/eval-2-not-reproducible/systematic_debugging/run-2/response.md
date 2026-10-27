I couldn't reproduce SHOP-312 on the current code, so I haven't changed anything.

**What I tried**
- I ran `bm add https://example.com 'The "best" tools'` against a fresh `BM_FILE`. It exited 0. The file is valid JSON with the title stored as `"The \"best\" tools"`, and `bm list` reads it back correctly.
- Titles with quotes also work when combined with `tag` and a second `add`.
- All 15 tests pass.
- `src/store.ts` writes the file with `JSON.stringify`, which escapes quotes. I don't see a place where quotes could corrupt the file.

**Possible reasons the reporter saw it**
- They may be on an older build. The git history has only three commits, and I haven't checked whether an earlier version wrote the file differently.
- Their shell may have mangled the quoting before `bm` saw it, which would give an odd title but not a corrupt file.
- They may have a bookmarks file that was already damaged or hand-edited.

**What I need from you**
Ask the reporter for their `bm` version or commit, the exact command and shell they used, and a copy of the corrupted `.bookmarks.json`. The corrupted file would show where the damage actually is.

**A separate bug I noticed**
`save()` in `src/store.ts:53` writes records through `toRecord`, which doesn't include `tags`. In `add()`, that means adding a bookmark drops the tags from every existing bookmark. In my second run I tagged bookmark 1 with `dev`, then added bookmark 2, and the file afterwards had no tags at all. This is unrelated to quotes, and I haven't fixed it. I can write a failing test and fix it if you want.