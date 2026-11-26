import { execFileSync } from 'node:child_process'

export function defaultOpener(): string {
  return process.env['BM_OPENER'] ?? (process.platform === 'darwin' ? 'open' : 'xdg-open')
}

export function openUrl(url: string, opener: string = defaultOpener()): void {
  execFileSync(opener, [url], { stdio: 'ignore' })
}
