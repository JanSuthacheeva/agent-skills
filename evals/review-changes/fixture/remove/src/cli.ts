import { readFileSync } from 'node:fs'

import type { Bookmark } from './bookmark.ts'
import { openUrl } from './opener.ts'
import type { BookmarkStore } from './store.ts'
import { BookmarkNotFoundError } from './store.ts'
import { InvalidUrlError, parseWebUrl } from './urls.ts'

export interface Output {
  log(line: string): void
  error(line: string): void
}

export function run(argv: string[], store: BookmarkStore, out: Output, open: (url: string) => void = openUrl): number {
  try {
    return dispatch(argv, store, out, open)
  } catch (error) {
    if (error instanceof InvalidUrlError) {
      out.error(`invalid url: ${error.raw}`)
      return 2
    }
    if (error instanceof BookmarkNotFoundError) {
      out.error(`no bookmark ${error.id}`)
      return 1
    }
    throw error
  }
}

function dispatch(argv: string[], store: BookmarkStore, out: Output, open: (url: string) => void): number {
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
    case 'import': {
      const [file] = args
      if (file === undefined) {
        out.error('usage: bm import <file>')
        return 2
      }
      const raw = JSON.parse(readFileSync(file, 'utf8')) as { url: string; title?: string }[]
      const entries = raw.map(entry => ({ url: parseWebUrl(entry.url), title: entry.title ?? entry.url }))
      const added = store.importAll(entries)
      out.log(`imported ${added.length}`)
      return 0
    }
    case 'open': {
      const id = Number(args[0])
      if (!Number.isInteger(id)) {
        out.error('usage: bm open <id>')
        return 2
      }
      open(store.get(id).url)
      return 0
    }
    case 'remove': {
      const id = Number(args[0])
      if (!Number.isInteger(id)) {
        out.error('usage: bm remove <id>')
        return 2
      }
      store.remove(id)
      out.log(`removed ${id}`)
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
