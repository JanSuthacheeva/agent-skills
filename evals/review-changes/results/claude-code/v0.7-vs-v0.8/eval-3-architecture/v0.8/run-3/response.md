I found four bugs on the branch and fixed them, each in its own commit with a test that fails without the fix. All 19 tests pass at `607388d`.

**Fixed**
- **Data loss** (`1e54526`): if the store file was corrupt, `load()` returned an empty list. The next `add` or `tag` then saved over the file and every bookmark was gone. I reproduced this through the real CLI. A corrupt file is now left untouched.
- **Duplicate tags and the tag filter** (`9865f7a`): tagging a bookmark twice printed a `console.warn` from the store, but the plan says it should do nothing. `list --tag "to do"` was accepted on an empty store because the tag was only checked inside the filter loop. Both now behave as the plan says.
- **The `tag` command bypassed the store** (`607388d`): the CLI did its own tagging with `list()` and `save()`, which left `BookmarkStore.tag()` unused. This goes against the plan and the layering rule in `AGENTS.md`. Separately, `bm tag "" work` printed "no bookmark 0" with exit 1 instead of the usage error with exit 2. The CLI now calls `store.tag()` and rejects ids that aren't whole numbers.
- **Missing tests**: added the ones the plan asked for, covering duplicate tags, unknown ids and non-numeric ids in both the store and the CLI.

**Open (needs your call, since each changes what users see)**
- **Corrupt store file**: it now crashes with a raw Node stack trace and exit code 1, the same as on `main`. That still breaks the `AGENTS.md` rule that the CLI turns errors into messages. I'd add a `CorruptStoreError` that prints `store file is corrupt: <path>`.
- **`bm list --tag` with no value**: it quietly lists everything. I'd make it a usage error with exit 2.
- **Missing review page**: the plan links to `.lavish/bookmark-tags-implementation.html`, which isn't in the repo.

**Where to look**
1. `src/store.ts`, `load()` through `save()`: what happens when the file is bad.
2. `src/cli.ts`, the `tag` case: how the id is parsed and the call to `store.tag`.

`src/tags.ts` and `src/bookmark.ts` are routine and can be skimmed.

**Checks**
- The project has no lint or type-check scripts.
- The security review found nothing. I ran it against local `main`, because `origin/main` doesn't have the plan commit yet.
- A separate agent reviewed my fix commits and found no problems with them.

I also wrote this summary into the plan as a `## Review` section (`0f880c4`). Nothing was pushed.