import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'

export const storeFileName = '.bookmarks.json'

interface BookmarkRecord {
  id: number
  url: string
  title: string
  createdAt: string
}

function toRecord(bookmark: Bookmark): BookmarkRecord {
  return { id: bookmark.id, url: bookmark.url, title: bookmark.title, createdAt: bookmark.createdAt.toISOString() }
}

function fromRecord(record: BookmarkRecord): Bookmark {
  return { id: record.id, url: record.url, title: record.title, createdAt: new Date(record.createdAt) }
}

export class BookmarkStore {
  #path: string

  constructor(path: string) {
    this.#path = path
  }

  load(): Bookmark[] {
    if (!existsSync(this.#path)) return []
    const records = JSON.parse(readFileSync(this.#path, 'utf8')) as BookmarkRecord[]
    return records.map(fromRecord)
  }

  save(bookmarks: Bookmark[]): void {
    this.#write(bookmarks.map(toRecord))
  }

  add(url: string, title: string, now: Date = new Date()): Bookmark {
    const all = this.load()
    const bookmark = { id: Math.max(0, ...all.map(one => one.id)) + 1, url, title, createdAt: now }
    this.save([...all, bookmark])
    return bookmark
  }

  list(): Bookmark[] {
    return this.load()
  }

  #write(records: BookmarkRecord[]): void {
    writeFileSync(this.#path, `${JSON.stringify(records, null, 2)}\n`)
  }
}
