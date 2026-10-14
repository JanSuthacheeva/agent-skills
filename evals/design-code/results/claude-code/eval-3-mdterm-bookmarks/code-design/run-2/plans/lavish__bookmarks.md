# mdterm bookmarks - implementation plan

Design page: [.lavish/bookmarks-implementation.html](bookmarks-implementation.html) (approved 2026-10-02)

## Decision

- **Approach A, source-anchored marks.** The markdown renderer stamps each `Line` with the 0-based source line of the block it came from. `wrap_lines` copies the stamp onto every wrapped row. A mark stores `(line, row, text)`, and a jump maps it back onto the current `wrapped`.
- **Keys.** `m` + `a-z` sets a mark and `'` + `a-z` jumps to it. The mouse-capture toggle moves from `m` to `M`.
- **Names.** Marks are `a-z` only, per file. No uppercase or global marks.
- **Storage.** One `marks.json` in `dirs::data_dir()/mdterm/`, keyed by canonical absolute path. It is not part of `config.toml`.
  - macOS: `~/Library/Application Support/mdterm/marks.json`
  - Linux: `~/.local/share/mdterm/marks.json`
- **Edits.** A mark is re-found by its stored trimmed line text. If the text is gone, it falls back to the stored line number, clamped to EOF.
- **Back navigation** (decided in review). A mark jump pushes `(current_file_idx, offset)` onto `nav_history`, so Backspace returns. There is no `''`.

## Units

### `src/marks.rs` (new)

Owns what a mark is and how one document's marks are read from and written to `marks.json`.

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Mark {
    pub line: usize,   // 0-based source line of the block's first line
    pub row: usize,    // wrapped rows below the block's first row
    pub text: String,  // trimmed text of `line` at set time
}

pub type FileMarks = BTreeMap<char, Mark>;

const FORMAT_VERSION: u32 = 1;

#[derive(Default, Serialize, Deserialize)]
struct MarksFile {
    version: u32,
    files: BTreeMap<String, FileMarks>,
}

pub struct MarkStore {
    path: Option<PathBuf>,
}

impl MarkStore {
    pub fn open() -> Self;                                            // dirs::data_dir()/mdterm/marks.json, None if no data dir
    pub fn at(path: PathBuf) -> Self;                                 // explicit path (tests)
    pub fn load(&self, doc: &Path) -> FileMarks;                      // never fails; missing/corrupt/newer/no path -> empty
    pub fn save(&self, doc: &Path, marks: &FileMarks) -> io::Result<()>;
}

impl Mark {
    pub fn relocate(&self, source: &str) -> usize;
}

pub fn is_mark_name(c: char) -> bool;                                 // 'a'..='z'

fn marks_path() -> Option<PathBuf>;                                   // mirrors config::config_path
fn doc_key(doc: &Path) -> io::Result<String>;                         // canonicalize -> String
fn read_marks_file(path: &Path) -> io::Result<MarksFile>;             // NotFound -> default; parse error or version > 1 -> InvalidData
```

`save` works in this order:

1. Read the existing file with `read_marks_file`.
2. Replace this document's entry, or remove it if `marks` is empty.
3. Set `version = FORMAT_VERSION`.
4. `create_dir_all` the parent directory.
5. Write `marks.json.tmp` and `rename` it over `marks.json`.

It returns an error in these cases:
- `InvalidData` if the existing file is corrupt or has a newer version. The file is never overwritten.
- `NotFound` if there is no path or `doc` cannot be canonicalized.

`relocate` checks three things in order:
1. If the trimmed text of `source.lines()[line]` equals `text`, it returns `line`.
2. Otherwise, if `text` is non-empty, it returns the nearest line with equal trimmed text. On a tie it picks the one above.
3. Otherwise it returns `line.min(last_line)`.

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    pub source_line: Option<usize>,   // new: 0-based source line of the markdown block
}

pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line>; // unchanged signature
```

- `wrap_lines` makes every produced row inherit `line.source_line`, on all three branches (as-is, blockquote, word_wrap).
- `Line::empty()` sets `source_line: None`.
- All existing `Line { spans, meta }` literals gain `..Default::default()`. That is about 50 sites across json.rs (20), markdown.rs (15), style.rs (13) and viewer.rs (3).

