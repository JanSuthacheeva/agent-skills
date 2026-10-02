# mdterm bookmarks - implementation plan

Review page: [.lavish/bookmarks-implementation.html](bookmarks-implementation.html)

## Decision

- Source-anchored marks: every rendered `Line` carries its 1-based source line; a mark stores `source line + trimmed line text`, re-located by text after edits and mapped back to the current wrapped line on jump.
- `m` + `a-z` sets, `'` + `a-z` jumps. Lowercase only, per file. No uppercase/global marks, no `''`.
- Mouse capture toggle moves from `m` to `M`.
- Store: `dirs::state_dir()` falling back to `dirs::data_dir()`, then `mdterm/marks.json`. One JSON file for all files, keyed by canonical absolute path (renames/moves lose marks - accepted).
- stdin input: marks kept in memory only.

## Units

### `src/marks.rs` (new)

Load, save and re-locate a file's bookmarks. Knows nothing about the viewer.

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io;
use std::path::{Path, PathBuf};

/// 1-based source line plus that line's trimmed text.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Mark {
    pub line: usize,
    pub text: String,
}

#[derive(Debug, PartialEq)]
pub enum Resolution {
    Exact(usize),       // text still on the stored line
    Moved(usize),       // text found on another line (nearest occurrence)
    Approximate(usize), // text gone; stored line clamped to document
}

#[derive(Default, Debug)]
pub struct FileMarks {
    marks: BTreeMap<char, Mark>,
}

impl Mark {
    /// None if `line` does not exist in `source`.
    pub fn capture(source: &str, line: usize) -> Option<Self>;
    /// Never fails: exact, nearest same text, or clamped line.
    pub fn resolve(&self, source: &str) -> Resolution;
}

impl FileMarks {
    /// Empty on missing, unreadable or corrupt store (like Config::load).
    pub fn load(file: &Path) -> Self;
    /// Re-reads the store, replaces this file's entry, writes atomically.
    /// Err (and no write) if no store dir, canonicalize fails, store corrupt, or I/O fails.
    pub fn save(&self, file: &Path) -> io::Result<()>;
    pub fn get(&self, letter: char) -> Option<&Mark>;
    /// Inserts or overwrites.
    pub fn set(&mut self, letter: char, mark: Mark);

    fn load_from(store: &Path, key: &str) -> Self;              // test seam
    fn save_to(&self, store: &Path, key: &str) -> io::Result<()>; // test seam
}

/// state_dir().or_else(data_dir) / "mdterm" / "marks.json"
fn store_path() -> Option<PathBuf>;
/// fs::canonicalize(file) as string
fn store_key(file: &Path) -> Option<String>;
/// NotFound -> Ok(MarkFile::default()); parse failure -> Err(InvalidData)
fn read_mark_file(store: &Path) -> io::Result<MarkFile>;
/// create_dir_all, write marks.json.tmp, rename over marks.json
fn write_mark_file(store: &Path, contents: &MarkFile) -> io::Result<()>;
```

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 1-based source markdown line; None without a markdown source (JSON views).
    pub source_line: Option<usize>,
}

// Signature unchanged; every wrapped piece (incl. blockquote path) inherits line.source_line.
pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line>;
```

All `Line { .. }` literals (style.rs ~13, markdown.rs ~15, json.rs ~20, viewer.rs ~3) gain `..Default::default()`. `Line::empty()` sets `None`.

### `src/markdown.rs` - `Renderer` (modified)

```rust
struct Renderer<'a> {
    // ...existing...
    line_starts: Vec<usize>,          // byte offset of each source line start
    event_start: usize,               // byte offset of event being processed
    span_source_line: Option<usize>,  // source line of first span in current_spans
    code_content_line: usize,         // source line of first code row in open block
}

impl<'a> Renderer<'a> {
    fn source_line_of(&self, byte: usize) -> usize;   // binary search line_starts, 1-based
    fn stamp_unstamped(&mut self, from: usize);      // lines[from..] with None -> source_line_of(event_start)
}
```

