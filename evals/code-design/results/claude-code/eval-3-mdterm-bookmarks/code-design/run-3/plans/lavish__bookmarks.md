# Bookmarks (m / ') - implementation plan

Review surface: [.lavish/bookmarks-implementation.html](bookmarks-implementation.html)
(approaches: [.lavish/bookmarks-approaches.html](bookmarks-approaches.html))

## Decision

- Source-anchored marks (approach B). The markdown renderer stamps each `Line` with its 1-based source line; `wrap_lines` propagates it. A new `marks.rs` maps viewport top <-> `Mark` and owns persistence. `viewer.rs` only handles keys, scrolling and toasts.
- `m` + `a`-`z` sets a mark, `'` + `a`-`z` jumps. Lowercase only - uppercase cancels the sequence like any other key outside `a`-`z`.
- Mouse capture toggle moves from `m` to `M`.
- Storage: one `marks.toml` in `dirs::state_dir()`, else `dirs::data_local_dir()`, under `mdterm/`, keyed by canonical file path.
- `Mark` = source line + row within block + text fingerprint; jumping re-anchors to the nearest line with matching text.
- Reusing a letter overwrites silently (toast "Mark 'a' set").
- Every save prunes paths that no longer exist.
- README: add the new keys, a short Bookmarks note with the marks file location, and fix the macOS config path (`dirs::config_dir()` is `~/Library/Application Support`, not `~/.config`). CLAUDE.md: eleven source files, add `marks.rs`.

## Units

### `src/marks.rs` (new)

Owns bookmark persistence and the mapping between a layout position and a `Mark`. Depends on `crate::style::Line`, `dirs`, `toml`, `serde`; never on the viewer.

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::{fmt, io};

use crate::style::Line;

pub struct MarkStore {
    /// None: session-only (no state dir, or tests).
    path: Option<PathBuf>,
    data: MarksFile,
}

impl MarkStore {
    /// Store backed by the platform state dir; never fails.
    pub fn load() -> Self;
    /// Store backed by `path`; a missing or unreadable file yields an empty store.
    pub fn load_from(path: Option<PathBuf>) -> Self;
    pub fn get(&self, file: &Path, letter: char) -> Option<&Mark>;
    /// Updates memory, then re-reads, merges, prunes missing paths and atomically rewrites.
    pub fn set(&mut self, file: &Path, letter: char, mark: Mark) -> Result<(), MarkStoreError>;
}

/// Builds the mark for wrapped-line index `top` (the viewport top).
pub fn anchor_at(wrapped: &[Line], top: usize, source: &str) -> Option<Mark>;
/// Where `mark` lands in the current layout, re-anchoring by text after edits.
pub fn resolve(mark: &Mark, wrapped: &[Line], source: &str) -> Option<MarkTarget>;

fn marks_path() -> Option<PathBuf>;
fn read_marks_file(path: &Path) -> Result<MarksFile, MarkStoreError>;
/// Writes to a sibling temp file, then renames over `path`.
fn write_marks_file(path: &Path, data: &MarksFile) -> Result<(), MarkStoreError>;
/// Nearest source line whose trimmed text equals `mark.text`, else `mark.line`. Returns (line, exact).
fn relocate(mark: &Mark, source: &str) -> (usize, bool);
```

- `anchor_at`: first line at or after `top` with `Some(source_line)` (search backwards if none); `row` = `top` minus the first wrapped index of that source line's contiguous block; `text` = trimmed source line, capped at 80 chars on a char boundary. `None` if no line has a source line.
- `resolve`: `relocate`, then the first wrapped index whose `source_line >= line`, plus `row` clamped to the end of that block. `None` only if `wrapped` is empty.
- `set`: no state dir -> memory only, `Err(NoStateDir)`. Re-read errors (`Corrupt`, `NewerVersion`) -> never write.

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 1-based line in the markdown source; None for content without a source (JSON view).
    pub source_line: Option<usize>,
}

impl Line {
    /// Line without a source position; renderers stamp it afterwards.
    pub fn new(spans: Vec<StyledSpan>, meta: LineMeta) -> Self;
    pub fn empty() -> Self; // unchanged, source_line: None
}

/// Unchanged signature; every wrapped row (plain and blockquote branch) inherits `source_line`.
pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line>;
```

All `Line { .. }` literals in `markdown.rs`, `json.rs`, `style.rs` and `viewer.rs` (including tests) move to `Line::new`.

### `src/markdown.rs` (modified)

