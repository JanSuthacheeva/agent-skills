export class InvalidUrlError extends Error {
  readonly raw: string

  constructor(raw: string) {
    super(`invalid url: ${raw}`)
    this.name = 'InvalidUrlError'
    this.raw = raw
  }
}

export function parseWebUrl(raw: string): string {
  try {
    return new URL(raw).href
  } catch {
    throw new InvalidUrlError(raw)
  }
}
