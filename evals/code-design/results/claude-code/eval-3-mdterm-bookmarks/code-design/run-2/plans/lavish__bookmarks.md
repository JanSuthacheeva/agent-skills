# mdterm bookmarks - implementation plan

Review page: [.lavish/bookmarks-implementation.html](bookmarks-implementation.html) (approaches: [bookmarks-approaches.html](bookmarks-approaches.html))

## Decision

- Approach B: source-anchored marks. Every rendered `Line` carries the 0-based source line of the block it renders; a mark stores that source line, so it survives resizes, width/theme/line-number changes and sessions. Edits above a mark shift it (vim-like).
- New `src/marks.rs` owns per-file marks and persists them as JSON at `dirs::data_dir()/mdterm/marks.json`.
- `m` + letter sets a mark, `'` + letter jumps. Mouse capture moves from `m` to `M`.
- Review decisions: letters are `a-z` only, all per file. Entries for files that no longer exist are kept in v1 (no pruning).

## Units

### `src/marks.rs` (new) - owns the per-document mark set and persists file-backed marks

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io;
use std::path::{Path, PathBuf};

/// Mark letter -> 0-based source line of the marked block.
pub type FileMarks = BTreeMap<char, usize>;

/// The document a mark belongs to.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum MarkTarget {
    /// Canonical path of a file on disk; persisted.
    File(PathBuf),
    /// Content piped on stdin; kept for this session only.
    Stdin,
}

pub struct MarkStore {
    path: Option<PathBuf>,
    files: BTreeMap<String, FileMarks>,
    stdin: FileMarks,
}

impl MarkStore {
    pub fn load() -> Self;
    pub fn load_from(path: Option<PathBuf>) -> Self;
    pub fn get(&self, target: &MarkTarget, letter: char) -> Option<usize>;
    pub fn set(&mut self, target: &MarkTarget, letter: char, source_line: usize) -> io::Result<()>;
}

pub fn is_mark_letter(c: char) -> bool;

#[derive(Serialize, Deserialize)]
struct MarksFile {
    version: u32,
    files: BTreeMap<String, FileMarks>,
}

impl Default for MarksFile { fn default() -> Self; } // version: 1, empty files

fn marks_path() -> Option<PathBuf>;
fn read_marks_file(path: &Path) -> io::Result<MarksFile>;
fn write_marks_file(path: &Path, file: &MarksFile) -> io::Result<()>;
fn target_key(path: &Path) -> String;
```

- `load()` - `load_from(marks_path())`. Never fails; missing/unreadable file gives an empty store (keeps `path`).
- `load_from(path)` - `None` means never persist (no data dir; tests).
- `get` - reads from memory.
- `set` - updates memory first; for `File` targets with a path: `read_marks_file`, merge this entry, `write_marks_file`. Returns `Err` on read/parse/write failure, mark stays in memory. `Stdin` or `path: None` -> `Ok(())`, no I/O.
- `is_mark_letter` - ASCII `a-z` only.
- `marks_path` - `dirs::data_dir()/mdterm/marks.json`.
- `read_marks_file` - `NotFound` -> `Ok(MarksFile::default())`; bad JSON or unknown `version` -> `Err(InvalidData)` (so the file is never overwritten).
- `write_marks_file` - `create_dir_all`, write `marks.json.tmp`, rename over `marks.json`.
- `target_key` - `path.to_string_lossy()`.

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 0-based line in the markdown source of the block this line renders.
    /// `None` for content without a source position (JSON views).
    pub source_line: Option<usize>,
}

impl Line {
    pub fn empty() -> Self; // source_line: None
}

pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line>; // unchanged signature
```

- All `Line { .. }` literals add `source_line`.
- `wrap_lines` copies `source_line` onto every fragment on both the blockquote path and the plain path (unlike `meta`). `word_wrap` unchanged (emits `None`, caller fills in).

### `src/markdown.rs` (modified) - Renderer stamps lines with their source line