```rust
/// Unchanged signature; every returned line now carries `source_line`.
pub fn render_with(input: &str, width: usize, theme: &Theme, line_numbers: bool, syntect_res: &SyntectRes) -> (Vec<Line>, DocumentInfo);

/// Byte offset -> 1-based source line, built once per render.
struct SourceLines { starts: Vec<usize> }
impl SourceLines {
    fn new(source: &str) -> Self;
    fn line_of(&self, byte: usize) -> usize;
}

/// Sets `source_line` on lines that do not have one yet.
fn stamp_source_line(lines: &mut [Line], line: usize);
```

In the `into_offset_iter` loop: record `renderer.lines.len()`, call `process`, stamp the new lines with `line_of(range.start)`. Stamp lines from the final `flush_line` with the last source line. `Renderer` is unchanged.

### `src/viewer.rs` (modified)

```rust
pub struct ViewerOptions {
    // ...existing fields
    pub marks: crate::marks::MarkStore,
}

/// Second key expected after `m` or `'`.
#[derive(PartialEq, Copy, Clone, Debug)]
enum PendingMark { Set, Jump }

struct ViewerState {
    // ...existing fields
    // Bookmarks
    marks: crate::marks::MarkStore,
    pending_mark: Option<PendingMark>,
}

impl ViewerState {
    /// Canonical path of the current markdown file; None for stdin and JSON.
    fn markable_file(&self) -> Option<PathBuf>;
    /// Wrapped-line index at the top of the view (slide start in slide mode).
    fn top_line(&self) -> usize;
    /// Puts `line_idx` at the top (clamped to max_offset), or selects the slide containing it.
    fn scroll_to_line(&mut self, line_idx: usize);
    fn set_mark(&mut self, letter: char);
    fn jump_to_mark(&mut self, letter: char);
}

/// Completes a pending `m` / `'` sequence; any key other than a-z cancels it.
fn handle_mark_key(state: &mut ViewerState, pending: PendingMark, code: KeyCode);
```

Changed, signatures unchanged:
- `handle_event`: after the Ctrl+C check and before `is_help_toggle`, `if let Some(p) = state.pending_mark.take()` -> `handle_mark_key`, mark dirty, return `false`.
- `handle_normal`: `m` -> `pending_mark = Some(Set)`, `'` -> `Some(Jump)`, mouse-capture arm moves to `M`.
- `handle_slide_keys`: same `m` / `'` arms.
- `finalize_layout`: expanded image rows copy the placeholder's `source_line`.
- `render_status_bar`: show ` m█ ` / ` '█ ` while pending (search-prompt style, also in slide mode).
- `help_sections`: Navigation gets `("m + a-z", "Set mark at current position")` and `("' + a-z", "Jump to mark")`; Actions changes to `("M", "Toggle mouse capture (for text select)")`.
- Test helper `make_state_with_lines` passes `marks: MarkStore::load_from(None)`.

### `src/main.rs` (modified)

`mod marks;` and `marks: marks::MarkStore::load()` in the interactive `ViewerOptions`.

### `src/json.rs` (modified)

Mechanical: `Line { .. }` -> `Line::new(..)`; `source_line` stays `None`.

## Data

```rust
/// A bookmark anchored to the markdown source, independent of layout.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Mark {
    pub line: usize,  // 1-based source line of the block at the viewport top
    pub row: usize,   // wrapped rows from the block's first row to the viewport top
    pub text: String, // trimmed source line (max 80 chars), for re-anchoring
}

#[derive(Debug, PartialEq)]
pub struct MarkTarget {
    pub line_idx: usize,
    pub exact: bool, // false: text not found, stored line number used
}

#[derive(Debug)]
pub enum MarkStoreError { NoStateDir, Corrupt(PathBuf), NewerVersion(u32), Io(io::Error) }
impl fmt::Display for MarkStoreError { /* user-facing toast text */ }

const MARKS_FILE_VERSION: u32 = 1;

#[derive(Debug, Serialize, Deserialize)]
struct MarksFile {
    #[serde(default = "default_version")] // missing version reads as 1
    version: u32,
    #[serde(default)]
    files: BTreeMap<String, BTreeMap<String, Mark>>, // canonical path -> letter -> mark
}
impl Default for MarksFile { /* version: MARKS_FILE_VERSION, files: empty */ }
fn default_version() -> u32;
```

`marks.toml`:

```toml
version = 1

[files."/Users/jan/notes/rust.md".a]
line = 142
row = 0
text = "## Ownership"
```

If `version` is greater than `MARKS_FILE_VERSION`, return `NewerVersion` and do not write.

## Call chains

### Startup and render

