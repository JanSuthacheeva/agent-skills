export class InvalidTagError extends Error {
  readonly raw: string

  constructor(raw: string) {
    super(`invalid tag: ${raw}`)
    this.name = 'InvalidTagError'
    this.raw = raw
  }
}

const tagPattern = /^[a-z0-9-]+$/

export function normalizeTag(raw: string): string {
  const tag = raw.trim().toLowerCase()
  if (!tagPattern.test(tag)) throw new InvalidTagError(raw)
  return tag
}
