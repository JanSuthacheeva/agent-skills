import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { BookmarkNotFoundError, BookmarkStore } from '../src/store.ts'

function tempStore(): BookmarkStore {
  return new BookmarkStore(join(mkdtempSync(join(tmpdir(), 'bm-')), 'bookmarks.json'))
}

test('tag persists a normalized tag', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  store.tag(1, ' Work ')
  assert.deepEqual(store.list()[0]?.tags, ['work'])
})

test('tagging twice keeps one tag', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  store.tag(1, 'work')
  store.tag(1, 'work')
  assert.deepEqual(store.list()[0]?.tags, ['work'])
})

test('listTagged returns only bookmarks with the tag', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  store.add('https://b.dev', 'B')
  store.tag(2, 'work')
  assert.deepEqual(store.listTagged('WORK').map(one => one.title), ['B'])
})

test('tag on a missing bookmark throws', () => {
  assert.throws(() => tempStore().tag(9, 'work'), BookmarkNotFoundError)
})

test('bookmarks saved before tags load with no tags', () => {
  const store = tempStore()
  store.add('https://a.dev', 'A')
  assert.deepEqual(store.list()[0]?.tags, [])
})
