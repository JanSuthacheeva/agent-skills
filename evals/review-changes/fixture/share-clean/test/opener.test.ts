import assert from 'node:assert/strict'
import { chmodSync, existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'

import { openUrl } from '../src/opener.ts'

test('the url reaches the opener as one argument, uninterpreted', () => {
  const dir = mkdtempSync(join(tmpdir(), 'bm-open-'))
  const opener = join(dir, 'opener')
  writeFileSync(opener, `#!/bin/sh\nprintf '%s' "$1" > "${join(dir, 'arg')}"\n`)
  chmodSync(opener, 0o755)
  const url = `https://a.dev/$(touch ${join(dir, 'pwned')})`
  openUrl(url, opener)
  assert.equal(readFileSync(join(dir, 'arg'), 'utf8'), url)
  assert.equal(existsSync(join(dir, 'pwned')), false)
})