Changed behaviour:
- `process(event, source_range)`: first sets `event_start = source_range.start`.
- `push_span(..)`: sets `span_source_line` when `current_spans` is empty.
- `flush_line_with_meta(meta)`: stamps the pushed line with `span_source_line.take()`.
- `Start(Tag::CodeBlock)`: sets `code_content_line` (fenced: fence line + 1; indented: start line).
- `emit_code_block()`: code row `i` gets `code_content_line + i` (mermaid diagram rows use fallback).
- `render_with(..)`: `let before = renderer.lines.len(); renderer.process(..); renderer.stamp_unstamped(before);`

### `src/viewer.rs` (modified)

```rust
use std::path::Path;
use crate::marks::{FileMarks, Mark, Resolution};

#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkAction { Set, Jump }

enum ViewMode {
    // ...existing...
    Mark(MarkAction), // waiting for the letter after `m` / `'`
}

impl ViewMode {
    fn accepts_text_input(self) -> bool; // now also true for Mark(_)
}

struct ViewerState {
    // ...existing...
    marks: FileMarks,
}

impl ViewerState {
    fn current_file_path(&self) -> Option<&Path>;          // None for stdin
    fn source_line_at_offset(&self) -> Option<usize>;      // first stamped line at/after offset
    fn line_idx_for_source(&self, source_line: usize) -> Option<usize>; // first wrapped idx of block with greatest source_line <= arg
    fn set_mark(&mut self, letter: char);
    fn jump_to_mark(&mut self, letter: char);
}

fn handle_mark(state: &mut ViewerState, code: KeyCode, action: MarkAction); // always returns to Normal
```

Changes to existing members:
- `ViewerState::new`: `marks = FileMarks::load(path)` if `files` non-empty, else `FileMarks::default()`.
- `switch_file`: reload `marks` for the new path (next to `search.clear()`).
- `handle_normal`: `m` -> `mode = Mark(Set)`; `'` -> `mode = Mark(Jump)`; mouse-capture arm moves to `M`.
- `handle_event`: arm `ViewMode::Mark(action) => { state.dirty = true; handle_mark(state, ke.code, action); }`.
- `finalize_layout`: rebuilt image rows copy `source_line` from placeholder row.
- `render_status_bar`: pending hint ` m_ ` / ` '_ ` in the search-prompt slot.
- `render_frame`: `suppress_images` also allows `Mark(_)`.
- `help_sections`: Navigation adds `("m a-z", "Set mark")`, `("' a-z", "Jump to mark")`; Actions `"m"` -> `"M"`.
- `tests::ALL_MODES`: add both `Mark` variants.

### Other

- `src/main.rs`: `mod marks;` between `markdown` and `style`.
- `src/json.rs`: literals only, no behaviour change.
- `README.md`: key list (marks, `M`). `CLAUDE.md`: eleven source files, describe `marks.rs`.

## Data

```rust
const MARK_FILE_VERSION: u32 = 1;

#[derive(Serialize, Deserialize, Default)]
struct MarkFile {
    version: u32,
    files: BTreeMap<String, BTreeMap<char, Mark>>,
}
```

```json
{
  "version": 1,
  "files": {
    "/home/jan/notes/runbook.md": {
      "a": { "line": 42, "text": "## Rolling back a deploy" }
    }
  }
}
```

- Keys outside `a-z` are ignored on load. A file with no marks is removed from `files` on save.

## Call chains

### Render (every rebuild)
1. ViewerState::rebuild -> markdown::render_with(&content, cw, &theme, line_numbers, &syntect_res): (Vec<Line>, DocumentInfo)
2. render_with -> Parser::into_offset_iter(): (Event, Range<usize>)
3. render_with -> Renderer::process(event, range) (stamps via push_span / flush_line_with_meta / emit_code_block)
4. render_with -> Renderer::stamp_unstamped(lines_before)
5. ViewerState::rebuild -> style::wrap_lines(&lines, cw): Vec<Line> (source_line inherited)
6. ViewerState::rebuild -> ViewerState::finalize_layout() (image rows keep source_line)
- JSON: lines have `source_line = None`; reported later by set_mark.