### `src/markdown.rs` (modified)

```rust
struct Renderer<'a> {
    // ...existing...
    line_starts: Vec<usize>,   // byte offset of each source line, built in Renderer::new
}

impl<'a> Renderer<'a> {
    fn stamp_source_lines(&mut self, from: usize, byte_offset: usize); // sets source_line on lines[from..] that are None
}

fn source_line_at(line_starts: &[usize], byte_offset: usize) -> usize;  // binary search; past EOF -> last line

pub fn render_with(input: &str, width: usize, theme: &Theme, line_numbers: bool, syntect_res: &SyntectRes)
    -> (Vec<Line>, DocumentInfo); // unchanged signature
```

The `into_offset_iter` loop changes to the following, and the final `flush_line()` is stamped with the last event's `range.start`:

```rust
let from = renderer.lines.len();
renderer.process(event, range.clone());
renderer.stamp_source_lines(from, range.start);
```

### `src/viewer.rs` (modified)

```rust
use crate::marks::{FileMarks, Mark, MarkStore};

pub struct ViewerOptions {
    // ...existing...
    pub mark_store: MarkStore,
}

enum ViewMode {
    // ...existing...
    MarkSet,
    MarkJump,
}

impl ViewMode {
    /// Modes where the user is typing free-form text or a key argument;
    /// single-letter bindings like `?` or `h` must be passed through as input.
    fn accepts_text_input(self) -> bool; // + MarkSet | MarkJump
}

struct ViewerState {
    // ...existing...
    // Marks for the current file, persisted through `mark_store`
    mark_store: MarkStore,
    marks: FileMarks,
}

impl ViewerState {
    fn load_marks(&mut self);                                     // marks = store.load(path) or empty for stdin
    fn current_path(&self) -> Option<&std::path::Path>;           // files[current_file_idx], None for stdin
    fn mark_at_offset(&self) -> Option<Mark>;                     // from wrapped[offset]; None if no source_line
    fn set_mark(&mut self, name: char);
    fn jump_to_mark(&mut self, name: char);
    fn wrapped_idx_for_source(&self, line: usize, row: usize) -> usize;
}

fn handle_mark_key(state: &mut ViewerState, code: KeyCode);
```

What the new functions do:
- `mark_at_offset`:
  - `line` comes from `wrapped[offset].source_line`.
  - `row` is `offset` minus the index of the first wrapped row with the same `source_line`.
  - `text` is the trimmed line `content.lines()[line]`.
- `wrapped_idx_for_source` finds the block with the greatest `source_line <= line` and returns its first row plus `row`, clamped to the block's last row. It returns 0 if no row has a source line.
- `handle_mark_key`:
  1. Read the current mode, then set `mode = Normal`.
  2. `Char(c)` where `is_mark_name(c)` calls `set_mark(c)` in `MarkSet` or `jump_to_mark(c)` in `MarkJump`.
  3. `Esc` does nothing.
  4. Anything else shows the toast "Marks are a-z".

Changes to existing functions (signatures unchanged):

- **`ViewerState::new`**: stores `opts.mark_store`, then calls `load_marks()`.
- **`handle_event`**: adds the arm `ViewMode::MarkSet | ViewMode::MarkJump => { state.dirty = true; handle_mark_key(state, ke.code); }`.
- **`handle_normal`**:
  - `Char('m')` sets `mode = MarkSet`.
  - `Char('\'')` sets `mode = MarkJump`.
  - The mouse-capture toggle body moves to `Char('M')`.
- **`switch_file`**: calls `self.load_marks()` after `rebuild()`.
- **`finalize_layout`**: rebuilt image rows copy the placeholder's `source_line`.
- **`render_status_bar`**: new branch, after the Search branch, that draws the prompt ` m█ ` (MarkSet) or ` '█ ` (MarkJump) in `theme.search_prompt`, in the same layout as the search prompt.
- **`render_frame`**: `suppress_images` no longer suppresses in `MarkSet | MarkJump`, so images don't flicker.
- **`help_sections`**:
  - Navigation gets `("m a-z", "Set mark")` and `("' a-z", "Jump to mark")`.
  - Backspace's text becomes "Go back (after a link or mark jump)".
  - Actions: `("M", "Toggle mouse capture (for text select)")` replaces the `m` entry.

