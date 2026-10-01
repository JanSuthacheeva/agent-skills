# mdterm bookmarks - implementation plan

Review page: [bookmarks-implementation.html](bookmarks-implementation.html) (approaches: [bookmarks-approaches.html](bookmarks-approaches.html))

## Decision

- `m` + `a-z` sets a mark at the current position, `'` + `a-z` jumps to it. Marks persist per file across sessions.
- Marks anchor to the **markdown source line** (approach B). Every rendered `Line` carries `source_line: Option<usize>`. A mark stores the source line of the top visible row, and a jump scrolls to the first row rendered from that line or later.
- Persistence lives in a new `src/marks.rs` (`MarkStore`) and is written to `dirs::data_dir()/mdterm/marks.json`.
- Mouse capture toggle moves from `m` to `M`.
- Decided in review:
  - Marks are `a-z` only, per file; `A-Z` cancel like any other key.
  - Resize drift is fixed with the same anchor, as its own commit.
  - JSON view does not support marks and shows a toast.

## Commits

1. `feat(style,markdown): stamp rendered lines with their source line`: `Line.source_line`, renderer stamping, propagation through wrapping, image row expansion and json literals, with tests.
2. `feat(viewer): add per-file bookmarks with m/' and move mouse toggle to M`: `marks.rs`, viewer keys/state, status bar, help, main wiring, README/CLAUDE.md, with tests.
3. `fix(viewer): keep the top source line stable across rebuilds`: the `rebuild()` anchor restore.

## Units

### `src/marks.rs` (new)

Store per-document marks and persist them to `marks.json`. Depends on `dirs`, `serde`, `serde_json` and `std::fs` only.

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io;
use std::path::{Path, PathBuf};

/// Identity of a document across sessions: its canonical absolute path.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(transparent)]
pub struct DocKey(String);

impl DocKey {
    /// `None` for `<stdin>` or a path that cannot be canonicalized.
    pub fn for_file(path: &str) -> Option<DocKey> { ... }
}

/// A saved position, anchored to a 0-based line of the markdown source.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Mark {
    pub source_line: usize,
}

#[derive(Default, Serialize, Deserialize)]
struct MarksFile {
    #[serde(default)]
    files: BTreeMap<DocKey, BTreeMap<char, Mark>>,
}

pub struct MarkStore {
    path: Option<PathBuf>,
    marks: MarksFile,
}

impl MarkStore {
    /// Loads marks.json; a missing, unreadable or corrupt file yields an empty store.
    pub fn load() -> Self { ... }

    /// A store that never touches disk.
    #[cfg(test)]
    pub fn in_memory() -> Self { ... }

    fn open(path: Option<PathBuf>) -> Self { ... }

    pub fn get(&self, doc: &DocKey, name: char) -> Option<Mark> { ... }

    /// Records the mark in memory, then merges it into the file on disk.
    /// The in-memory mark survives a failed save.
    pub fn set(&mut self, doc: &DocKey, name: char, mark: Mark) -> io::Result<()> { ... }
}

/// `Ok(MarksFile::default())` if the file does not exist, `InvalidData` if it does not parse.
fn read_marks_file(path: &Path) -> io::Result<MarksFile> { ... }

/// Writes a sibling temp file and renames it over `path`, creating the parent dir.
fn write_marks_file(path: &Path, marks: &MarksFile) -> io::Result<()> { ... }

/// `dirs::data_dir()/mdterm/marks.json`
fn marks_path() -> Option<PathBuf> { ... }
```

- `load()` keeps `path` even when the file is corrupt, so a later `set` detects `InvalidData` again and never overwrites the file.
- `set` order: insert into `self.marks`, then (if `path` is `Some`) `read_marks_file`, insert into the fresh copy, `write_marks_file`, and replace `self.marks` with the merged copy.

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 0-based markdown source line this row was rendered from; `None` for JSON rows.
    pub source_line: Option<usize>,
}

impl Line {
    pub fn empty() -> Self { ... } // source_line: None
}

pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line> { ... } // signature unchanged
```

- `wrap_lines` / `word_wrap` copy `source_line` to **every** fragment, including in the blockquote branch.
- Update all 11 `Line { .. }` literals.

### `src/markdown.rs` (modified)

```rust
struct Renderer<'a> {
    // ...existing fields

    // Source mapping
    line_starts: Vec<usize>,
    code_block_first_line: usize,
}

impl<'a> Renderer<'a> {
    /// 0-based source line containing `byte_offset` (binary search over `line_starts`).
    fn source_line_at(&self, byte_offset: usize) -> usize { ... }

    /// Sets the source line of `byte_offset` on every line pushed since index `from`
    /// that does not have one yet.
    fn stamp_source_lines(&mut self, from: usize, byte_offset: usize) { ... }
}

/// Byte offset of the start of every source line.
fn line_starts(source: &str) -> Vec<usize> { ... }

pub fn render_with(
    input: &str,
    width: usize,
    theme: &Theme,
    line_numbers: bool,
    syntect_res: &SyntectRes,
) -> (Vec<Line>, DocumentInfo) { ... } // signature unchanged
```

