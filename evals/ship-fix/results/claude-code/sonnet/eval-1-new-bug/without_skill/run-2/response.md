I didn't push or create the MR, because the push was denied. The fix is committed on `fix/SHOP-311-tags-lost-on-add`.

**Cause:** `toRecord` in `src/store.ts` left `tags` out. Every `save()`, including the one `bm add` triggers, rewrote the file without any tags. `list --tag` itself was fine.

**Fix:** `toRecord` now writes `tags`, and `tag()` uses `save()` instead of its own `#write`. I added a regression test in `test/store.tags.test.ts`. It failed before the fix, and all 16 tests pass now.

**Commit:** `bm: keep tags when saving bookmarks`, with `Refs: SHOP-311`.

**MR title:** `SHOP-311 Tags disappear`

**MR description:**
```
Adding a bookmark wiped the tags of all existing ones, so `bm list --tag`
came back empty. `toRecord` left `tags` out, so every `save()` rewrote the
file without them; it now writes them.

- `tag()` now goes through `save()` instead of its own `#write` with tags
  patched in, so there is a single serialization path.

Refs: SHOP-311
```

If you want me to push and open the MR, say so or allow the push. The command is `git push -u origin fix/SHOP-311-tags-lost-on-add`, then `glab mr create --target-branch main`.

One thing to check first: `origin` fetches from `git@gitlab.com:shop/shop.git`, but its push URL is a local path (`.../origin.git`). `glab mr create` talks to the GitLab project, so the push and the MR may not end up in the same place.