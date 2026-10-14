The review found four deviations from the plan, and I fixed all of them. All 16 tests pass.

I haven't pushed or opened a merge request. The next step would be `write-merge-request`.

**Fixed**
- **Duplicate tags:** `bm tag 1 work` run twice stored `["work","work"]`. The plan says re-tagging is a no-op. Fixed in dc2258d.
- **Method name:** `listTagged` didn't match the plan's `listByTag`. Renamed in dc2258d.
- **Exit code:** an unknown id exited 2, but the plan and `AGENTS.md` say 1. Fixed in f976cb6.
- **`list --tag`:** `list --tag Work` matched nothing, and `list --tag 'bad tag'` exited 0. The tag is now normalized, and an invalid one exits 2. Fixed in f976cb6.
- **Tests:** I added the missing ones for a duplicate tag, an unknown id (store and CLI), a non-numeric id, and `list --tag` normalization and invalid input.

A fresh agent reviewed the two fix commits and found no problems.

**Open**
- **`bm list --tag` with no value:** it lists every bookmark and exits 0, and the plan doesn't say what it should do. I'd print `usage: bm list [--tag <tag>]` and exit 2, but that adds user-visible behavior, so I left it for you.
- **dc2258d on its own:** its tests don't pass end to end, because the CLI still calls the old method name until f976cb6. Squash the two commits if you want the history bisectable.

**Where to look**
- `src/store.ts`, `tag()` and `listByTag()`: the only code that writes the store file.
- `src/cli.ts`, `run()` and the `tag` and `list` cases: argument parsing and error-to-exit-code mapping.
- Everything else is routine and can be skimmed.

The summary is also in the plan's `## Review` section (f769830).