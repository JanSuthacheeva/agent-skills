import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'
import { normalizeTag } from './tags.ts'

export const storeFileName = '.bookmarks.json'

export class BookmarkNotFoundError extends Error {
  readonly id: number

  constructor(id: number) {
    super(`no bookmark ${id}`)
    this.name = 'BookmarkNotFoundError'
    this.id = id
  }
}

interface BookmarkRecord {
  id: number
  url: string
  title: string
  createdAt: string
  tags?: string[]
}

function toRecord(bookmark: Bookmark): BookmarkRecord {
  return { id: bookmark.id, url: bookmark.url, title: bookmark.title, createdAt: bookmark.createdAt.toISOString() }
}

function fromRecord(record: BookmarkRecord): Bookmark {
  return {
    id: record.id,
    url: record.url,
    title: record.title,
    createdAt: new Date(record.createdAt),
    tags: record.tags ?? [],
  }
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
    const bookmark = { id: Math.max(0, ...all.map(one => one.id)) + 1, url, title, createdAt: now, tags: [] }
    this.save([...all, bookmark])
    return bookmark
  }

  list(): Bookmark[] {
    return this.load()
  }

  tag(id: number, tag: string): Bookmark {
    const all = this.load()
    const bookmark = all.find(one => one.id === id)
    if (bookmark === undefined) throw new BookmarkNotFoundError(id)
    const normalized = normalizeTag(tag)
    if (!bookmark.tags.includes(normalized)) bookmark.tags.push(normalized)
    this.#write(all.map(one => ({ ...toRecord(one), tags: one.tags })))
    return bookmark
  }

  listTagged(tag: string): Bookmark[] {
    const normalized = normalizeTag(tag)
    return this.load().filter(bookmark => bookmark.tags.includes(normalized))
  }

  #write(records: BookmarkRecord[]): void {
    writeFileSync(this.#path, `${JSON.stringify(records, null, 2)}\n`)
  }
}
