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

test('add then list prints the bookmark', () => {
  const { store, lines, out } = setup()
  assert.equal(run(['add', 'https://nodejs.org', 'Node'], store, out), 0)
  assert.equal(run(['list'], store, out), 0)
  assert.deepEqual(lines, ['added 1', '1  Node  https://nodejs.org'])
})

test('add without url is bad input', () => {
  const { store, errors, out } = setup()
  assert.equal(run(['add'], store, out), 2)
  assert.match(errors[0] ?? '', /usage/)
})
