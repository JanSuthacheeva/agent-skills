import assert from 'node:assert/strict'
import { test } from 'node:test'

import { InvalidUrlError, parseWebUrl } from '../src/urls.ts'

test('http and https urls are accepted', () => {
  assert.equal(parseWebUrl('https://nodejs.org'), 'https://nodejs.org/')
  assert.equal(parseWebUrl('http://example.com/a'), 'http://example.com/a')
})

test('a url that does not parse is rejected', () => {
  assert.throws(() => parseWebUrl('not a url'), InvalidUrlError)
})

test('other schemes are rejected', () => {
  assert.throws(() => parseWebUrl('file:///etc/passwd'), InvalidUrlError)
  assert.throws(() => parseWebUrl('javascript:alert(1)'), InvalidUrlError)
})
