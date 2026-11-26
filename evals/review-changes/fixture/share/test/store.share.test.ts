import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { BookmarkNotFoundError, BookmarkStore } from '../src/store.ts'

function tempStore(): BookmarkStore {
  return new BookmarkStore(join(mkdtempSync(join(tmpdir(), 'bm-')), 'bookmarks.json'))
}

test('importAll appends with increasing ids', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  const added = store.importAll([{ url: 'https://b.dev/', title: 'B' }, { url: 'https://c.dev/', title: 'C' }])
  assert.deepEqual(added.map(one => one.id), [2, 3])
  assert.deepEqual(store.list().map(one => one.title), ['A', 'B', 'C'])
})

test('get finds a bookmark by id', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  assert.equal(store.get(1).title, 'A')
})

test('get of an unknown id throws', () => {
  assert.throws(() => tempStore().get(9), BookmarkNotFoundError)
})
