I reviewed the branch against its plan and fixed five deviations. All 15 tests pass, and I ran `add`, `tag` and `list --tag` against a temp store file to check the output.

- **Duplicate tags:** `tag` appended without checking, so tagging twice stored the tag twice. It's now a no-op, as the plan says.
- **Unknown id:** the CLI returned exit 2, but the plan and `AGENTS.md` say 1 for not found. It now returns 1.
- **Method name:** `listTagged` didn't match the plan's `listByTag`, so I renamed it.
- **`list --tag` input:** the tag value wasn't normalized, so `--tag WORK` found nothing. It's normalized now. A bare `--tag` with no value used to list everything silently. It now prints `usage: bm list [--tag <tag>]` and exits 2.
- **Missing tests:** I added tests for a duplicate tag, an unknown id (store and CLI), a non-numeric id, and `list --tag` with normalization and a missing value.

The `/commit` skill isn't available here, so I committed directly as `ddfe415`.