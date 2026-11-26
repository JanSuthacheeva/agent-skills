import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'

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
    return JSON.parse(readFileSync(this.#path, 'utf8')) as Bookmark[]
  }

  save(bookmarks: Bookmark[]): void {
    writeFileSync(this.#path, `${JSON.stringify(bookmarks, null, 2)}\n`)
  }

  add(url: string, title: string, now: Date = new Date()): Bookmark {
    return this.importAll([{ url, title }], now)[0]!
  }

  list(): Bookmark[] {
    return this.load()
  }

  get(id: number): Bookmark {
    const bookmark = this.load().find(one => one.id === id)
    if (bookmark === undefined) throw new BookmarkNotFoundError(id)
    return bookmark
  }

  remove(id: number): Bookmark {
    const all = this.load()
    const bookmark = all.find(one => one.id === id)
    this.save(all.filter(one => one.id !== id))
    return bookmark ?? { id, url: '', title: '', createdAt: '' }
  }

  importAll(entries: { url: string; title: string }[], now: Date = new Date()): Bookmark[] {
    const all = this.load()
    let next = Math.max(0, ...all.map(one => one.id)) + 1
    const added = entries.map(entry => ({ id: next++, url: entry.url, title: entry.title, createdAt: now.toISOString() }))
    this.save([...all, ...added])
    return added
  }
}
