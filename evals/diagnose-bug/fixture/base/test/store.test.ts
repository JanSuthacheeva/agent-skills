import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { BookmarkStore } from '../src/store.ts'

function tempStore(): BookmarkStore {
  return new BookmarkStore(join(mkdtempSync(join(tmpdir(), 'bm-')), 'bookmarks.json'))
}

test('add assigns increasing ids and persists', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  const second = store.add('https://b.dev', 'B')
  assert.equal(second.id, 2)
  assert.deepEqual(store.list().map(one => one.title), ['A', 'B'])
})

test('createdAt survives a round trip', () => {
  const store = tempStore()
  const now = new Date('2026-10-01T09:30:00.000Z')
  store.add('https://a.dev', 'A', now)
  assert.equal(store.list()[0]?.createdAt.toISOString(), now.toISOString())
})

test('a missing file is an empty store', () => {
  assert.deepEqual(tempStore().list(), [])
})
