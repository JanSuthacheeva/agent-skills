import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'

export const storeFileName = '.bookmarks.json'

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
    const all = this.load()
    const bookmark = { id: Math.max(0, ...all.map(one => one.id)) + 1, url, title, createdAt: now.toISOString() }
    this.save([...all, bookmark])
    return bookmark
  }

  list(): Bookmark[] {
    return this.load()
  }
}
