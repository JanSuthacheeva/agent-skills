# Bookmarks (marks) - Design

Date: 2026-10-01
Status: Approved design, pending spec review

## Goal

Vim/less-style marks in the mdterm viewer:

- `m` + letter sets a mark at the current position.
- `'` + letter jumps to it.
- Marks persist per file between sessions.

Purpose: return to spots in long documents (specs, notes, runbooks) that are re-read and edited over time.

## Success criteria

- A mark lands on the same content after terminal resizes, theme toggles, line-number toggles and image loading.
- A mark follows its content when lines are inserted or deleted above it, including edits picked up by auto-reload.
- Marks survive quitting and restarting mdterm.
- A missing, corrupt or unwritable marks file never breaks the viewer and is never silently overwritten.

## Non-goals

- Uppercase / cross-file (global) marks.
- Deleting marks (re-setting a letter overwrites it).
- A marks list overlay.
- Vim's `''` (Backspace already returns to the pre-jump position).
- Marks in slide mode or the JSON view.
- Pruning entries for files that no longer exist.

## Key bindings

Normal mode only.

| Key | Action |
|---|---|
| `m{a-z}` | Set mark |
| `'{a-z}` | Jump to mark |
| `M` | Toggle mouse capture (moved from `m`) |

- Any key other than `a`-`z` after a prefix, including `Esc`, cancels silently.
- `Ctrl+c` still quits while a prefix is pending.
- Help overlay: `m{a-z}` and `'{a-z}` go in the "Navigation" section. The existing mouse entry in "Actions" changes its key from `m` to `M`.
- README is updated accordingly.

## Architecture

```
markdown text --pulldown-cmark (offset iter)--> Renderer
   --> Vec<Line> with Line.src = source byte offset
   --> wrap_lines (src copied to every wrapped row)
   --> viewer: top row src  --Anchor::capture-->  Anchor  --MarkStore-->  marks.json
       viewer: Anchor::resolve(content) --> byte --> first row of the containing block
```

Units:

- **`style.rs` / `markdown.rs` - provenance.** Every rendered `Line` knows which source byte produced it.
- **`marks.rs` - new module, no terminal code.** `Anchor` (capture and resolve, pure functions over `&str`) and `MarkStore` (load/save).
- **`viewer.rs` - integration only.** Key handling, row <-> byte mapping, toasts, status hint, help text.

### Provenance: `Line.src`

- `Line` gets `pub src: Option<usize>`, a byte offset into the source markdown. All existing `Line { .. }` literals get `src: None`.
- Stamping happens in a single place, the `render_with` event loop. After each `renderer.process(event, range)`, every line pushed during that call whose `src` is `None` gets `range.start`. Blocks flushed on their `End` event get the block's start offset, because the `End` range covers the whole element.
- Code blocks are the one exception: each code line gets its own offset (text range start plus the bytes preceding that line). Those lines are already `Some` when the loop's stamping runs, so they keep their per-line value.
- `wrap_lines` copies `src` to every wrapped row on every path (plain, blockquote, continuation), independent of the existing `meta` propagation rules.
- Image rows expanded in `finalize_layout` copy `src` from their placeholder line.
- JSON renderer lines stay `src: None`.

Resulting granularity: prose marks resolve to a block (paragraph, list item, heading, table). Code-block marks resolve to a single line. A mark set partway down a long wrapped paragraph jumps to the paragraph's first row.

### Anchor (`marks.rs`)

```rust
pub struct Anchor {
    pub line: usize,   // 0-based source line
    pub text: String,  // trimmed line text, truncated to 256 chars
}

pub struct Resolved {
    pub byte: usize,   // byte offset of the resolved line start
    pub line: usize,
    pub exact: bool,   // false when falling back to the line number
}

impl Anchor {
    pub fn capture(content: &str, byte: usize) -> Anchor;
    pub fn resolve(&self, content: &str) -> Resolved;
}
```

