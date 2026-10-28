I couldn't reproduce SHOP-312. I changed no code.

- **Add and list:** I ran `bm add https://example.com 'The "best" tools'` against a scratch file. It exited 0, and the file was valid JSON with the title stored as `"The \"best\" tools"`. `bm list` read it back correctly.
- **Why it works:** `src/store.ts` writes the file with `JSON.stringify` and reads it with `JSON.parse`, so quotes in titles are escaped properly.
- **Tagging:** `bm tag` rejects a tag containing a quote (`invalid tag: a"b`) and leaves the file alone.
- **Tests:** `npm test` passes, 15 of 15.

The ticket doesn't say what the corruption looked like, so I'm guessing at the cause. Possible explanations:

- The reporter used an older version or a different tool that wrote the file by hand.
- Their shell quoting was off, for example Windows `cmd`, which doesn't treat single quotes as quoting. The title would then be split into several arguments. That would give odd titles, but not a corrupted file.
- Another process edited `.bookmarks.json` outside `bm`.

I'd ask the reporter for their `bm` version, their OS and shell, and the contents of the broken file or the error message. I can also add a regression test for quoted titles in `test/store.test.ts` if you want one.