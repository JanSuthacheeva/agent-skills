import assert from 'node:assert/strict'
import { test } from 'node:test'

import { InvalidTagError, normalizeTag } from '../src/tags.ts'

test('lowercases and trims', () => {
  assert.equal(normalizeTag(' Work '), 'work')
})

test('rejects empty and invalid tags', () => {
  assert.throws(() => normalizeTag('  '), InvalidTagError)
  assert.throws(() => normalizeTag('to do'), InvalidTagError)
})
