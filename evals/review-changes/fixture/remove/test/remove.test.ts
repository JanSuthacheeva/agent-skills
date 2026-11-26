import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { run } from '../src/cli.ts'
import { BookmarkStore, storeFileName } from '../src/store.ts'

function setup() {
  const store = new BookmarkStore(join(mkdtempSync(join(tmpdir(), 'bm-')), storeFileName))
  const lines: string[] = []
  const errors: string[] = []
  return { store, lines, errors, out: { log: (l: string) => lines.push(l), error: (l: string) => errors.push(l) } }
}

test('remove deletes only that bookmark', () => {
  const { store, lines, out } = setup()
  store.add('https://a.dev', 'A')
  store.add('https://b.dev', 'B')
  assert.equal(run(['remove', '1'], store, out), 0)
  assert.deepEqual(lines, ['removed 1'])
  assert.deepEqual(store.list().map(one => one.title), ['B'])
})

test('remove without an id is bad input', () => {
  const { store, errors, out } = setup()
  assert.equal(run(['remove', 'x'], store, out), 2)
  assert.deepEqual(errors, ['usage: bm remove <id>'])
})