- `Renderer::new` computes `line_starts(source)`.
- `render_with` loop: `let from = renderer.lines.len(); renderer.process(event, range.clone()); renderer.stamp_source_lines(from, range.start);`. After the final `flush_line()`, stamp the remaining lines with the last source line.
- `process`: `Start(Tag::CodeBlock(kind))` sets `code_block_first_line`. For `Fenced` this is the fence line + 1, for `Indented` the start line.
- `emit_code_block`: content row `i` gets `Some(code_block_first_line + i)` directly. Borders, tables, mermaid diagrams and images keep the block start from the stamp.
- All 15 `Line { .. }` literals get `source_line: None`.

### `src/json.rs` (modified, mechanical)

- All 20 `Line { .. }` literals get `source_line: None`.

### `src/viewer.rs` - state (modified)

```rust
use crate::marks::{DocKey, Mark, MarkStore};

pub struct ViewerOptions {
    // ...existing fields
    pub marks: MarkStore,
}

struct ViewerState {
    // ...existing fields

    // Marks
    marks: MarkStore,
    mark_doc: Option<DocKey>,
    pending_mark: Option<MarkPrefix>,
}

impl ViewerState {
    /// Source line of the top visible row, or of the first stamped row below it.
    fn top_source_line(&self) -> Option<usize> { ... }

    /// Offset of the first row rendered from `source_line` or later, clamped to `max_offset()`.
    fn offset_for_source_line(&self, source_line: usize) -> usize { ... }

    /// Saves mark `name` at the top visible source line and toasts the outcome.
    fn set_mark(&mut self, name: char) { ... }

    /// Pushes the current position onto `nav_history` and scrolls to mark `name`, or toasts why not.
    fn jump_to_mark(&mut self, name: char) { ... }
}
```

- `new()`: `mark_doc = DocKey::for_file(&opts.filename)`, `pending_mark = None`.
- `switch_file()`: refresh `mark_doc` for the new path and clear `pending_mark`.
- `finalize_layout()`: expanded image rows copy the placeholder's `source_line`.
- `rebuild()` (commit 3):
  - capture `top_source_line()` before re-rendering;
  - after `finalize_layout()`, set `offset = offset_for_source_line(anchor)`;
  - when the anchor is `None` (JSON view), keep today's `saved_offset.min(max_offset())`.
- Update the 3 `Line { .. }` literals, including the test helper `line()`. `make_state_with_lines` passes `marks: MarkStore::in_memory()`.

### `src/viewer.rs` - key handling (modified + new fn)

```rust
/// First key of a two-key mark command, waiting for the mark letter.
#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkPrefix {
    Set,
    Jump,
}

/// Completes a pending `m` / `'`: `a-z` sets or jumps, any other key (including `A-Z`) cancels.
fn handle_mark_key(state: &mut ViewerState, prefix: MarkPrefix, code: KeyCode) { ... }

fn handle_event(state: &mut ViewerState, ev: Event) -> bool { ... }                       // signature unchanged
fn handle_normal(state: &mut ViewerState, code: KeyCode, mods: KeyModifiers) -> bool { ... } // signature unchanged
```

- `handle_event`: put this right after the Ctrl+c check and **before** `is_help_toggle`. If `state.mode == ViewMode::Normal` and `state.pending_mark.take()` is `Some(prefix)`, call `handle_mark_key(state, prefix, ke.code)`, set `dirty`, and return `false`.
- `handle_normal`:
  - `Char('m')` sets `pending_mark = Some(MarkPrefix::Set)`.
  - `Char('\'')` sets `pending_mark = Some(MarkPrefix::Jump)`.
  - The existing mouse-toggle body moves unchanged to a `Char('M')` arm.
  - These arms come after the slide-mode early return.
- `handle_mark_key`: `KeyCode::Char(c) if c.is_ascii_lowercase()` calls `set_mark(c)` or `jump_to_mark(c)`. Any other key does nothing; the prefix is already cleared.

### `src/viewer.rs` - status bar and help (modified)

- `render_status_bar`: while `pending_mark` is `Some`, show `" m█ "` (Set) or `" '█ "` (Jump) in `theme.search_prompt`, in an early-return branch shaped like the search-input label.
- `help_sections`:
  - Navigation gains `("m a-z", "Set mark")` and `("' a-z", "Jump to mark")`.
  - In Actions, `("m", "Toggle mouse capture (for text select)")` becomes `("M", ...)`.

### `src/main.rs` (modified)

```rust
mod marks;

