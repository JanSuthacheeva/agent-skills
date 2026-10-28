import { homedir } from 'node:os'
import { join } from 'node:path'

import { run } from './cli.ts'
import { BookmarkStore, storeFileName } from './store.ts'

const path = process.env['BM_FILE'] ?? join(homedir(), storeFileName)
process.exitCode = run(process.argv.slice(2), new BookmarkStore(path), console)
