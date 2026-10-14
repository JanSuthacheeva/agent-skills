Bookmark tags are implemented and committed (`8eb78d9`). All 16 tests pass. In a manual run with a temp store file:
- `add`, `tag 1 Work` and `list --tag work` worked as planned.
- `tag 1 "a b"` printed `invalid tag: a b` and exited 2.
- `tag 5 x` printed `no bookmark 5` and exited 1.

I deviated from the plan in one place. It declared `InvalidTagError` as `constructor(readonly raw: string)`. That is a parameter property, which `AGENTS.md` forbids because Node can't strip it. I declared `raw` as a plain field and assigned it in the constructor instead. Behavior is the same.

Two smaller choices the plan left open:
- `bm list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2.
- `BookmarkStore.tag` and `listByTag` normalize the tag themselves, so the store stays correct if called directly.

I used a plain `git commit` because no `/commit` skill is listed in this session. I also ticked all the task boxes in the plan file.