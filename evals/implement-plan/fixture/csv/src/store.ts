import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'

export const storeFileName = '.bookmarks.csv'

const header = 'id,url,title,createdAt'

// Users open this file in spreadsheets and sync it between machines, so the
// columns are part of the public format.
export class BookmarkStore {
  #path: string

  constructor(path: string) {
    this.#path = path
  }

  load(): Bookmark[] {
    if (!existsSync(this.#path)) return []
    const [, ...rows] = readFileSync(this.#path, 'utf8').trimEnd().split('\n')
    return rows.map(parseRow)
  }

  save(bookmarks: Bookmark[]): void {
    writeFileSync(this.#path, [header, ...bookmarks.map(formatRow)].join('\n') + '\n')
  }

  add(url: string, title: string, now: Date = new Date()): Bookmark {
    const all = this.load()
    const bookmark = { id: Math.max(0, ...all.map(one => one.id)) + 1, url, title, createdAt: now.toISOString() }
    this.save([...all, bookmark])
    return bookmark
  }

  list(): Bookmark[] {
    return this.load()
  }
}

function quote(field: string): string {
  return /[",\n]/.test(field) ? `"${field.replaceAll('"', '""')}"` : field
}

function formatRow(bookmark: Bookmark): string {
  return [String(bookmark.id), bookmark.url, bookmark.title, bookmark.createdAt].map(quote).join(',')
}

function parseRow(row: string): Bookmark {
  const fields: string[] = []
  let field = ''
  let isQuoted = false
  for (let i = 0; i < row.length; i++) {
    const char = row[i]
    if (isQuoted && char === '"' && row[i + 1] === '"') {
      field += '"'
      i++
    } else if (char === '"') {
      isQuoted = !isQuoted
    } else if (char === ',' && !isQuoted) {
      fields.push(field)
      field = ''
    } else {
      field += char
    }
  }
  fields.push(field)
  const [id = '', url = '', title = '', createdAt = ''] = fields
  return { id: Number(id), url, title, createdAt }
}
