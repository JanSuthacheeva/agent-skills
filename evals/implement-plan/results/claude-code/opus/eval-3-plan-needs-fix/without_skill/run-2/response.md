Bookmark tags are implemented. All 23 tests pass, and I ran `add`, `tag` and `list --tag` with `npm run bm` against a temp store file and the output was correct. There are five commits, one per plan task, plus one to update the plan.

**One change from the plan:** it specified `InvalidTagError` with `constructor(readonly raw: string)`. That syntax makes Node crash when it loads the file (I tried it on Node 22.23), and AGENTS.md rules it out. So `raw` is now a normal `readonly raw: string` field set in the constructor. Code using the class sees the same thing. I updated the plan to match and ticked off its tasks.

**What works:**
- `bm tag <id> <tag>` cleans up the tag (`" Runtime "` becomes `runtime`) and prints `tagged <id> <tag>`. Adding a tag the bookmark already has does nothing.
- `bm list --tag <tag>` prints in the same format as `list`.
- Errors give the messages and exit codes from the plan:
  - invalid tag: `invalid tag: <raw>`, exit 2
  - unknown id: `no bookmark <id>`, exit 1
  - non-numeric id: the usage message, exit 2
- Store files written before tags existed load as `tags: []` and can be tagged with no migration. I checked this with a hand-written old-format file.

**Small additions the plan didn't cover:**
- `list --tag` with no tag, or with extra arguments, prints `usage: bm list [--tag <tag>]` and exits 2. This means `list` now rejects arguments it used to ignore silently.
- `tag` with a missing tag or extra arguments prints the `tag` usage message and exits 2.

The plan links to a review page, `.lavish/bookmark-tags-implementation.html`, which isn't in the repo.