I couldn't reproduce SHOP-312, so I haven't written a fix plan. I didn't change any code, and the scratch files I used are deleted.

**What I tried.** I pointed `BM_FILE` at a temporary file and ran the CLI both through `npm run bm` and directly with `node src/main.ts`:
- **The ticket's exact command:** `bm add https://example.com 'The "best" tools'` returned `added 1` and exit code 0. The file is valid JSON with `"title": "The \"best\" tools"`, and `bm list` prints `1  The "best" tools  https://example.com`.
- **Variations:** I also tried quotes mixed with a backslash (`He said "hi" \ back`), curly quotes (`“best”`), a title passed as separate words with the quotes in the middle one, and quotes in the URL (`https://e.com/?q="a"`). All were stored correctly and listed without errors.
- **History:** every version of `src/store.ts` in git has written the file with `JSON.stringify`, which escapes quotes correctly. No version of `bm` in this repo writes quotes in a way that would break the file.

**Something else I noticed, possibly related.** Adding a bookmark deletes the tags on every existing bookmark. `save()` → `toRecord()` (`src/store.ts:27`) never writes the `tags` field. Only `tag()` writes it, through its own path. To reproduce: `bm tag 1 tools`, then `bm add …`, then `bm list --tag tools` prints nothing. If the reporter had tagged bookmarks before adding the quoted one, this might look like "the file is corrupted and bm stops working". The quotes would then be a coincidence. That's a guess, and it's a separate bug that probably needs its own ticket.

**What would help:**
1. The reporter's actual bookmarks file (`~/.bookmarks.json`) after the corruption, or the error `bm` prints when it "stops working".
2. Which `bm` they're running (version or commit, and whether it's from this repo) and their shell or platform. Shell quoting on Windows `cmd`, for example, behaves differently.
3. The commands they ran just before it broke, especially any `bm tag`.

Do you want me to write the tag-loss bug up as its own diagnosis and fix plan while we wait for those details?