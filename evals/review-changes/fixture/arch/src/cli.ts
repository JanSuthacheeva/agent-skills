import type { Bookmark } from './bookmark.ts'
import type { BookmarkStore } from './store.ts'
import { BookmarkNotFoundError } from './store.ts'
import { InvalidTagError, normalizeTag } from './tags.ts'

export interface Output {
  log(line: string): void
  error(line: string): void
}

export function run(argv: string[], store: BookmarkStore, out: Output): number {
  try {
    return dispatch(argv, store, out)
  } catch (error) {
    if (error instanceof InvalidTagError) {
      out.error(`invalid tag: ${error.raw}`)
      return 2
    }
    if (error instanceof BookmarkNotFoundError) {
      out.error(`no bookmark ${error.id}`)
      return 1
    }
    throw error
  }
}

function dispatch(argv: string[], store: BookmarkStore, out: Output): number {
  const [command, ...args] = argv
  switch (command) {
    case 'add': {
      const [url, ...title] = args
      if (url === undefined) {
        out.error('usage: bm add <url> [title]')
        return 2
      }
      const bookmark = store.add(url, title.join(' ') || url)
      out.log(`added ${bookmark.id}`)
      return 0
    }
    case 'tag': {
      const [rawId, rawTag] = args
      const id = Number(rawId)
      if (!Number.isInteger(id) || rawTag === undefined) {
        out.error('usage: bm tag <id> <tag>')
        return 2
      }
      const tag = normalizeTag(rawTag)
      const bookmarks = store.list()
      const bookmark = bookmarks.find(one => one.id === id)
      if (bookmark === undefined) throw new BookmarkNotFoundError(id)
      if (!bookmark.tags.includes(tag)) bookmark.tags.push(tag)
      store.save(bookmarks)
      out.log(`tagged ${id} ${tag}`)
      return 0
    }
    case 'list': {
      const bookmarks = args[0] === '--tag' && args[1] !== undefined ? store.listByTag(args[1]) : store.list()
      for (const bookmark of bookmarks) out.log(format(bookmark))
      return 0
    }
    default:
      out.error(`unknown command: ${command ?? ''}`)
      return 2
  }
}

function format(bookmark: Bookmark): string {
  return `${bookmark.id}  ${bookmark.title}  ${bookmark.url}`
}
