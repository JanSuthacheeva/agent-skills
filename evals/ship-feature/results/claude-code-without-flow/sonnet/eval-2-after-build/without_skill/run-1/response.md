The build is done and the end-to-end check is fixed. Next is `review-changes`, then `write-merge-request`. I haven't started either.

All five plan tasks were already checked off, but running the CLI against a temp store showed the code didn't match the plan. I fixed these in commit `bm: match tag behavior to the plan`:
- **Unknown id:** `bm tag 99 x` exited 2. It now exits 1, as the plan and AGENTS.md say.
- **Duplicate tag:** tagging twice stored the tag twice. It is now a no-op.
- **`list --tag` normalization:** the tag was not normalized, so `" Work "` found nothing. It is now normalized, and an invalid tag exits 2.
- **`list --tag` with no value:** it silently listed everything. It now prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't specify this, so I chose the exit code to match the other usage errors.
- **Method name:** `listTagged` is now `listByTag`, as in the plan.
- **Tests:** I added the tests the plan required but were missing: duplicate tag, unknown id at store and CLI level, and a non-numeric id. I also added tests for the `list --tag` fixes above. All 17 tests pass.

Both the CLI and the store now normalize the tag in `list --tag`. That duplicates the work, but it keeps the store correct for any caller.

Should I run `review-changes` on the branch now? I'd open the merge request only after that, and only once you approve the push.