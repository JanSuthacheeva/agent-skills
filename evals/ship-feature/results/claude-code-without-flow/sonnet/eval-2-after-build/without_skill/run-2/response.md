The review is finished and committed. I haven't pushed or opened a merge request, because that needs your approval. All 17 tests pass, and the end-to-end run against a temp store behaves as the plan says.

**Fixed** (in `4f26c7a`, each with a test that failed first)
- **Exit code:** an unknown id in `tag` exited 2. The plan and `AGENTS.md` say 1.
- **Duplicates:** tagging a bookmark twice with the same tag stored it twice. The plan says it should be a no-op.
- **`list --tag` normalizing:** `list --tag Work` skipped `normalizeTag`, so it found nothing and accepted invalid tags.
- **`list --tag` without a tag:** it silently listed everything. It's now a usage error, `usage: bm list [--tag <tag>]`, exit 2. I added that line to the plan.
- **Name:** `listTagged` is now `listByTag`, as the plan names it.

**Open**
- `load()` casts the parsed JSON without checking it. A corrupt store file crashes the CLI with a raw `SyntaxError`. This was already the case before this branch, so I left it. I recommend a store error mapped to exit 2 in a follow-up.
- I re-read the fixes myself as a separate pass. No independent agent reviewed them.

**Where to look**
- `src/store.ts`, `load()` to `save()`: old files without `tags` are read as `[]` and get the field written back on the next change.
- `src/cli.ts`, `run()` error mapping and the `tag` and `list` cases: exit codes and messages.
- The tests and `src/tags.ts` are routine.

The plan now has a `## Review` section with this summary (`0eeab54`).

Do you want me to write the merge request next?