`resolve` checks these in order:

1. `line` exists and its trimmed text equals `text` -> that line, `exact: true`.
2. Otherwise, the nearest line (minimum `|i - line|`, the earlier line on a tie) whose trimmed text equals `text` -> `exact: true`.
3. Otherwise, `line` clamped to the last line (0 for an empty file) -> `exact: false`.

An empty `text` skips steps 1-2 and matches by line number only. Line splitting uses `str::lines`, so CRLF files behave the same as LF files.

### Viewer mapping

- **Set:**
  1. Start from the top visible row (`state.offset`) and scan forward to the first row with `src`. If there is none, scan backward.
  2. Call `Anchor::capture(&content, src)`.
  3. Call `MarkStore::set`.
- **Jump:**
  1. Call `anchor.resolve(&content)`.
  2. Find the largest `src` value `<= resolved.byte`, then the first wrapped row carrying that `src`.
  3. Push `(current_file_idx, offset)` onto `nav_history`.
  4. Set `offset` to that row, clamped to `max_offset()`.
- **Re-anchoring:** if `exact` and `resolved.line != anchor.line`, store the anchor with the new line, so drift doesn't add up over edits. If not `exact`, keep the stored anchor so it can match again if the text comes back.

## Viewer state and key flow

- `enum MarkOp { Set, Jump }` and `pending_mark: Option<MarkOp>` on `ViewerState`, plus `marks: MarkStore`, loaded in `ViewerState::new`.
- `handle_normal`: `m` / `'` only set `pending_mark`, after the guards below. `M` toggles mouse capture, using the existing logic moved from `m`.
- `handle_event`: when `pending_mark` is `Some`, the next key press is consumed before the help-toggle check. That makes `m` then `h` set mark `h`. `Ctrl+c` is checked first and still quits. The prefix is cleared whatever the key was.
- Mouse events, resizes, reloads and file switches do not clear `pending_mark`. The next key resolves against whatever is current.
- Status bar shows `m-` or `'-` while a prefix is pending.

Toasts:

| Situation | Toast |
|---|---|
| Mark set | `Mark a set` |
| Jump, exact | `Jumped to mark a` |
| Jump, fallback | `Jumped to mark a (text not found)` |
| Unknown mark | `Mark a not set` |
| stdin input | `Marks need a file` |
| JSON view | `Marks not available in JSON view` |
| Store unreadable (first set only) | `Marks file unreadable - not saving` |
| Write failure | `Could not save marks` |

### Context guards

| Context | Behaviour |
|---|---|
| Normal markdown view | Marks work, per current file. A jump never switches files. |
| Multiple files (Tab / Shift+Tab) | Each file has its own `a`-`z` namespace. |
| stdin (`files` empty) | Toast `Marks need a file`. Also prevents indexing `files[current_file_idx]`. |
| JSON view (`json_view.is_some()`) | Toast `Marks not available in JSON view`. Invalid JSON falls back to markdown rendering and marks work there. |
| Slide mode | Not bound: `handle_slide_keys` returns before `handle_normal`. |
| Search / TOC / LinkPicker / Fuzzy / Help | Not bound. Search and Fuzzy treat `m` / `'` as typed text. |

## Storage

### Location

- `dirs::state_dir()`, falling back to `dirs::data_dir()`, then `mdterm/marks.json`.
- Linux: `~/.local/state/mdterm/marks.json`. macOS: `~/Library/Application Support/mdterm/marks.json`.
- If neither directory exists, marks are in-memory only.
- Marks are kept separate from `config.toml`: they are state, not configuration.

### Format

```json
{
  "version": 1,
  "files": {
    "/Users/jan/notes/spec.md": {
      "a": { "line": 41, "text": "## Rollout plan" }
    }
  }
}
```

- Keys are `fs::canonicalize(path)` of the viewed file, so relative paths and symlinks share marks.
- If canonicalization fails, the mark is kept in memory under the given path and not persisted.

