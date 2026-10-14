I implemented the bookmark tags plan and ticked off all five tasks. All 22 tests pass, and I ran the real CLI against a temp store file to check `tag` and `list --tag` end to end.

**One fix to the plan:** it declared `InvalidTagError` with `constructor(readonly raw: string)`. That shorthand (a "parameter property") is banned by `AGENTS.md`, and I confirmed Node 22 refuses to run it. I made `raw` an ordinary field set in the constructor instead and updated the plan to match. `BookmarkNotFoundError` follows the same pattern and also keeps the `id`, which the CLI uses for its `no bookmark <id>` message.

**What's in place:**
- **`src/tags.ts`:** `normalizeTag` trims and lowercases the tag, then rejects it with `InvalidTagError` if it's empty or has anything other than `a-z`, `0-9` and `-`.
- **`src/store.ts`:**
  - New bookmarks start with `tags: []`, and `load()` treats files written before tags existed as untagged.
  - `tag(id, tag)` throws `BookmarkNotFoundError` for an unknown id and does nothing if the bookmark already has that tag.
  - `listByTag(tag)` returns only the bookmarks with that tag.
- **`src/cli.ts`:** `bm tag <id> <tag>` and `bm list --tag <tag>`, with the messages and exit codes from the plan.

**One choice the plan didn't cover:** `list` with an argument it doesn't recognise (e.g. `list --tags x` or `list --tag a b`) now prints `usage: bm list [--tag <tag>]` and exits 2. Before this change `list` silently ignored extra arguments.

**Commits:** the `/commit` skill isn't available in this session, so I made the five commits directly with `git`, one per task. Nothing is pushed.

**Also not done:** the plan's review page, `.lavish/bookmark-tags-implementation.html`, isn't in the repo, so I didn't look at it.