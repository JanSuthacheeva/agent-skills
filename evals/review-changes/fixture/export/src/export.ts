import type { Bookmark } from './bookmark.ts'

const entities: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;' }

export function escapeHtml(text: string): string {
  return text.replace(/[&<>]/g, char => entities[char]!)
}

export function renderPage(bookmarks: Bookmark[]): string {
  const items = bookmarks.map(bookmark => {
    const title = escapeHtml(bookmark.title)
    return `  <li><a href="${bookmark.url}" title="${title}">${title}</a></li>`
  })
  return ['<!doctype html>', '<meta charset="utf-8">', '<title>Bookmarks</title>', '<ul>', ...items, '</ul>', ''].join('\n')
}