### `MarkStore`

```rust
pub struct MarkStore {
    path: Option<PathBuf>,
    files: HashMap<PathBuf, BTreeMap<char, Anchor>>,
    writable: bool,
}

impl MarkStore {
    pub fn load() -> Self;                     // default location
    pub fn load_from(path: PathBuf) -> Self;   // tests
    pub fn get(&self, file: &Path, letter: char) -> Option<&Anchor>;
    pub fn set(&mut self, file: &Path, letter: char, anchor: Anchor) -> io::Result<()>;
}
```

- `set` updates memory, then persists straight away. Re-anchoring also goes through `set`.
- Persist steps:
  1. Re-read `marks.json` from disk.
  2. Merge in only the changed `(file, letter)` entry.
  3. Write `marks.json.tmp` in the same directory.
  4. `rename` it over `marks.json` (atomic).
  5. Create the parent directory if it is missing.
- Concurrent instances only conflict on the same file and letter at the same moment, and then the last write wins. No file locking.
- Piped output and HTML export never construct a `MarkStore`.

### Failure behaviour

| Condition | Behaviour |
|---|---|
| File missing | Start empty, writable. |
| Unreadable, invalid JSON, or unknown `version` | Start empty with `writable = false`. Never overwrite. Marks work for the session. The first `set` shows `Marks file unreadable - not saving`, once per session. |
| Write fails | `set` returns `Err`. The viewer shows `Could not save marks`. The mark stays in memory. |
| Re-read during persist fails to parse | Treated like an unreadable file: abort the write, set `writable = false`. |

## Files touched

- `src/marks.rs` (new): `Anchor`, `Resolved`, `MarkStore`, unit tests.
- `src/style.rs`: `Line.src`; `wrap_lines` propagation.
- `src/markdown.rs`: stamping in `render_with`; per-line code offsets; `src: None` on literals.
- `src/json.rs`, `src/export.rs`, `src/viewer.rs`: `src: None` on literals where present.
- `src/viewer.rs`:
  - `MarkOp`, `pending_mark` and `marks` fields
  - pending-key interception in `handle_event`
  - `m` / `'` / `M` bindings and guards
  - status-bar hint
  - help entries
  - `finalize_layout` `src` copy
- `src/main.rs`: `mod marks;`
- `README.md`, `CLAUDE.md`: key docs; architecture list goes from ten to eleven source files.
- `Cargo.toml`: `tempfile` dev-dependency.

## Testing

Unit tests:

- `marks.rs` / `Anchor`:
  - unchanged file
  - lines inserted above
  - lines deleted above
  - mark line edited (fallback, `exact: false`)
  - duplicate lines (nearest wins, earlier on tie)
  - file truncated below the mark line
  - empty file
  - CRLF content
  - empty `text`
- `marks.rs` / `MarkStore`:
  - set/load round trip
  - merge with entries written by another instance between load and set
  - corrupt file is not overwritten and `writable` is false
  - unknown `version` treated as unreadable
  - missing parent directory is created
- `markdown.rs`:
  - `src` set on heading, paragraph, list item and table lines
  - code-block lines carry distinct per-line offsets
- `style.rs`: `src` survives wrapping on plain, blockquote and continuation rows.
- `viewer.rs`:
  - row <-> byte mapping, including a mark line inside a multi-line paragraph
  - pending-prefix interception precedes the help toggle (`m` then `h`)
  - cancel on non-letter
  - stdin and JSON guards

End-to-end, in a real terminal with the built binary:

1. Set marks, resize the terminal, toggle line numbers and theme, and jump.
2. With the file open, insert lines above a mark in an editor, let auto-reload pick it up, and jump.
3. Quit, restart and jump.
4. Corrupt `marks.json`, set a mark, and confirm the file is unchanged and the toast appears.
5. Confirm `M` toggles mouse capture and `m` no longer does.