1. `main -> MarkStore::load(): MarkStore` -> `marks_path()` -> `MarkStore::load_from(path)`
2. `MarkStore::load_from -> read_marks_file(&path): Result<MarksFile, MarkStoreError>`; any `Err` -> empty store, file untouched
3. `main -> viewer::run(ViewerOptions { marks, .. })` -> `ViewerState::new` moves the store into state
4. `ViewerState::rebuild -> markdown::render_with(..): (Vec<Line>, DocumentInfo)`
5. `render_with -> stamp_source_line(&mut lines[before..], source_lines.line_of(range.start))` per event
6. `ViewerState::rebuild -> wrap_lines(&lines, cw)`: rows inherit `source_line`
7. `ViewerState::rebuild -> finalize_layout()`: expanded image rows copy `source_line`

Errors: no state dir -> session-only store (the next set toasts "not saved"). Corrupt or newer file -> empty store; the next `set` re-reads, hits the same error and refuses to write.

### `m` + letter (set)

1. `handle_event -> handle_normal(state, Char('m'), mods)`: `pending_mark = Some(Set)`
2. Next key: `handle_event -> handle_mark_key(state, Set, Char('a'))` (before `is_help_toggle`)
3. `handle_mark_key -> ViewerState::set_mark('a')`
4. `set_mark -> markable_file(): Option<PathBuf>`
5. `set_mark -> marks::anchor_at(&self.wrapped, self.top_line(), &self.content): Option<Mark>`
6. `set_mark -> MarkStore::set(&file, 'a', mark): Result<(), MarkStoreError>` (overwrites any existing `a`)
7. `MarkStore::set -> read_marks_file`, merge, prune missing paths, `write_marks_file` (tmp + rename)
8. `set_mark -> set_toast("Mark 'a' set")`

Errors:
- Step 2, key not in `a`-`z` (uppercase, Esc, `?`, ...) -> cancel silently, key swallowed. Ctrl+C still quits.
- Step 4 `None` -> toast "Marks need a markdown file".
- Step 5 `None` -> toast "Nothing to mark here".
- Step 6 `Err(e)` -> the mark stays in memory for the session; toast "Mark 'a' set - not saved: {e}".

### `'` + letter (jump)

1. `handle_event -> handle_normal(state, Char('\''), mods)`: `pending_mark = Some(Jump)`
2. Next key: `handle_event -> handle_mark_key(state, Jump, Char('a'))`
3. `handle_mark_key -> ViewerState::jump_to_mark('a')`
4. `jump_to_mark -> markable_file(): Option<PathBuf>`
5. `jump_to_mark -> MarkStore::get(&file, 'a'): Option<&Mark>`
6. `jump_to_mark -> marks::resolve(&mark, &self.wrapped, &self.content): Option<MarkTarget>`
7. `jump_to_mark -> self.nav_history.push((self.current_file_idx, self.offset))`
8. `jump_to_mark -> scroll_to_line(target.line_idx)`
9. `jump_to_mark -> set_toast("Mark 'a'")`

Errors:
- Step 4 `None` -> "Marks need a markdown file".
- Step 5 or 6 `None` -> "Mark 'a' not set", no scroll.
- `exact == false` -> jump anyway, toast "Mark 'a' - text changed, jumped to line N".
- Jumping never writes.

## Test seams

- `marks::anchor_at` / `resolve` / `relocate`: unit tests on hand-built `Vec<Line>` + source strings (edit above, deleted line, duplicate text -> nearest, row clamped to block, empty layout).
- `MarkStore`: real FS under `std::env::temp_dir()` via `load_from(Some(..))` (round-trip, two stores merge, corrupt / `version = 2` files left byte-identical, missing paths pruned, overwrite). No new dev-dependency.
- `markdown::render_with`: existing `render_test` helper; heading, paragraph, code block, list and table lines carry the expected `source_line`.
- `style::wrap_lines`: all wrapped rows, including the blockquote branch, inherit `source_line`.
- `viewer`: `make_state_with_lines` with `MarkStore::load_from(None)` - `m` `h` sets a mark instead of opening help; `'` `Esc` and `m` `A` cancel; set + resize + jump lands on the same source line; jump pushes `nav_history`; stdin toasts. The existing `help_sections_no_duplicate_keys` covers the help entries.
- E2E (manual / `run` skill): set marks, resize, quit, reopen, jump; edit above a mark, jump again.

## Assumptions

1. A mark is the top line of the viewport; jumping puts it back at the top.
2. A jump pushes onto `nav_history`, so Backspace returns.
3. After `m` / `'`, any key outside `a`-`z` cancels silently and is swallowed; the pending key shows in the status bar.
4. Marks are unavailable for stdin and JSON.
5. Slide mode supports marks: set uses the slide's first line, jump selects the slide containing the mark.
6. The file is written on every set (re-read, merge, prune, atomic replace); a jump never writes.
7. A corrupt or newer-version marks file is never overwritten; marks still work for the session.
8. The fingerprint is the trimmed source line, capped at 80 chars; re-anchoring searches the whole file for the nearest exact match.