// interactive branch only (export and piped output never load marks)
let opts = viewer::ViewerOptions {
    // ...existing fields
    marks: marks::MarkStore::load(),
};
```

### Docs (modified)

- README key table: add `m` + `a-z`, `'` + `a-z`, and `M` for mouse capture. The old `m` binding was never listed.
- CLAUDE.md: "Ten source files" becomes eleven, plus a `marks.rs` bullet.

## Data

| Type | Fields | Crosses |
|---|---|---|
| `Line.source_line` | `Option<usize>`, 0-based | markdown.rs / json.rs -> style.rs -> viewer.rs |
| `Mark` | `source_line: usize` | viewer.rs -> marks.rs -> disk |
| `DocKey` | newtype over canonical path `String` | viewer.rs -> marks.rs; disk map key |
| `MarksFile` (private) | `files: BTreeMap<DocKey, BTreeMap<char, Mark>>` | marks.rs <-> disk |
| `MarkPrefix` (private) | `Set \| Jump` | inside viewer.rs |
| `ViewerOptions.marks` | `MarkStore` | main.rs -> viewer.rs |

`marks.json` (`~/Library/Application Support/mdterm/` on macOS, `~/.local/share/mdterm/` on Linux):

```json
{
  "files": {
    "/Users/jan/notes/rust.md": {
      "a": { "source_line": 141 },
      "b": { "source_line": 7 }
    }
  }
}
```

There is nothing to migrate because the file is new.

## Call chains

### Set a mark: `m` `a`

1. `handle_event -> handle_normal(state, Char('m'), mods): false` sets `state.pending_mark = Some(MarkPrefix::Set)`
2. `render_status_bar` shows `" m█ "`
3. `handle_event -> state.pending_mark.take(): Some(MarkPrefix::Set)` (before `is_help_toggle`)
4. `handle_event -> handle_mark_key(state, MarkPrefix::Set, Char('a'))`
   - error: any key other than `a-z` (including `A-Z`): prefix dropped, key swallowed, no toast
5. `handle_mark_key -> ViewerState::set_mark('a')`
   - error: `mark_doc` is `None` (stdin): `set_toast("Marks need a file on disk")`, return
6. `ViewerState::set_mark -> ViewerState::top_source_line(): Option<usize>`
   - error: `None` (JSON view): `set_toast("Marks are not available in JSON view")`, return
