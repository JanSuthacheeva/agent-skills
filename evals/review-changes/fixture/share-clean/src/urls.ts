export class InvalidUrlError extends Error {
  readonly raw: string

  constructor(raw: string) {
    super(`invalid url: ${raw}`)
    this.name = 'InvalidUrlError'
    this.raw = raw
  }
}

export function parseWebUrl(raw: string): string {
  let url: URL
  try {
    url = new URL(raw)
  } catch {
    throw new InvalidUrlError(raw)
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') throw new InvalidUrlError(raw)
  return url.href
}
