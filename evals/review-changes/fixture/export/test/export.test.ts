import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { run } from '../src/cli.ts'
import { escapeHtml, renderPage } from '../src/export.ts'
import { BookmarkStore, storeFileName } from '../src/store.ts'

const bookmark = { id: 1, url: 'https://a.dev/', title: 'A', createdAt: '2026-11-25T00:00:00.000Z' }

test('escapeHtml escapes markup', () => {
  assert.equal(escapeHtml('<b>Tom & Jerry</b>'), '&lt;b&gt;Tom &amp; Jerry&lt;/b&gt;')
})

test('renderPage links every bookmark', () => {
  const page = renderPage([bookmark])
  assert.match(page, /<li><a href="https:\/\/a\.dev\/" title="A">A<\/a><\/li>/)
})

test('a title with markup is shown as text', () => {
  assert.match(renderPage([{ ...bookmark, title: '<script>x</script>' }]), />&lt;script&gt;x&lt;\/script&gt;</)
})

test('export writes the page and reports the count', () => {
  const dir = mkdtempSync(join(tmpdir(), 'bm-'))
  const store = new BookmarkStore(join(dir, storeFileName))
  store.add('https://a.dev/', 'A')
  const lines: string[] = []
  const out = { log: (l: string) => lines.push(l), error: () => {} }
  const file = join(dir, 'page.html')
  assert.equal(run(['export', file], store, out), 0)
  assert.deepEqual(lines, [`exported 1 to ${file}`])
  assert.match(readFileSync(file, 'utf8'), /a\.dev/)
})
