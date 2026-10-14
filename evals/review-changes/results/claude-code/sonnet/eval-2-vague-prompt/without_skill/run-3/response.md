I reviewed `feature/bookmark-tags` against its plan and `AGENTS.md`, and fixed what I found. All 15 tests pass, and I ran `add`, `tag` and `list --tag` against a temp store to check the output. The fixes are in commit `7b335f9`.

- **Wrong exit code:** an unknown id on `bm tag` exited 2. `AGENTS.md` and the plan say 1 for not found, so it now exits 1.
- **Duplicate tags:** tagging a bookmark with a tag it already had added the tag again. The plan says that should be a no-op, so `BookmarkStore.tag` now skips it.
- **Unnormalized filter:** `list --tag Work` returned nothing because the filter value wasn't normalized. It now goes through `normalizeTag`, as the plan's call chain says.
- **Silent `--tag`:** a bare `bm list --tag` listed everything. It now prints `usage: bm list [--tag <tag>]` and exits 2.
- **Method name:** I renamed `listTagged` to `listByTag` to match the plan's API.
- **Tests:** the plan required tests for a duplicate tag and an unknown id, and they were missing. I added those, plus tests for normalized `list --tag` and for bare `--tag`.

The `/commit` skill isn't available in this session, so I used a plain `git commit`.