```rust
struct Renderer<'a> {
    // ...existing fields...
    source_line_starts: Vec<usize>, // byte offset of each source line start
    open_block_start: usize,        // byte offset of the most recent Event::Start
    stamped_lines: usize,           // lines in self.lines already stamped
}

impl<'a> Renderer<'a> {
    fn source_owner(&mut self, event: &Event, range: &std::ops::Range<usize>) -> usize;
    fn stamp_new_lines(&mut self, owner_byte: usize);
    fn source_line_of(&self, byte: usize) -> usize;
}

pub fn render_with(input: &str, width: usize, theme: &Theme, line_numbers: bool, syntect_res: &SyntectRes)
    -> (Vec<Line>, DocumentInfo); // unchanged signature
```

- `source_owner` - `End` events -> `range.start`; other events -> `open_block_start`. On `Start`, afterwards records `range.start` as `open_block_start`.
- `stamp_new_lines` - sets `Some(source_line_of(owner_byte))` on `lines[stamped_lines..]`, advances `stamped_lines`.
- `source_line_of` - `partition_point` over `source_line_starts`.
- `Renderer::new` builds `source_line_starts`.
- `render_with` loop: `owner = source_owner(&event, &range); process(event, range); stamp_new_lines(owner);`, after loop `flush_line(); stamp_new_lines(open_block_start)`. Existing push sites only add `source_line: None` to literals.

### `src/json.rs` (modified)

- All `Line { .. }` literals add `source_line: None`. No behaviour change.

### `src/viewer.rs` (modified) - state, modes, helpers

```rust
use crate::marks::{MarkStore, MarkTarget};

pub struct ViewerOptions {
    // ...existing fields...
    pub marks: MarkStore,
}

#[derive(PartialEq, Copy, Clone, Debug)]
enum ViewMode {
    Normal, Search, Toc, LinkPicker, FuzzyHeading, Help,
    /// Waiting for the letter after `m` or `'`.
    MarkPending(MarkAction),
}

#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkAction { Set, Jump }

struct ViewerState {
    // ...existing fields...
    marks: MarkStore,
}

impl ViewerState {
    fn mark_target(&self) -> MarkTarget;
    fn source_line_at_offset(&self) -> Option<usize>;
    fn offset_for_source_line(&self, source_line: usize) -> usize;
}
```

- `ViewerState::new` moves `opts.marks` into `state.marks`.
- `mark_target` - `Stdin` if `files` is empty, else `File(canonicalize(files[current_file_idx]))`, fallback `std::path::absolute`.
- `source_line_at_offset` - `source_line` of the first non-blank row at/below `offset`; `None` if none.
- `offset_for_source_line` - first wrapped row with `source_line >= target`, clamped to `max_offset()`; none -> `max_offset()`.
- `finalize_layout` - rebuilt image rows copy `source_line` from the placeholder.
- `accepts_text_input` unchanged (`?`/F1 while pending open help, cancelling the pending mark).

### `src/viewer.rs` (modified) - key handling

```rust
fn handle_mark_pending(state: &mut ViewerState, action: MarkAction, code: KeyCode);
fn set_mark(state: &mut ViewerState, letter: char);
fn jump_to_mark(state: &mut ViewerState, letter: char);
```

- `handle_normal`: `Char('m')` -> `mode = MarkPending(Set)`; `Char('\'')` -> `mode = MarkPending(Jump)`; `Char('M')` -> existing mouse-capture toggle (moved from `m`).
- `handle_event`: new arm `ViewMode::MarkPending(action) => { state.dirty = true; handle_mark_pending(state, action, ke.code); }`.
- `handle_mark_pending` - sets `mode = Normal`; letter -> `set_mark`/`jump_to_mark`; anything else (incl. Esc) cancels silently.
- `set_mark` / `jump_to_mark` - see call chains.
- Slide mode: not bound (`handle_slide_keys` returns first).

### `src/viewer.rs` (modified) - status bar and help

- `render_status_bar`: early branch before the search-results branch, same style: `╰─ m_ set mark · Esc cancel ──── pos ─╯` / `' _ jump to mark`.
- `help_sections`: Navigation adds `("m + letter", "Set mark at current position")`, `("' + letter", "Jump to mark")`; Actions changes `("m", ...)` to `("M", "Toggle mouse capture (for text select)")`.

