# mdterm bookmarks (vim-style marks) - implementation plan

## Goal

- `m` + `a-z` sets a mark at the current position.
- `'` + `a-z` jumps to that mark. `''` jumps to the position before the last jump.
- Marks persist per file between sessions and survive resize, line-number toggling, image loading and external edits.

## Decisions (confirmed)

| # | Decision |
|---|----------|
| 1 | Mouse capture toggle moves from `m` to `M`. `m` becomes the mark prefix. |
| 2 | A mark stores its source line text so it can relocate after external edits. |
| 3 | Only `a-z`, per file. Uppercase letters (and anything else) do not set marks. |
| 4 | `''` jumps to the previous position using `nav_history`. Backspace keeps working. |
| 5 | Feedback via toasts only. No marks list overlay, no gutter indicator. |
| 6 | stdin: session-only marks with a toast. JSON view: marks disabled with a toast. Slide mode: marks work and jump to the containing slide. |
| 7 | `'x` on an unset mark toasts "Mark x not set". Re-setting a letter overwrites silently with a "Mark x set" toast. |
| 8 | Marks of files that no longer exist are pruned on load. |

## Current state (verified)

- `m` toggles mouse capture: `src/viewer.rs:1647`, help entry `src/viewer.rs:3637`, README Controls.
- `state.offset` is an index into `wrapped` (post-wrap lines). It changes with width, `l`, `width_override`, image row expansion in `finalize_layout` (`src/viewer.rs:605`) and file edits. It cannot be persisted.
- The markdown renderer receives source byte ranges (`parser.into_offset_iter()`, `src/markdown.rs:1585`) but `Line` (`src/style.rs:56`) only holds `spans` and `meta`.
- `nav_history: Vec<(usize, usize)>` (file index, offset) is pushed on link follow (`src/viewer.rs:1966`) and popped by Backspace (`src/viewer.rs:1765`).
- Key routing: `handle_event` (Ctrl-C, help toggle, Help mode) then `handle_normal`, which dispatches to `handle_slide_keys` / `handle_json_keys` first.
- No persisted state exists today. `config.rs` only reads `config.toml`. `serde`, `serde_json` and `dirs` are already dependencies.

## Architecture

```
markdown source --(into_offset_iter)--> Renderer tags Line.source
        --> wrap_lines copies source --> finalize_layout copies source to image rows
        --> ViewerState.wrapped

m{a-z}:  wrapped + position + source text --capture--> Mark --MarkStore.set--> marks.json (atomic)
'{a-z}:  MarkStore.get --> Mark --resolve(wrapped, source text)--> wrapped index --> jump_to_line
```

### 1. Source line tracking (`style.rs`, `markdown.rs`, `json.rs`, `viewer.rs`)

- Add `pub source: Option<usize>` (0-based source line) to `Line`. `Line::empty()` and all JSON-rendered lines use `None`.
- `wrap_lines` / `word_wrap` (including the blockquote path) copy `source` from the parent line to every wrapped piece.
- `finalize_layout` copies `source` from the image placeholder to every expanded image row.
- Tagging in `render_with` is centralised: before each `renderer.process(event, range)` remember `lines.len()`, afterwards set `source = line_of(range.start)` on every new line that is still `None`. `line_of` binary-searches a precomputed line-start table.
- Refinement for code blocks: content lines get `line_of(code_text_start) + i` so marks inside long code blocks are exact. Set inside the code block renderer, so the central pass leaves them untouched.
- Tables and multi-line source paragraphs map to their block start. Precision within them comes from the mark's `row` (see below).
- Choosing this over a parallel `Vec<usize>` source map: a field travels through wrapping, image expansion and clones automatically. A parallel vec would have to be kept in sync by every transform. Cost: about 50 mechanical `Line { .. }` literal updates.

### 2. New module `src/marks.rs`

```rust
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Mark {
    pub line: usize,   // 0-based source line
    pub row: usize,    // wrapped rows below the first row of that source line
    pub text: String,  // source line text, trailing whitespace trimmed
}

pub fn capture(wrapped: &[Line], pos: usize, source: &str) -> Option<Mark>;
pub fn resolve(mark: &Mark, wrapped: &[Line], source: &str) -> Option<usize>;

pub struct MarkStore { /* path, persisted files, session marks, warning */ }

impl MarkStore {
    pub fn load() -> Self;                         // default location
    pub fn load_from(path: Option<PathBuf>) -> Self; // tests, None = in-memory only
    pub fn get(&self, file: Option<&Path>, letter: char) -> Option<&Mark>;
    pub fn set(&mut self, file: Option<&Path>, letter: char, mark: Mark) -> io::Result<()>;
    pub fn take_warning(&mut self) -> Option<String>;
}
```

`capture`:
1. From `pos`, find the first wrapped line with `Some(source)` (search backward if none follows).
2. `row` = distance from the first wrapped line sharing that source line.
3. `text` = that source line, `trim_end`.

`resolve`:
1. Target line: `mark.line` if its text still equals `mark.text`. Otherwise the nearest line (by distance, ties go up) whose text equals `mark.text`. Blank texts are not distinctive, so they skip relocation. Fallback: `mark.line` clamped to the last line.
2. Index = first wrapped line with `source >= target`. Add `row` only if that line's source equals `target`, clamped to the rows of that source line.
3. Caller clamps to `max_offset`.

So with unchanged width the jump is exact. After a resize it lands on the same source line. After an edit it follows the text.

#### Storage

- Location: `dirs::state_dir()` (Linux `$XDG_STATE_HOME`, `~/.local/state`) falling back to `dirs::data_dir()` (macOS `~/Library/Application Support`), then `mdterm/marks.json`. Not `config.toml`: that file is user-authored.
- Format:

