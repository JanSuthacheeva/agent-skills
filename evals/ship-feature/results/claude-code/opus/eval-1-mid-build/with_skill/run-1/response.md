I finished building the feature and the separate review is done, but it left two open items that need your decision before I write the merge request.

**Where it stands:** the plan has all 5 tasks ticked across 5 commits (`9f69283` through `2aaa969`), and all 16 tests pass. I checked the commits, ticked boxes and test run in the repo myself. The review (`7fd6d48`) didn't fix anything; everything it tried matched the plan.

The build hit two error cases the plan didn't cover and handled both. It added them to the plan's Errors section:
- `bm tag <id>` with no tag prints `usage: bm tag <id> <tag>` and exits 2.
- `bm list --tag` with no tag prints the usage line and exits 2.

**Open items:**

1. **Unknown arguments are silently ignored.** A typo like `bm list --tags work` lists every bookmark and exits 0. Extra arguments such as `bm tag 1 work extra` are ignored too. `list` on `main` already behaves this way, and fixing it changes what users see.
   - Options: (a) leave it for a follow-up, as the reviewer recommends; (b) add a task now so unknown options and extra arguments print the usage message and exit 2.
   - **I recommend (b).** The new `--tag` option makes this typo likely, and right now the mistake gives no error at all. It's a small, well-contained task.

2. **Test data got into your real bookmark file.** The CLI uses `~/.bookmarks.json` when `BM_FILE` isn't set. That file now holds one test bookmark: id 1, `https://a.dev`, "A", created today, tagged `work`. An earlier manual check without `BM_FILE` probably created it. The reviewer also wrote to the file once by mistake and says it removed its own changes. I've looked at the file but haven't changed it.
   - **I recommend deleting `~/.bookmarks.json`** if you weren't already using `bm` for real bookmarks. Should I delete it?

Once you decide on 1, I'll add any new task to the plan, build it, and run a second review on those commits.