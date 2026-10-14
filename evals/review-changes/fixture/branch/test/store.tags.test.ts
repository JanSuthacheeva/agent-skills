import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { BookmarkStore } from '../src/store.ts'

function tempPath(): string {
  return join(mkdtempSync(join(tmpdir(), 'bm-')), 'bookmarks.json')
}

test('a file written before tags existed loads with empty tags', () => {
  const path = tempPath()
  writeFileSync(path, JSON.stringify([{ id: 1, url: 'https://a.dev', title: 'A', createdAt: '2026-01-01T00:00:00.000Z' }]))
  assert.deepEqual(new BookmarkStore(path).list()[0]?.tags, [])
})

test('tag adds a normalized tag and listTagged finds it', () => {
  const store = new BookmarkStore(tempPath())
  store.add('https://a.dev', 'A')
  store.add('https://b.dev', 'B')
  store.tag(1, 'Work')
  assert.deepEqual(store.listTagged('work').map(one => one.id), [1])
})
