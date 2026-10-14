Bookmark tags are implemented as planned, in four commits (one per code task). All 18 tests pass. I also ran the CLI against a temp store file, and `add`, `tag` and `list --tag` behaved as the plan describes.

- **Output and exit codes:** `tag 2 Runtime` prints `tagged 2 runtime`. `tag 9 x` prints `no bookmark 9` with exit 1. `tag 1 a_b` prints `invalid tag: a_b` with exit 2. A non-numeric id prints the usage line with exit 2.
- **Old store files:** files written before tags existed load as `tags: []`, with a test for it.
- **Plan checklist:** all five tasks are ticked in the plan file.

**Not in the plan:** `list` with a missing or unknown flag prints `usage: bm list [--tag <tag>]` and exits 2. I added that so a malformed `--tag` doesn't silently list everything.

The `/commit` skill isn't available in this session, so I committed with plain `git commit`.