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

test('tag then list --tag prints the tagged bookmark', () => {
  const { store, lines, out } = setup()
  run(['add', 'https://a.dev', 'A'], store, out)
  run(['add', 'https://b.dev', 'B'], store, out)
  assert.equal(run(['tag', '1', 'work'], store, out), 0)
  assert.equal(run(['list', '--tag', 'work'], store, out), 0)
  assert.deepEqual(lines.slice(2), ['tagged 1 work', '1  A  https://a.dev'])
})

test('an invalid tag is bad input', () => {
  const { store, errors, out } = setup()
  run(['add', 'https://a.dev', 'A'], store, out)
  assert.equal(run(['tag', '1', 'to do'], store, out), 2)
  assert.equal(errors[0], 'invalid tag: to do')
})
