import { execSync } from 'node:child_process'

export function defaultOpener(): string {
  return process.env['BM_OPENER'] ?? (process.platform === 'darwin' ? 'open' : 'xdg-open')
}

export function openUrl(url: string, opener: string = defaultOpener()): void {
  execSync(`${opener} "${url}"`, { stdio: 'ignore' })
}
