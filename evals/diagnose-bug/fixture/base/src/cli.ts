import type { Bookmark } from './bookmark.ts'
import type { BookmarkStore } from './store.ts'

export interface Output {
  log(line: string): void
  error(line: string): void
}

export function run(argv: string[], store: BookmarkStore, out: Output): number {
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
    case 'list':
      for (const bookmark of store.list()) out.log(format(bookmark))
      return 0
    default:
      out.error(`unknown command: ${command ?? ''}`)
      return 2
  }
}

function format(bookmark: Bookmark): string {
  return `${bookmark.id}  ${bookmark.title}  ${bookmark.url}`
}
