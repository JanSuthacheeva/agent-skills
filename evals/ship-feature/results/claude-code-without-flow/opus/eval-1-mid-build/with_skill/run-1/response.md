I finished building the bookmark tags feature. A separate review then raised two questions that need your decision before I write the merge request.

**Build:** all 5 tasks in the plan are done, one commit each:
- `57a957e` bm: store tags on bookmarks
- `084e5b7` bm: store: tag bookmarks and list by tag
- `6f0d3d9` bm: cli: add tag command and list --tag
- `680aef0` docs: tick bookmark tags end-to-end check

I ran the real CLI against a temporary bookmarks file, including one saved before tags existed. Tagging, case-insensitive matching, filtering, saving the same tag twice and all the error cases printed the right messages and exit codes. The old file loaded fine and gained a `tags` field when it was next saved. All tests pass; the project has no lint or type checks, so tests were the only check available.

**One addition to the plan:** it didn't say what happens when `list` gets `--tag` with no value, or an option it doesn't know. Both now print `usage: bm list [--tag <tag>]` and exit 2, the same way other bad input is handled. I added this to the plan and covered it with a test. Before this branch, `bm list` ignored extra arguments, so tell me if you'd rather keep that.

**Review:** the reviewer had no access to this conversation. It added two missing tests (`38deacb`) and left two open questions:

1. **Extra arguments are ignored.** `bm tag 1 work extra` and `bm list --tag work extra` succeed with exit 0. The reviewer recommends printing the usage message and exiting with 2. I agree: it matches the `list` case above.
2. **A tag made only of dashes is accepted.** `bm tag 1 -` saves `-`. The plan's rule (letters, digits and `-`) allows this, but it's probably not intended. The reviewer recommends the pattern `^[a-z0-9]+(-[a-z0-9]+)*$`, which also rejects leading, trailing and double dashes. I agree, and it's best to do now: tightening the rule after tags have been saved would leave invalid tags in existing files.

Should I build both as recommended? If so, I'll add them to the plan as new tasks, build them, run another review and then write the merge request.