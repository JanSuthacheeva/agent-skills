import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { BookmarkStore } from '../src/store.ts'

function tempStore(): BookmarkStore {
  return new BookmarkStore(join(mkdtempSync(join(tmpdir(), 'bm-')), 'bookmarks.csv'))
}

test('add assigns increasing ids and persists', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  const second = store.add('https://b.dev', 'B')
  assert.equal(second.id, 2)
  assert.deepEqual(store.list().map(one => one.title), ['A', 'B'])
})

test('a missing file is an empty store', () => {
  assert.deepEqual(tempStore().list(), [])
})

test('titles with commas and quotes survive a round trip', () => {
  const store = tempStore()
  store.add('https://c.dev', 'Say "hi", then go')
  assert.equal(store.list()[0]?.title, 'Say "hi", then go')
})