### `src/main.rs` (modified)

```rust
mod marks;

let opts = viewer::ViewerOptions {
    // ...existing...
    mark_store: marks::MarkStore::open(),
};
```

### `README.md` (modified)

- Navigation table: add `m` + `a-z` (set mark) and `'` + `a-z` (jump to mark). Change Backspace to "Go back (after a local file link or mark jump)".
- Features table: add `M` (toggle mouse capture). It was previously undocumented.
- Add a note on where `marks.json` lives, next to the config file section.

## Data

`Mark`, `FileMarks` (`BTreeMap<char, Mark>`) and `MarksFile { version: u32, files: BTreeMap<String, FileMarks> }` are defined above.

On disk (`marks.json`):

```json
{
  "version": 1,
  "files": {
    "/Users/jan/notes/setup.md": {
      "a": { "line": 41, "row": 0, "text": "## Installing on macOS" }
    }
  }
}
```

`Line.source_line: Option<usize>`:
- `Some` for every line the markdown renderer emits. Spacer and rule lines take the line of the event that pushed them, and End events carry the block's range, so a block's lines get the block's first line.
- `None` for JSON output.

## Call chains

### Set a mark (`m`, `a`)

1. `handle_event -> handle_normal(state, KeyCode::Char('m'), mods): bool`, which sets `state.mode = ViewMode::MarkSet`. The status bar shows ` m█ `.
2. `handle_event -> handle_mark_key(state, KeyCode::Char('a'))`, which sets `mode = Normal` and checks `is_mark_name('a'): true`.
3. `handle_mark_key -> ViewerState::set_mark('a')`
4. `ViewerState::set_mark -> ViewerState::mark_at_offset(): Option<Mark>`
5. `ViewerState::set_mark -> FileMarks::insert('a', mark)`
6. `ViewerState::set_mark -> ViewerState::current_path(): Option<&Path>`
7. If the path is `Some`: `ViewerState::set_mark -> MarkStore::save(path, &marks): io::Result<()>`. This reads marks.json, merges this document's entry, writes the tmp file and renames it.
8. `ViewerState::set_mark -> ViewerState::set_toast("Mark 'a' set")`

Error paths:
- The key is not a-z: `handle_mark_key` shows the toast "Marks are a-z" and the mode is Normal.
- `Esc`: the mode is Normal and there is no toast.
- `mark_at_offset` returns `None` (JSON view): `set_mark` shows "Marks unavailable in this view" and stores nothing.
- `save` returns `Err(e)` (unwritable dir, corrupt or newer file, path not canonicalizable): the mark is kept in memory and `set_mark` shows "Mark 'a' set, not saved: {e}".
- stdin (`current_path` returns `None`): save is skipped, the toast is "Mark 'a' set", and the mark lasts for the session only.

### Jump to a mark (`'`, `a`)

1. `handle_event -> handle_normal(state, KeyCode::Char('\''), mods): bool`, which sets `state.mode = ViewMode::MarkJump`. The status bar shows ` '█ `.
2. `handle_event -> handle_mark_key(state, KeyCode::Char('a'))`, which sets `mode = Normal`.
3. `handle_mark_key -> ViewerState::jump_to_mark('a')`
4. `ViewerState::jump_to_mark -> FileMarks::get(&'a'): Option<&Mark>`
5. `ViewerState::jump_to_mark -> Mark::relocate(&self.content): usize`
6. `ViewerState::jump_to_mark -> ViewerState::wrapped_idx_for_source(line, mark.row): usize`
7. `ViewerState::jump_to_mark -> nav_history.push((current_file_idx, offset))`, then `offset = idx.min(max_offset())`
8. `ViewerState::jump_to_mark -> ViewerState::set_toast("Jumped to mark 'a'")`
9. Later, Backspace pops `nav_history` (existing code, src/viewer.rs:1765) and returns to the position from before the jump.

