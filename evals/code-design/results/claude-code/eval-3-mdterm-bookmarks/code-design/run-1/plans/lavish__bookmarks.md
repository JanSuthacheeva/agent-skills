# mdterm bookmarks - implementation plan

Review page: [.lavish/bookmarks-implementation.html](bookmarks-implementation.html) (approaches: [bookmarks-approaches.html](bookmarks-approaches.html))

## Decision

- `m` + letter sets a mark at the top of the viewport, `'` + letter jumps to it. Marks persist per file in `dirs::data_dir()/mdterm/marks.toml`.
- A mark stores the 0-based **source line** of the markdown, not the wrapped-line offset. `Line` gets a `source_line` field, which the renderer stamps and wrapping copies to every piece.
- A mark also stores a **fingerprint**: the marked line's trimmed text, capped at 120 chars. On jump, `Mark::resolve` re-anchors to the nearest line with matching text, so marks survive edits made outside mdterm.
- Mouse capture moves from `m` to `M`.
- Letters are `a`-`z` only, per file. `A`-`Z` are reserved and treated as invalid.

## Units

### `src/marks.rs` (new) - mark model, re-anchoring, persistence

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io;
use std::path::{Path, PathBuf};

const FINGERPRINT_MAX_CHARS: usize = 120;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Mark {
    pub source_line: usize,
    pub fingerprint: String,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum MarkTarget {
    Unchanged(usize),
    Moved(usize),
    NotFound(usize),
}

impl Mark {
    pub fn capture(source: &str, source_line: usize) -> Mark;
    pub fn resolve(&self, source: &str) -> MarkTarget;
}

impl MarkTarget {
    pub fn source_line(self) -> usize;
}

#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct FileMarks(BTreeMap<char, Mark>);

impl FileMarks {
    pub fn get(&self, letter: char) -> Option<&Mark>;
    pub fn set(&mut self, letter: char, mark: Mark);
}

type MarksFile = BTreeMap<String, FileMarks>; // keyed by canonical path

pub struct MarkStore {
    file: Option<PathBuf>,
}

impl MarkStore {
    pub fn open() -> Self;
    pub fn at(file: PathBuf) -> Self;
    pub fn load(&self, doc: &Path) -> FileMarks;
    pub fn save(&self, doc: &Path, marks: &FileMarks) -> io::Result<()>;
}

fn marks_path() -> Option<PathBuf>;
```

- `capture`: the fingerprint is the trimmed text of source line `source_line`, cut to 120 chars on a char boundary. Out of range gives an empty fingerprint.
- `resolve`: returns `Unchanged(source_line)` if the stored line still matches or the fingerprint is empty. Otherwise returns `Moved(n)` for the nearest matching line in the whole file (ties go to the line above), or `NotFound(source_line)` if nothing matches. Comparison uses trimmed, capped text. Line indexing uses `str::lines()`, which agrees with the renderer's `line_starts`.
- `open`: uses `data_dir()/mdterm/marks.toml`. Without a data dir, `file` is `None` and `save` is a no-op `Ok`.
- `load`: returns empty marks if the file is missing or unparsable, or the doc has no entry. Never fails.
- `save`: re-reads the file, replaces this doc's entry, then writes via tmp + rename (creating the parent dir). If the existing file does not parse, returns `io::ErrorKind::InvalidData` without writing.

### `src/style.rs` (modified)

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 0-based line in the source document this line was rendered from.
    pub source_line: Option<usize>,
}

// Unchanged signatures; output lines inherit `source_line` from their input line.
pub fn wrap_lines(lines: &[Line], width: usize) -> Vec<Line>;
fn word_wrap(line: &Line, width: usize) -> Vec<Line>;
```

- `Line::empty()` sets `source_line: None`. Both wrap branches (blockquote and plain) copy `source_line` to every piece.

### `src/markdown.rs` Renderer (modified)

```rust
struct Renderer<'a> {
    // ...existing fields...
    line_starts: Vec<usize>,
    stamped: usize,
    code_block_first_line: usize,
}

impl<'a> Renderer<'a> {
    fn source_line_of(&self, byte: usize) -> usize;   // partition_point over line_starts
    fn stamp_new_lines(&mut self, byte: usize);       // fills None on lines[stamped..], clamps stamped to lines.len()
}

pub fn render_with(input: &str, width: usize, theme: &Theme, line_numbers: bool, syntect_res: &SyntectRes)
    -> (Vec<Line>, DocumentInfo); // unchanged signature
```

- Build `line_starts` in `Renderer::new`.
- All ~15 `Line { .. }` literals get `source_line: None`.
- `render_with` calls `stamp_new_lines(range.start)` after each `process`, and again after the final `flush_line`.
- The `Start(Tag::CodeBlock)` arm sets `code_block_first_line`: the fence line + 1 for fenced blocks, the start line for indented ones.
- `emit_code_block` pre-stamps each code row with `code_block_first_line + line_num`. The label and border rows get the block start through the normal stamp.

### `src/json.rs` (modified)

- All ~20 `Line { .. }` literals get `source_line: None`.

### `src/viewer.rs` (modified)

```rust
use crate::marks::{FileMarks, Mark, MarkStore, MarkTarget};

pub struct ViewerOptions {
    // ...existing fields...
    pub mark_store: MarkStore,
}

#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkAction {
    Set,
    Jump,
}

struct ViewerState {
    // ...existing fields...
    mark_store: MarkStore,
    marks: FileMarks,
    pending_mark: Option<MarkAction>,
}

impl ViewerState {
    fn current_doc_path(&self) -> Option<PathBuf>;          // canonical files[current_file_idx]; None for stdin
    fn source_line_at(&self, offset: usize) -> Option<usize>; // first Some at or after offset
    fn offset_for_source_line(&self, source_line: usize) -> usize; // first wrapped idx with line >= source_line, clamped to max_offset()
    fn set_mark(&mut self, letter: char);
    fn jump_to_mark(&mut self, letter: char);
    fn save_marks(&self) -> io::Result<()>;                 // current_doc_path + mark_store.save; Ok(()) without path
}

fn handle_mark_key(state: &mut ViewerState, code: KeyCode); // takes pending_mark; a-z dispatches, anything else cancels
```

Changes to existing members:

- `ViewerState::new`: store `mark_store` and load `marks` for the initial document (empty for stdin).
- `switch_file`: on success, reload `marks` for the new document and clear `pending_mark`.
- `handle_event`: add an intercept after the Ctrl-C check and before `is_help_toggle`. When `pending_mark.is_some()` and the mode is Normal, call `handle_mark_key`, set `dirty` and return `false`.
- `handle_normal`:
  - `m` sets `pending_mark = Some(Set)`. In JSON view it shows the toast "Marks are not available for JSON" instead.
  - `'` sets `Some(Jump)`.
  - The mouse-capture arm moves to `M`.
  - Slide mode still returns early, so marks are inactive there.
- `finalize_layout`: expanded image rows copy `source_line`.
- `render_status_bar` (normal bar): while a key is pending, the hint is `" m - a-z set mark · Esc cancel "` or `" ' - a-z jump to mark · Esc cancel "`.
- `help_sections`:
  - Navigation adds `("m a-z", "Set mark")` and `("' a-z", "Jump to mark")`.
  - Backspace text becomes "Go back (after link or mark jump)".
  - Actions changes `"m"` to `"M"`.
- `tests::make_state_with_lines`: passes `MarkStore::at(<tempfile>)`.

### `src/main.rs` (modified)

- Add `mod marks;` and pass `mark_store: marks::MarkStore::open()` in the TTY-branch `ViewerOptions`.

### Docs / build

- README Controls: add `m`/`'` mark rows and the `M` mouse-capture row (missing today), and document where `marks.toml` lives.
- CLAUDE.md: "Ten source files" becomes eleven; add a `marks.rs` bullet.
- Cargo.toml: add `[dev-dependencies] tempfile = "3"`.

## Data

| Type | Fields | Crosses |
|---|---|---|
| `Mark` (new) | `source_line: usize`, `fingerprint: String` | viewer <-> marks <-> disk |
| `MarkTarget` (new) | `Unchanged(usize) \| Moved(usize) \| NotFound(usize)` | marks -> viewer |
| `FileMarks` (new) | `BTreeMap<char, Mark>`, serde transparent | viewer <-> marks <-> disk |
| `MarksFile` (private) | `BTreeMap<String, FileMarks>` | marks <-> disk |
| `MarkAction` (private) | `Set \| Jump` | viewer only |
| `Line` (modified) | + `source_line: Option<usize>` | markdown/json -> style -> viewer |
| `ViewerOptions` (modified) | + `mark_store: MarkStore` | main -> viewer |

`marks.toml` (new file, no migration):

```toml
["/Users/jan/notes/rust-book.md"]
a = { source_line = 141, fingerprint = "## Ownership rules" }
t = { source_line = 2, fingerprint = "- [ ] finish chapter 4" }
```

## Call chains

### Set mark (`m`, `a`)

1. run loop -> handle_event(state, Key('m')) -> handle_normal(state, Char('m'), mods): bool - sets `pending_mark = Some(Set)`
2. run loop -> handle_event(state, Key('a')) - intercept -> handle_mark_key(state, Char('a'))
3. handle_mark_key -> ViewerState::set_mark('a')
4. set_mark -> ViewerState::source_line_at(self.offset): Option<usize>
5. set_mark -> Mark::capture(&self.content, line): Mark
6. set_mark -> FileMarks::set('a', mark)
7. set_mark -> ViewerState::save_marks(): io::Result<()> -> current_doc_path(): Option<PathBuf> -> MarkStore::save(&doc, &self.marks): io::Result<()>
8. set_mark -> set_toast("Mark 'a' set")

Error paths:
- E1 `source_line_at` returns None (empty doc) -> toast "Nothing to mark here"; marks unchanged.
- E2 stdin, so no doc path -> `save_marks` returns Ok without writing; toast "Mark 'a' set" (session only).
- E3 `save` returns Err(e) -> the mark stays in memory; toast `"Mark 'a' set, not saved: {e}"`.
- E4 second key is not a-z (Esc, `?`, F1, digit, `A`-`Z`) -> pending cleared silently; no quit, no help.
- E5 `m` in JSON view -> toast "Marks are not available for JSON"; no pending state.

### Jump to mark (`'`, `a`)

1. run loop -> handle_event(Key('\'')) -> handle_normal - sets `pending_mark = Some(Jump)`
2. run loop -> handle_event(Key('a')) - intercept -> handle_mark_key(state, Char('a')) -> ViewerState::jump_to_mark('a')
3. jump_to_mark -> FileMarks::get('a'): Option<&Mark>
4. jump_to_mark -> Mark::resolve(&self.content): MarkTarget
5. on `Moved(n)`: FileMarks::set('a', Mark { source_line: n, fingerprint }) -> save_marks(): io::Result<()>
6. jump_to_mark -> offset_for_source_line(target.source_line()): usize
7. jump_to_mark -> nav_history.push((current_file_idx, offset))
8. jump_to_mark: self.offset = target; set_toast("Jumped to mark 'a'")

Error paths:
- E1 `get` returns None -> toast "Mark 'a' not set"; no scroll, no history entry.
- E2 `resolve` returns `NotFound(line)` -> jump to the stored line; the mark is not rewritten; toast "Mark 'a': text changed, jumped to saved line".
- E3 save after `Moved` fails -> the jump still happens and the in-memory mark is updated; toast `"Jumped to mark 'a', not saved: {e}"`.
- E4 line past the end of the file -> `offset_for_source_line` returns `max_offset()`.
- E5 invalid second key -> cancel silently.

### Load marks (startup, file switch)

1. main -> MarkStore::open(): MarkStore
2. main -> viewer::run(ViewerOptions { mark_store, .. }): io::Result<()>
3. run -> ViewerState::new(opts, cols, rows) -> current_doc_path() -> MarkStore::load(&doc): FileMarks
4. Tab / BackTab / Backspace / dispatch_link -> ViewerState::switch_file(idx): bool -> current_doc_path() -> MarkStore::load(&doc): FileMarks (replaces `marks`, clears `pending_mark`)

Error paths:
- E1 no data dir -> store has no file; load returns empty; save is a no-op Ok.
- E2 marks file missing or corrupt -> load returns empty silently.
- E3 stdin -> `marks = FileMarks::default()`.

### Stamp source lines (render)

1. ViewerState::rebuild -> markdown::render_with(..): (Vec<Line>, DocumentInfo)
2. render_with -> Renderer::new(..) - builds `line_starts`
3. for each (event, range): Renderer::process(event, range.clone()); `End(CodeBlock)` -> emit_code_block() pre-stamps code rows
4. render_with -> Renderer::stamp_new_lines(range.start) -> source_line_of(byte): usize
5. render_with: final flush_line(), then stamp_new_lines(last_start)
6. rebuild -> style::wrap_lines(&lines, cw): Vec<Line> - pieces keep `source_line`
7. rebuild -> finalize_layout() - expanded image rows copy `source_line`

No error path. Popped lines are handled by clamping `stamped`.

## Test seams

- `marks.rs` Mark (pure):
  - `capture` trims and caps at 120 chars on a char boundary.
  - `resolve`: `Unchanged`; `Moved` after inserting or deleting lines above; nearest match among duplicates, the line above on a tie; `NotFound` after the line is edited; an empty fingerprint is always `Unchanged`; CRLF behaves like LF.
- `marks.rs` MarkStore (`MarkStore::at(tempdir)`):
  - Round-trip with char keys and fingerprints.
  - Saving doc A keeps doc B.
  - Creates the parent dir.
  - A corrupt file loads empty, save returns `InvalidData`, and the file is left unchanged.
  - A store with no file saves Ok.
- `markdown.rs`: a fixture with heading, paragraph, list, fenced code and table asserts `source_line` for each; code rows are per-line; no line is left `None`.
- `style.rs`: `wrap_lines` copies `source_line` to every piece in both branches.
- `viewer.rs` (`make_state_with_lines` + temp store):
  - `source_line_at` and `offset_for_source_line`, including clamping.
  - `m a`, scroll, `' a` round-trip.
  - `m Esc` does not quit; `m ?` does not open help; `m A` sets nothing.
  - Unset mark toast; JSON toast; `M` toggles `mouse_captured`.
  - Editing `content` above a mark makes the jump land on the moved line and the store hold the new line.
- E2E (scripted tmux):
  - Mark at 120 cols, quit, reopen at 60 cols, jump, and assert the same text is at the top.
  - Insert lines near the top of the file, reopen, jump, and assert the same text again.

## Assumptions

1. The marked position is the top line of the viewport; a jump restores it to the top.
2. Granularity is per block for paragraphs, list items and tables, and per line in code blocks.
3. Letters are `a`-`z`, per file; `A`-`Z` are reserved and cancel like any other invalid key.
4. Setting an existing letter overwrites it silently.
5. After `m` or `'`, a non-`a`-`z` key cancels silently; Ctrl-C still quits.
6. A jump pushes onto the Backspace history; there is no `''`.
7. Marks are inactive in slide mode; JSON view shows a toast.
8. Marks are saved on every set, and when a jump re-anchors a mark.
9. Documents are identified by canonical path; moving or renaming a file loses its marks; symlinks resolve to the target.
10. stdin documents get marks for the session only.
11. Two instances saving marks for the same document: the last save wins for that document.
12. Entries for deleted files are never pruned.
13. Re-anchoring needs an exact match of the trimmed text. If the marked line is reworded, the jump falls back to the stored line with a toast. No fuzzy matching.
14. The search covers the whole file; the nearest match wins, and the line above wins a tie.
15. A `Moved` line is written back; a `NotFound` mark is left unchanged.
16. Re-anchoring runs only on jump. Blank-line marks have an empty fingerprint and never move.
17. There is no marks list overlay or delete-mark command.
18. The file stores the 0-based `source_line`.

## Decisions made during review

- Round 1: approach C (source-line anchor in a new `marks.rs`); mouse capture moves to `M`.
- Round 2: `A`-`Z` reserved, `a`-`z` only per file; add the fingerprint and re-anchor on jump now, instead of accepting drift.
