# Fix: tags disappear after adding a bookmark

Report: SHOP-311 "Tags disappear"

## Report

Expected: `bm list --tag work` lists the bookmarks tagged work.
Actual: after another `bm add`, it lists nothing.
Steps and environment: tag bookmarks, add a new one, list by tag. The
reporter suspects `list --tag`.

## Reproduction

    export BM_FILE=$(mktemp -d)/bm.json
    npm run -s bm -- add https://a.example A        # added 1
    npm run -s bm -- tag 1 work                     # tagged 1 work
    npm run -s bm -- list --tag work                # 1  A  https://a.example
    npm run -s bm -- add https://b.example B        # added 2
    npm run -s bm -- list --tag work                # (nothing), exit 0

Fails every run. After the second `add`, no record in `$BM_FILE` has a
`tags` field.

## Root cause

`src/store.ts` `toRecord()` builds the stored record from a field list
written before tags existed, so it leaves `tags` out. `BookmarkStore.save()`
writes every bookmark through it, and `add()` saves all bookmarks, so each
`bm add` rewrites the file without any tags. `tag()` writes its own
records with `tags` added back, which is why tagging appears to work.
Proven by loading a tagged file and calling `save(load())` in a scratch
script: the tags are gone. Introduced in "bm: tag bookmarks and list by
tag", which added `tags` to `Bookmark` and `fromRecord()` but not to
`toRecord()`. `listTagged()` and `list --tag` are correct.

## Fix

`toRecord(bookmark: Bookmark): BookmarkRecord` copies `tags`. `tag()`
saves through `save(all)` like `add()`, so there is one way to write the
file. No signature changes.

## Also affected

Every `bm add` since the tags commit has removed all tags from the user's
file; they cannot be recovered from it and must be added again.

## Assumptions

- The regression test goes in `test/store.tags.test.ts`, next to the
  other tag tests.

## Tasks

- [ ] Add "adding a bookmark keeps existing tags" in `test/store.tags.test.ts` (fails today with `[]` instead of `[ 'work' ]`), then fix `toRecord()` in `src/store.ts`
- [ ] Make `tag()` save through `save(all)`, with a test that tagging two bookmarks keeps both tags
- [ ] End-to-end: run the reproduction again and see `1  A  https://a.example` from the last `list --tag work`
