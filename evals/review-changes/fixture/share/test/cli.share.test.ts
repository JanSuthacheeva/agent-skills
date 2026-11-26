import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { run } from '../src/cli.ts'
import { BookmarkStore, storeFileName } from '../src/store.ts'

function setup() {
  const dir = mkdtempSync(join(tmpdir(), 'bm-'))
  const store = new BookmarkStore(join(dir, storeFileName))
  const lines: string[] = []
  const errors: string[] = []
  const opened: string[] = []
  const out = { log: (l: string) => lines.push(l), error: (l: string) => errors.push(l) }
  return { dir, store, lines, errors, opened, out, open: (url: string) => opened.push(url) }
}

function shared(dir: string, entries: unknown): string {
  const file = join(dir, 'shared.json')
  writeFileSync(file, JSON.stringify(entries))
  return file
}

test('import adds every entry of a shared file', () => {
  const { dir, store, lines, out } = setup()
  const file = shared(dir, [{ url: 'https://a.dev', title: 'A' }, { url: 'https://b.dev' }])
  assert.equal(run(['import', file], store, out), 0)
  assert.deepEqual(lines, ['imported 2'])
  assert.deepEqual(store.list().map(one => one.title), ['A', 'https://b.dev'])
})

test('import of a url that does not parse imports nothing', () => {
  const { dir, store, errors, out } = setup()
  const file = shared(dir, [{ url: 'https://a.dev' }, { url: 'nope' }])
  assert.equal(run(['import', file], store, out), 2)
  assert.deepEqual(errors, ['invalid url: nope'])
  assert.deepEqual(store.list(), [])
})

test('open opens the bookmark url', () => {
  const { store, opened, out, open } = setup()
  store.add('https://a.dev/', 'A')
  assert.equal(run(['open', '1'], store, out, open), 0)
  assert.deepEqual(opened, ['https://a.dev/'])
})

test('open of an unknown id is not found', () => {
  const { store, errors, out, open } = setup()
  assert.equal(run(['open', '9'], store, out, open), 1)
  assert.deepEqual(errors, ['no bookmark 9'])
})