```json
{
  "version": 1,
  "files": {
    "/Users/jan/notes/rust.md": {
      "a": { "line": 41, "row": 0, "text": "## Ownership" },
      "t": { "line": 210, "row": 3, "text": "| Trait | Purpose |" }
    }
  }
}
```

- Keys: `fs::canonicalize(path)` (falls back to the absolute path), so symlinks and relative paths share marks. `BTreeMap` for stable diffs.
- Load: missing file means empty. Entries whose path no longer exists are pruned. Unparseable file: rename to `marks.json.bak`, start empty, and set a warning that the viewer toasts on startup.
- `set` for a real file: re-read from disk (merges marks set by other running instances), apply the letter, prune, write to a temp file in the same directory, then `rename`. On error the mark is kept in memory and the toast says it was not saved.
- `set` with `file = None` (stdin): session map only, never written.

### 3. Viewer integration (`viewer.rs`, `main.rs`)

- `ViewerOptions` gains `marks: MarkStore`. `main.rs` builds it with `MarkStore::load()`. Tests inject `load_from(tempdir)` so they never touch the real state dir.
- `ViewerState` gains `marks: MarkStore` and `pending_mark: Option<MarkAction>` where `enum MarkAction { Set, Jump }`.
- `handle_normal`: `m` / `'` (no Ctrl/Alt) are matched before slide and JSON dispatch. JSON view (`json_view.is_some()`): toast "Marks are not available for JSON". Otherwise set `pending_mark`.
- `handle_event`: right after the Ctrl-C check and before `is_help_toggle`, if `pending_mark.take()` is `Some`, route the key to `handle_mark_key` and return. This ordering matters: `m` `h` must set mark `h`, not open help.
- `handle_mark_key`:
  - `a-z`: Set or Jump.
  - `'` while Jump: previous position.
  - Other characters (uppercase, digits): toast "Marks use letters a-z".
  - Non-character keys (Esc, arrows): cancel silently.
- New helpers on `ViewerState`:
  - `position()`: slide mode uses `slide_boundaries[current_slide]`, otherwise `offset`.
  - `jump_to_line(idx)`: slide mode sets `current_slide` to the slide containing `idx`, otherwise `offset = idx.min(max_offset)`.
  - `mark_file()`: canonical path of `files[current_file_idx]`, `None` for stdin.
  - `go_back(record_current: bool)`: shared by Backspace (`false`) and `''` (`true`, so repeated `''` toggles between two spots).
- Set: `capture` then `marks.set`. Toasts: "Mark a set", "Mark a set (stdin: this session only)", "Mark a set (not saved: <err>)".
- Jump: `get`, else toast "Mark a not set". `resolve`, then push `(current_file_idx, position())` to `nav_history` if the target differs, then `jump_to_line`.
- `''` with empty history: toast "No previous position".
- Status bar while pending: normal and slide hints become `mark: a-z  Esc cancel` or `jump: a-z  ' previous  Esc cancel`.
- Startup: toast `marks.take_warning()` if present.
- Mouse toggle: `KeyCode::Char('m')` becomes `KeyCode::Char('M')`.

### 4. Help and docs

- Help: new "Marks" section with `m a-z` Set mark, `' a-z` Jump to mark, `''` Jump to previous position. Actions: `M` Toggle mouse capture. Backspace text becomes "Go back (after a link or mark jump)".
- README: Marks table under Controls, `M` under Features, marks file location under Configuration.
- CLAUDE.md: eleven source files, `marks.rs` bullet, data-flow note about `Line.source`.

## Tests

- `style.rs`: wrapping (plain and blockquote) preserves `source` on every piece.
- `markdown.rs`: headings, paragraphs, list items, code block content lines (exact), tables (block start).
- `marks.rs`:
  - capture and resolve round trip at widths 40 and 120
  - `row` exactness
  - text moved by inserted lines relocates
  - deleted text falls back to the line
  - blank lines don't relocate
  - store round trip with char keys
  - prune missing files
  - two stores setting different letters both persist
  - corrupt file moved to `.bak` with a warning
  - stdin marks are never written
- `viewer.rs`:
  - `m` `h` sets mark h and does not open help
  - `'` `a` jumps and pushes history
  - `''` toggles
  - uppercase is rejected
  - JSON toast
  - `M` toggles mouse
  - help has no duplicate keys
- Dev-dependency: `tempfile = "3"`.
- E2E in tmux:
  1. `cargo run -- test.md`, mark, scroll, jump, quit, relaunch and jump again.
  2. Resize, toggle `l`, then jump.
  3. Insert lines above the mark from another shell (auto-reload), then jump.
  4. Slide mode.
  5. stdin input.

## Commit sequence

1. `feat(viewer): move mouse capture toggle to M`
2. `feat(render): track source line on rendered lines`
3. `feat(marks): add persistent mark store with capture/resolve`
4. `feat(viewer): set and jump to marks with m and '`
5. `docs: document marks in help, README and CLAUDE.md`

## Risks

- **Precision inside tables and long soft-wrapped paragraphs** after a resize: the jump lands on the block start, not the exact row. With unchanged width it is exact.
- **Concurrent instances**: there's no file lock. Each write re-reads the file first and the race window is tiny, so the worst case is losing one mark that two instances set at the same moment.
- **Duplicate line text** (for example two identical table rows): relocation picks the nearest one, so after an edit a mark can land on a sibling row.
- **Line literal churn** in `json.rs`, `markdown.rs`, `style.rs` and `viewer.rs`: mechanical, and the compiler catches every site.
- **Behaviour change**: users with `m` in muscle memory for mouse capture now set a pending mark. The next key either sets a mark or cancels, so nothing breaks, but the README and help call out the move to `M`.
