No MR exists yet. Here are the title and description. I won't push until you say so.

**Title:** `SHOP-311 Tags disappear`

**Description:**
```
Every `bm add` rewrote the bookmarks file without any tags, so
`bm list --tag` found nothing after the next add. `toRecord()` in the
store predated tags and left them out; it now copies them.

- `tag()` now saves through `save()` like `add()`, so there is one way
  to write the file and the record shape cannot diverge again.

Review:
1. `src/store.ts` `toRecord()` and `tag()` (about 12 changed lines): check that
   `tags` is written on every save path.
Skim: the tests in `test/store.tags.test.ts` and the plan.

Tags already lost from users' files cannot be recovered by code; affected
users have to add them again.

Refs: SHOP-311
```

Before the fix, adding a bookmark after tagging left `list --tag work` empty. After it, the reproduction lists `1  A  https://a.example`.

Should I push `fix/SHOP-311-tags-lost` and create the merge request against `main`?