7. `ViewerState::set_mark -> MarkStore::set(&doc, 'a', Mark { source_line }): io::Result<()>`
8. `MarkStore::set -> read_marks_file(&path): io::Result<MarksFile>` (fresh read, merges other instances' marks)
9. `MarkStore::set -> write_marks_file(&path, &merged): io::Result<()>` (temp file + rename)
   - error: `InvalidData` (corrupt file) or any IO error: `Err(e)` returned, file untouched, mark kept in memory; `set_mark` toasts `"Mark a set, not saved: {e}"`
10. `ViewerState::set_mark -> set_toast("Mark a set")`

### Jump to a mark: `'` `a`

1. `handle_event -> handle_normal(state, Char('\''), mods): false` sets `pending_mark = Some(MarkPrefix::Jump)`
2. `handle_event -> handle_mark_key(state, MarkPrefix::Jump, Char('a'))`
3. `handle_mark_key -> ViewerState::jump_to_mark('a')`
   - error: `mark_doc` is `None`: `set_toast("Marks need a file on disk")`, return
4. `ViewerState::jump_to_mark -> MarkStore::get(&doc, 'a'): Option<Mark>`
   - error: `None`: `set_toast("Mark a not set")`, return
5. `ViewerState::jump_to_mark -> ViewerState::offset_for_source_line(mark.source_line): usize` (a line past the end clamps to `max_offset()` and is not an error)
6. `ViewerState::jump_to_mark -> nav_history.push((current_file_idx, offset))`
7. `ViewerState::jump_to_mark -> offset = target; set_toast("Jumped to mark a")`

### Render stamping and position restore: any `rebuild()`

1. `ViewerState::rebuild -> ViewerState::top_source_line(): Option<usize>` (anchor; commit 3)
2. `ViewerState::rebuild -> markdown::render_with(&content, cw, &theme, line_numbers, &syntect_res): (Vec<Line>, DocumentInfo)`
3. `render_with -> Renderer::process(event, range.clone())` per event; `emit_code_block` stamps content rows itself
4. `render_with -> Renderer::stamp_source_lines(from, range.start)` per event, filling rows that are still `None`
5. `Renderer::stamp_source_lines -> Renderer::source_line_at(byte_offset): usize`
6. `ViewerState::rebuild -> style::wrap_lines(&lines, cw): Vec<Line>` (fragments copy `source_line`)
7. `ViewerState::rebuild -> ViewerState::finalize_layout()` (image rows copy `source_line`)
8. `ViewerState::rebuild -> ViewerState::offset_for_source_line(anchor): usize`, then `offset =` that value (commit 3)
   - JSON branch: rows keep `None`, the anchor is `None`, and `rebuild` falls back to `saved_offset.min(max_offset())` as today

### Startup

1. `main -> MarkStore::load(): MarkStore`
2. `MarkStore::load -> marks_path(): Option<PathBuf>`
3. `MarkStore::load -> read_marks_file(&path): io::Result<MarksFile>`
   - error: no data dir, or an unreadable or corrupt file: empty store, silently
4. `main -> viewer::run(ViewerOptions { marks, .. }) -> ViewerState::new(opts, cols, rows)`
5. `ViewerState::new -> DocKey::for_file(&opts.filename): Option<DocKey>` (`None` for `<stdin>`)

### Mouse capture: `M`

1. `handle_event -> handle_normal(state, Char('M'), mods)` runs the existing toggle body; behaviour and toasts are unchanged

## Test seams

- **marks.rs (unit)**, using `MarkStore::open(Some(tmp))` under `std::env::temp_dir()`:
  - round trip;
  - `set` merges a mark written externally in between;
  - a corrupt file makes `set` return `InvalidData` and stays byte-identical;
  - a missing parent dir is created;
  - `DocKey::for_file("<stdin>")` is `None`.
- **markdown.rs (unit)**, via `render_test`:
  - a heading on line 0 has `source_line == Some(0)`;
  - a paragraph after a blank line has `Some(2)`;
  - list items are stamped;
  - fenced code content rows are exact;
  - every markdown row is `Some`.
- **style.rs (unit)**: `wrap_lines` on a long stamped line gives every fragment the same `source_line`, including the blockquote branch.
- **viewer.rs (unit)**, using `make_state_with_lines` + `MarkStore::in_memory()` with `mark_doc` set directly:
  - `top_source_line`;
  - `offset_for_source_line` clamping;
  - `handle_event` for `m`,`a`, then a scroll, then `'`,`a` returns to the mark;
  - `m`,`h` does not open help;
  - `Esc` and `m`,`A` cancel;
  - `M` flips `mouse_captured`;
  - `rebuild()` at a different `cols` keeps `top_source_line()`.
- **End to end (manual, real terminal)**:
  - open `test.md`, press `m` `a` mid-document, quit;
  - reopen with a different `-w` and window size, press `'` `a`: it should land on the same text;
  - Backspace returns to where you were;
  - resizing keeps the top text;
  - the help overlay shows `M` and the mark keys.
- Run `cargo fmt`, `cargo clippy -- -D warnings` and `cargo test` before each commit.

## Assumptions

1. Mark names are `a-z` only, local to the file (26 per file). `A-Z` cancel the pending prefix like any other key outside `a-z`.
2. Setting an existing mark overwrites it without asking.
3. A mark saves the top visible row's source line. If that row continues a wrapped paragraph, the jump lands on the paragraph's first row.
4. A jump puts the marked row at the top of the viewport, clamped near the end of the document.
5. If the file shrank below the mark, the jump goes to the end of the document without an error.
6. A jump pushes onto `nav_history`, so Backspace returns to where you were.
7. After `m` or `'` the next key is always consumed. `a-z` acts; anything else (`A-Z`, Esc, digits, `h`, `?`, F1, Tab) cancels silently. Ctrl+c still quits.
8. While waiting for the letter, the status bar shows `m█` or `'█`.
9. Toasts: "Mark a set", "Jumped to mark a", "Mark a not set", "Marks need a file on disk", "Marks are not available in JSON view", "Mark a set, not saved: <error>".
10. Marks do nothing in slide mode, where `m` and `'` stay unbound.
11. JSON view has no marks. A `.json` file that fails to parse and falls back to markdown rendering does support them.
12. A resize, reload, theme or line-number toggle keeps the same source line at the top of the viewport. JSON view keeps today's offset behaviour.
13. stdin input has no marks.
14. A file is identified by its canonical absolute path: renaming or moving a file loses its marks, and symlinks resolve to their target.
15. Storage is `dirs::data_dir()/mdterm/marks.json`, written on every set.
16. With several mdterm instances open, each set re-reads the file and merges into it. The last writer wins per file and letter. Marks set in another instance become visible after your next set or a restart.
17. A corrupt `marks.json` is ignored on load and never overwritten. Marks keep working for the session, with a toast.
18. No delete, list or overlay for marks in v1. Entries for deleted files are never pruned.
19. Source lines are 0-based in memory and on disk.
20. Precision is per line inside code blocks; tables, mermaid diagrams and images resolve to the block start.
21. Mark keys work while search results are active, and `n`/`N` are unaffected.
22. Moving mouse capture from `m` to `M` is a breaking key change and is mentioned in the commit/PR description.
