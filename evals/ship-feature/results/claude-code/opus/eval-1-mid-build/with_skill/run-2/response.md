I've built and reviewed the bookmark tags feature on `feature/bookmark-tags`. The reviewer left two items open, and I need you to decide them before I open the merge request.

**Where it stands:**
- **Build:** a fresh agent finished tasks 2-5, and I checked the result myself: all boxes in the plan are ticked and 18 of 18 tests passed.
- **Review:** a separate fresh agent found one bug and fixed it. `bm list --tag work extra` printed the list instead of the usage message (fix in `7707ef6`). It's now 19 of 19 tests passing. The review is written into the plan (`454ac8b`).
- **Your call:** the build agent changed four small things from the plan, and the plan file is updated to match:
  - `bm tag <id>` with no tag prints the usage message and exits 2.
  - `bm list` with any extra argument now prints `usage: bm list [--tag <tag>]` and exits 2. Before, it ignored the extra argument. This is the one users would notice.
  - The argument parsing moved into a private `dispatch()`, and `run()` only turns errors into messages and exit codes.
  - Tagging a bookmark with a tag it already has doesn't rewrite the file.

**Open items:**

1. **Extra arguments to `tag`:** `bm tag 1 to do` tags `to` and silently drops `do`.
   - The options are to reject extra arguments with the usage message and exit 2, or keep ignoring them.
   - I recommend rejecting them, which matches how `list` behaves now.

2. **Corrupt store file:** a corrupt file crashes with a raw `SyntaxError`. This was already the case on `main`, and no data is lost.
   - The options are to fix it here or leave it.
   - I recommend fixing it here. I'd add a `CorruptStoreError` thrown from `load()`, have the CLI print `corrupt store file: <path>` and exit 1, and add a test for it.

Should I add both as tasks, build them and run a second review?