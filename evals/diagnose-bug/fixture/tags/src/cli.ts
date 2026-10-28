import type { Bookmark } from './bookmark.ts'
import type { BookmarkStore } from './store.ts'
import { BookmarkNotFoundError } from './store.ts'
import { InvalidTagError } from './tags.ts'

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
      const [rawId, tag] = args
      const id = Number(rawId)
      if (!Number.isInteger(id) || tag === undefined) {
        out.error('usage: bm tag <id> <tag>')
        return 2
      }
      const bookmark = store.tag(id, tag)
      out.log(`tagged ${bookmark.id} ${bookmark.tags.join(',')}`)
      return 0
    }
    case 'list': {
      const [flag, tag] = args
      const bookmarks = flag === '--tag' && tag !== undefined ? store.listTagged(tag) : store.list()
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
