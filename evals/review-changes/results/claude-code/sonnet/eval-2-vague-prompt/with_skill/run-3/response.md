I reviewed the branch against `docs/plans/2026-10-14-bookmark-tags.md` and fixed four deviations in one commit, `aee0b82`. Tests were green before and are green after (15 pass). There is no lint or type-check script in the repo.

I did not run a second review of the production-code fix. I wrote the fixes in this session, so I couldn't give it an unbiased read, and I didn't start a fresh agent for it. The diff is small (`src/cli.ts` and `src/store.ts`).

**Fixed**
- **Unknown id exit code:** `bm tag 9 x` exited 2, but the plan says 1. A new CLI test failed first.
- **Duplicate tags:** `store.tag` pushed a repeated tag again, although the plan says it should be a no-op. A new store test failed first.
- **`list --tag` normalization:** the tag went to the store unnormalized, so `--tag " Work "` found nothing and an invalid tag was never rejected. The plan says the CLI normalizes first and exits 2 on an invalid tag. A new CLI test failed first.
- **Method name:** `listTagged` is now `listByTag`, as the plan states. I also added the missing tests the plan's tasks list: duplicate tag, unknown id, non-numeric id.

**Open**
- `bm list --tag` with no value silently lists everything. The plan doesn't cover it. I'd print a usage error and exit 2, but that changes the command's behaviour, so I left it for you.
- The plan's last task (run `npm run bm -- add`, `tag` and `list --tag` against a temp store) is ticked, but I didn't redo it. The new CLI tests cover the same paths.

**Where to look**
1. `src/cli.ts`, the `run` / `dispatch` split and the error-to-exit-code mapping. This is where the exit-code bug was.
2. `src/store.ts` `tag()` and `listByTag()`. They normalize again even though the CLI already does, which is harmless but redundant.
3. Everything else, including `src/tags.ts`, `src/bookmark.ts` and the `load()` default of `tags: []` for old files, is routine and can be skimmed.