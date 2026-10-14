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

export class BookmarkStore {
  #path: string

  constructor(path: string) {
    this.#path = path
  }

  load(): Bookmark[] {
    if (!existsSync(this.#path)) return []
    let raw: Partial<Bookmark>[]
    try {
      raw = JSON.parse(readFileSync(this.#path, 'utf8')) as Partial<Bookmark>[]
    } catch {
      return []
    }
    return raw.map(bookmark => ({ ...bookmark, tags: bookmark.tags ?? [] }) as Bookmark)
  }

  save(bookmarks: Bookmark[]): void {
    writeFileSync(this.#path, `${JSON.stringify(bookmarks, null, 2)}\n`)
  }

  add(url: string, title: string, now: Date = new Date()): Bookmark {
    const all = this.load()
    const bookmark = { id: Math.max(0, ...all.map(one => one.id)) + 1, url, title, createdAt: now.toISOString(), tags: [] }
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
    if (bookmark.tags.includes(normalized)) {
      console.warn(`bookmark ${id} already has tag ${normalized}`)
      return bookmark
    }
    bookmark.tags.push(normalized)
    this.save(all)
    return bookmark
  }

  listByTag(tag: string): Bookmark[] {
    return this.load().filter(bookmark => bookmark.tags.includes(normalizeTag(tag)))
  }
}