### `m` then `a` - set
1. handle_event -> handle_normal(state, Char('m'), mods): bool -> mode = Mark(Set)
2. handle_event -> handle_mark(state, Char('a'), MarkAction::Set) -> mode = Normal
3. handle_mark -> ViewerState::set_mark('a')
4. set_mark -> ViewerState::source_line_at_offset(): Option<usize>
5. set_mark -> Mark::capture(&content, line): Option<Mark>
6. set_mark -> FileMarks::set('a', mark)
7. set_mark -> ViewerState::current_file_path(): Option<&Path>
8. set_mark -> FileMarks::save(path): io::Result<()> -> read_mark_file -> write_mark_file
9. set_mark -> set_toast("Mark a set")

Errors:
- Non-letter key (Esc, digit, arrow): back to Normal, no toast. Uppercase: toast "Marks are a-z".
- No source line / capture None (JSON, empty doc): toast "Nothing to mark here", nothing stored.
- stdin (no path): kept in memory, toast "Mark a set".
- save Err: mark kept in memory, toast "Mark a set (not saved: <reason>)". Corrupt marks.json never overwritten.

### `'` then `a` - jump
1. handle_event -> handle_normal(state, Char('\''), mods): bool -> mode = Mark(Jump)
2. handle_event -> handle_mark(state, Char('a'), MarkAction::Jump) -> mode = Normal
3. handle_mark -> ViewerState::jump_to_mark('a')
4. jump_to_mark -> FileMarks::get('a'): Option<&Mark>
5. jump_to_mark -> Mark::resolve(&content): Resolution
6. jump_to_mark -> ViewerState::line_idx_for_source(line): Option<usize>
7. state.offset = idx.min(state.max_offset())
8. On Moved(line): FileMarks::set('a', Mark { line, text }) -> FileMarks::save(path) (heal; error ignored)

Errors:
- get None: toast "Mark a not set".
- Approximate(line): jumps, toast "Mark a: text changed, jumped to line N".
- line_idx_for_source None: toast "Mark a not found", offset unchanged.

### Open / switch file
1. ViewerState::new(opts, cols, rows) or ViewerState::switch_file(idx): bool
2. -> ViewerState::current_file_path(): Option<&Path>
3. -> FileMarks::load(path): FileMarks -> store_path() -> store_key(path) -> read_mark_file(store)
4. state.marks = loaded (FileMarks::default() for stdin)
- No store dir, missing/corrupt file, canonicalize failure: empty marks silently; corruption surfaces on next save.

## Test seams

- marks.rs unit: capture/resolve (exact, moved up/down, nearest duplicate, approximate clamp); load_from/save_to on temp dir (round-trip incl. char keys, preserves other files, refuses corrupt store, ignores non a-z keys).
- markdown.rs unit: fixture with heading, wrapped paragraph, list, fenced code, table -> assert source_line per line.
- style.rs unit: wrap_lines copies source_line to all pieces incl. blockquote.
- viewer.rs unit: via make_state_with_lines - line_idx_for_source, source_line_at_offset, handle_mark transitions (letter/Esc/uppercase), set/jump on stdin state (no disk); Mark modes in is_help_toggle matrix; help has no duplicate keys.
- E2E manual in real TTY: set, resize, jump; quit and reopen; edit above the mark while auto-reload runs.

## Assumptions (confirmed)

1. Position = top line of viewport; jump puts the marked line at the top.
2. Setting an existing letter overwrites silently.
3. No toast on exact jump; only failures and approximate jumps toast.
4. Moved marks are healed (stored line updated) on jump.
5. Jumps do not push onto nav_history.
6. Marks inactive in slide mode and JSON views.
7. Precision is one rendered block; code blocks exact per line.
8. Entries for deleted files are never pruned.