Error paths:
- The mark is not set: the toast is "Mark 'a' not set" and the offset is unchanged.
- The marked text was deleted: `relocate` falls back to the stored line, clamped to EOF. It does not fail.
- No stamped rows (JSON): unreachable, because `set_mark` can't store a mark there. `wrapped_idx_for_source` returns 0.

### Load marks (startup, file switch)

1. `main -> marks::MarkStore::open(): MarkStore`, passed as `ViewerOptions.mark_store`
2. `viewer::run -> ViewerState::new(opts, cols, rows) -> ViewerState::load_marks()`
3. `ViewerState::load_marks -> ViewerState::current_path(): Option<&Path>`. For `None`, `marks = FileMarks::new()`.
4. `ViewerState::load_marks -> MarkStore::load(path): FileMarks`
5. On Tab, Shift+Tab, a local link or Backspace: `ViewerState::switch_file(idx) -> rebuild() -> load_marks()`

Error paths:
- marks.json is missing, unreadable, corrupt or a newer version: `load` silently returns an empty map. The next `save` returns `InvalidData` and the user sees the "not saved" toast.
- The platform has no data dir: the store's path is `None`, `load` returns an empty map, and `save` returns `NotFound`.

### Rendering (source line stamping)

1. `ViewerState::rebuild -> markdown::render_with(content, cw, theme, line_numbers, syntect_res): (Vec<Line>, DocumentInfo)`
2. `render_with -> Renderer::new(..)`, which builds `line_starts`
3. For each `(event, range)`: `from = renderer.lines.len()`, then `Renderer::process(event, range.clone())`, then `Renderer::stamp_source_lines(from, range.start)`
4. `Renderer::stamp_source_lines -> source_line_at(&self.line_starts, byte_offset): usize`
5. `render_with -> Renderer::flush_line()`, then `Renderer::stamp_source_lines(from, last_start)`
6. `ViewerState::rebuild -> style::wrap_lines(&lines, cw): Vec<Line>`, where every row inherits `source_line`
7. `ViewerState::rebuild -> ViewerState::finalize_layout()`, where rebuilt image rows keep `source_line`

Error paths: none. Stamping is total, and JSON rendering leaves `None`.

## Test seams

- **`MarkStore`**: unit tests using `MarkStore::at(std::env::temp_dir().join(<unique>))`. Cover:
  - loading a missing file
  - a save/load round trip
  - a save that keeps other documents' entries
  - refusing to overwrite a corrupt file or a newer version
  - removing an emptied document's entry
- **`Mark::relocate`**: pure tests for:
  - unchanged line
  - text moved down or up
  - a tie between two matches
  - text deleted
  - empty text
  - a line past EOF
- **`source_line_at` / `render_with`**:
  - a heading on line 3 gives `Some(2)`
  - code block and table lines get the block's start line
  - JSON lines are `None`
- **`wrap_lines`**: a wrapped paragraph gives every row the same `source_line`, including in a blockquote.
- **`ViewerState` mark methods**: use a `make_state_with_lines`-style helper with a temp `MarkStore`. Cover:
  - set then jump round-trips
  - a mark survives a rebuild at a different width
  - `wrapped_idx_for_source` clamps `row`
  - a jump pushes `nav_history` and Backspace returns
- **`handle_mark_key` / `is_help_toggle`**:
  - `?` in `MarkSet` does not open help
  - a non-letter returns to Normal with a toast
  - `help_sections_no_duplicate_keys` still passes
- **End-to-end** (manual, real terminal): set marks, resize, quit, reopen and jump. Then edit the file above a mark with auto-reload on and jump again.

## Assumptions

1. "Current position" means the top visible row (`state.offset`).
2. Slide mode has no marks, because `handle_slide_keys` owns every key there. In JSON views, `m` shows "Marks unavailable in this view".
3. Marks on stdin input last for the session only and are never written.
4. Setting a letter that is already used overwrites it. There is no delete command or marks list in this iteration.
5. Precision is per block plus a row offset. After a resize, `row` is clamped to the block's length.
6. Relocation happens only at jump time. The stored `line` is never rewritten.
7. There is no locking between instances: each save re-reads and merges, and the last writer wins only for the same document.
8. On-disk line numbers are 0-based, and toasts do not show line numbers.