### `src/main.rs` (modified)

```rust
mod marks;

// interactive branch
let opts = viewer::ViewerOptions {
    // ...existing fields...
    marks: marks::MarkStore::load(),
};
```

### Docs (modified)

- README controls table: `m` + letter, `'` + letter, `M` mouse capture (previously undocumented), note on where marks are stored.
- CLAUDE.md: "Ten source files" -> eleven, add `marks.rs` bullet.

## Data

| Type | Fields | Boundary |
|---|---|---|
| `Line.source_line` | `Option<usize>`, 0-based source line | markdown.rs -> style::wrap_lines -> viewer.rs |
| `MarkTarget` (pub) | `File(PathBuf)` \| `Stdin` | viewer.rs -> marks.rs |
| `FileMarks` (pub alias) | `BTreeMap<char, usize>` | marks.rs, file format |
| `MarksFile` (private) | `version: u32` (=1), `files: BTreeMap<String, FileMarks>` | marks.rs <-> disk |
| `ViewMode::MarkPending` | `MarkAction` | viewer.rs internal |
| `MarkAction` | `Set` \| `Jump` | viewer.rs internal |

```json
{
  "version": 1,
  "files": {
    "/Users/jan/notes/rust.md": { "a": 42, "b": 7 }
  }
}
```

## Call chains

### Startup

1. `main -> MarkStore::load(): MarkStore`
2. `MarkStore::load -> marks_path(): Option<PathBuf>`
3. `MarkStore::load -> MarkStore::load_from(path): MarkStore`
4. `MarkStore::load_from -> read_marks_file(&path): io::Result<MarksFile>`
5. Error: no data dir or `Err` from `read_marks_file` -> empty store, `path` kept; user sees nothing; the next `set` surfaces the error in its toast.
6. `main -> viewer::run(ViewerOptions { marks, .. })` -> `ViewerState::new` moves store into `state.marks`.

### `m` + `a` (set)

1. `run -> handle_event(state, Key('m')) -> handle_normal(state, Char('m'), mods): bool` -> `mode = MarkPending(Set)`, returns `false`.
2. `run -> render_frame -> render_status_bar(..)` draws `m_ set mark · Esc cancel`.
3. `run -> handle_event(state, Key('a')) -> handle_mark_pending(state, Set, Char('a'))` -> `mode = Normal`.
4. `handle_mark_pending -> is_mark_letter('a'): bool`
5. Error: not a letter (incl. Esc, uppercase) -> return, no toast.
6. `handle_mark_pending -> set_mark(state, 'a')`
7. Error: `state.json_view.is_some()` -> `set_toast("Marks are not available for JSON")`, return.
8. `set_mark -> ViewerState::source_line_at_offset(): Option<usize>`
9. Error: `None` -> `set_toast("Nothing to mark")`, return.
10. `set_mark -> ViewerState::mark_target(): MarkTarget`
11. `set_mark -> MarkStore::set(&target, 'a', line): io::Result<()>` (memory updated)
12. `MarkStore::set -> read_marks_file(&path): io::Result<MarksFile>`, merge entry
13. `MarkStore::set -> write_marks_file(&path, &file): io::Result<()>` (tmp + rename)
14. Error: either returns `Err(e)` -> `set` returns it; mark kept in memory; `set_mark` -> `set_toast("Mark 'a' set (not saved: e)")`.
15. `set_mark -> set_toast("Mark 'a' set")`

### `'` + `a` (jump)

1. `run -> handle_event(state, Key('\'')) -> handle_normal(..)` -> `mode = MarkPending(Jump)`; status bar draws `'_ jump to mark`.
2. `run -> handle_event(state, Key('a')) -> handle_mark_pending(state, Jump, Char('a'))` -> `mode = Normal`, `is_mark_letter` (cancel as above).
3. `handle_mark_pending -> jump_to_mark(state, 'a')`
4. Error: JSON view -> `set_toast("Marks are not available for JSON")`, return.
5. `jump_to_mark -> ViewerState::mark_target(): MarkTarget`
6. `jump_to_mark -> MarkStore::get(&target, 'a'): Option<usize>`
7. Error: `None` -> `set_toast("Mark 'a' not set")`, return.
8. `jump_to_mark -> ViewerState::offset_for_source_line(line): usize`
9. `jump_to_mark` pushes `(current_file_idx, offset)` onto `nav_history`, sets `state.offset`, `set_toast("Mark 'a'")`.
10. Later `Backspace` pops `nav_history` (existing code) and returns.

