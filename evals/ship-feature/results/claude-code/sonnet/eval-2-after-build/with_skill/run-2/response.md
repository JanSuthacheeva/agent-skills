The review is done and the tests pass (15 of 15). It fixed five problems and left three items open for you to decide.

**Fixed in `b6b9a23`**
- An unknown id in `bm tag` now exits 1. It exited 2 before.
- Tagging a bookmark with a tag it already has is now a no-op. It used to store a duplicate.
- `bm list --tag` now normalizes its tag. An invalid tag prints `invalid tag: <raw>` and exits 2.
- `listTagged` is renamed to the planned `listByTag`.
- Tests were added for each of these. The reviewer says each new test failed before the fix.

I didn't have a second fresh agent available, so the reviewer re-read its own fixes against the findings.

**Open items (your decision)**
1. **`bm list --tag` with no value** lists every bookmark without saying anything. The plan doesn't cover this case. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2 before merge.
2. **A corrupt store file** throws a raw `SyntaxError` out of `run`. This was already the case before the branch. I recommend a separate change that maps it to a clear error.
3. **`BookmarkStore.tag` also normalizes the tag**, although the plan has only the CLI do it. It's harmless and keeps the store safe for other callers. I recommend keeping it.

**Where to look**
1. `src/store.ts`, from `load()` to `tag()`. This is the only code that reads and rewrites stored data.
2. `src/cli.ts`: the `run()` error mapping and the `tag` and `list` cases, for exit codes and messages against the plan.
3. Skim the rest. `src/tags.ts` and the tests are routine.

How do you want to handle them?
- **Item 1:** I'd add it as a new task in the plan and build it now.
- **Item 2:** I'd leave it for a separate change.
- **Item 3:** I'd keep it as it is.

If you agree, I'll add the usage-error task to the plan, build it, and run a second review on the new commits. After that I'll draft the merge request for you to approve before anything is pushed.