### Rebuild (startup, resize, reload, theme, `l`)

1. `ViewerState::rebuild -> markdown::render_with(content, cw, theme, line_numbers, res): (Vec<Line>, DocumentInfo)`
2. `render_with -> Renderer::new(..)` builds `source_line_starts`.
3. Per `(event, range)`: `render_with -> Renderer::source_owner(&event, &range): usize`
4. `render_with -> Renderer::process(event, range)` (unchanged)
5. `render_with -> Renderer::stamp_new_lines(owner) -> source_line_of(owner): usize`
6. After loop: `flush_line()`, `stamp_new_lines(open_block_start)`.
7. `ViewerState::rebuild -> style::wrap_lines(&lines, cw): Vec<Line>` copies `source_line` to all fragments.
8. `ViewerState::rebuild -> finalize_layout()` keeps `source_line` on resized image rows.
9. No error path. JSON views produce `None` everywhere.

## Test seams

- `marks.rs`: unit tests on `MarkStore::load_from(Some(tmp))` with a unique path under `std::env::temp_dir()` (no new dev-dependency). Round trip; `set` merges with another writer's entries; corrupt file untouched + `set` returns `Err` while `get` still works; `load_from(None)` and `Stdin` never touch disk; char keys survive JSON; `is_mark_letter` rejects uppercase.
- `markdown.rs`: `render_test` asserts `source_line` on headings, paragraphs, code blocks, tables, consecutive list items (incl. items flushed by the next `Start`).
- `style.rs`: `wrap_lines` copies `source_line` to every fragment, plain and blockquote paths.
- `viewer.rs`: `make_state_with_lines` gets `marks: MarkStore::load_from(None)`. Key-sequence tests via `handle_event`: `m a`, scroll, `' a` restores offset; `m Esc` does not quit; `M` toggles mouse; after rebuild at different width the mark lands on the same source line. Existing help tests cover the help table.
- E2E: in tmux, `cargo run -- test.md` at 80 cols, `m a`, quit; relaunch at 120 cols, `' a` lands on the same heading; `marks.json` has the entry.

## Assumptions

1. Marked position = first non-blank row at the top of the viewport.
2. Marks resolve to block start (paragraph, heading, code block, list item, table); inside a long paragraph a jump lands on its first row.
3. Jump puts the marked row at the top of the viewport, clamped near EOF.
4. A mark past EOF after edits jumps to the end.
5. Re-setting a letter overwrites silently; toast "Mark 'a' set".
6. After `m`/`'`, any non-letter key (incl. Esc, uppercase) cancels without a toast; Esc does not quit while pending.
7. Status bar shows the pending hint until the letter arrives.
8. Jumping pushes onto `nav_history`; Backspace returns.
9. Not available in slide mode.
10. JSON view: both keys toast "Marks are not available for JSON".
11. Stdin content gets session-only marks.
12. Files keyed by canonical absolute path; rename/move loses marks; symlinks share with their target.
13. Concurrent instances: `set` re-reads and merges; marks set elsewhere after startup are seen only after restart.
14. Unreadable or newer-version `marks.json` is never overwritten; marks work in-session with a "not saved" toast.
15. No data directory: in-session only, silently.
16. Entries for missing files are kept (no pruning in v1).
17. Out of scope for v1: listing marks, deleting marks, `''`/backtick jump-back, gutter indicators, global/uppercase marks.
18. Moving mouse capture to `M` is a breaking keybinding change, documented in README and help, no alias.

## Decisions made in review

- Approach B (source-anchored marks).
- Mouse capture moves to `M`.
- Mark letters: `a-z` only, per file.
- Stale entries for missing files: kept in v1.
