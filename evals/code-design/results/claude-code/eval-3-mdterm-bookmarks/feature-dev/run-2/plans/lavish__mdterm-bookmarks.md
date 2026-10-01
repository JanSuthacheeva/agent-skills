# mdterm bookmarks - implementation plan

Status: approved. Option B (trimmed), including reload re-anchoring (step 13) and resize-stable `rebuild` (step 15), no file lock. No code written yet.

## Goal

Vim-style marks in the interactive viewer:

- `m` + `a-z` sets a mark at the current top-of-screen position.
- `'` + `a-z` jumps to it. `''` jumps back to where the last jump started.
- Marks persist per file between sessions.

## Confirmed decisions

| Topic | Decision |
|---|---|
| Key conflict | Mouse capture toggle moves from `m` to `M` (help + README updated; README currently lacks the entry entirely) |
| Anchor | Source line in the markdown file, not wrapped-line index |
| Position | Top line of the viewport; jump restores it as top line |
| Letters | `a-z` only, per file. No uppercase marks |
| History | Jumps push onto `nav_history` so `Backspace` returns; `''` swaps to pre-jump position |
| Feedback | Toast on set/jump, mark letter in the left margin. Mark list deferred |
| Storage | JSON at `dirs::state_dir()/mdterm/marks.json`, fallback `dirs::data_dir()` (macOS: `~/Library/Application Support/mdterm/marks.json`). Never in `config.toml`. Entries for missing files pruned |
| stdin | Session-only marks, not persisted |
| Slide mode, JSON viewer | Marks disabled |
| Unset mark | Toast `Mark 'x' not set` |
| Deleted line | Clamp to nearest valid line |
| Approach | Option B trimmed (see Options) |
| Scope | Includes live-reload re-anchoring and resize-stable `rebuild` |
| Locking | No `flock`; delta-update + atomic rename only |

## Current state (verified in code)

- `m` toggles mouse capture: `src/viewer.rs:1647`, help entry `src/viewer.rs:3637`.
- No chord support: `handle_normal` (`src/viewer.rs:1606`) is a single-key match. `is_help_toggle` runs first in `handle_event` (`src/viewer.rs:999`), so `m` then `h` would open help unless a pending prefix is intercepted before it.
- `state.offset` (`src/viewer.rs:294`) is a wrapped-line index. It drifts on resize (`rebuild`, `src/viewer.rs:485`), image row expansion (`finalize_layout`, `src/viewer.rs:605`) and live reload (`src/viewer.rs:773`).
- The renderer already iterates `parser.into_offset_iter()` (`src/markdown.rs:1585`) but drops the byte ranges.
- `Line` (`src/style.rs:55`) derives `Default`, so adding a field is a mechanical `..Default::default()` change at ~50 literal sites (markdown.rs, json.rs, style.rs, viewer.rs).
- Left margin is `Print("│ ")` (`src/viewer.rs:2528`), `GUTTER_COLS = 2` (`src/viewer.rs:935`). Column 1 is free for the mark letter.
- `nav_history: Vec<(usize, usize)>` (`src/viewer.rs:365`), pushed in `dispatch_link` (`src/viewer.rs:1966`), popped by Backspace (`src/viewer.rs:1765`). Its offsets drift on resize too.
- mdterm never writes app state today; `config.rs` is read-only TOML.

## Options

### A. Minimal: parallel side tables (rejected)

- `markdown::render_with_src` returns `Vec<usize>` source lines next to `lines`, computed by watching `renderer.lines.len()` around each `process` call.
- `style::wrap_lines_with_origin` returns a pre-wrap index per wrapped row; `ViewerState.line_src` is the composition, kept in sync by hand in `finalize_layout`.
- `src/marks.rs` holds store + format; viewer glue (~110 lines) added inline to `viewer.rs`.
- Save = read-merge-write of this file's whole entry + atomic rename.
- Cost: ~200 prod lines, 5 files. `Line` untouched.
- Weakness: three parallel arrays that must stay index-aligned through every layout mutation; desync is silent. Grows the 4356-line `viewer.rs` further. Reload does not re-anchor marks.

### B. Clean: source position on `Line`, layered modules (chosen, trimmed)

- `Line.src: Option<SourceLine>` stamped by the renderer, copied through `wrap_lines` and image expansion. No parallel arrays.
- Pure domain modules, IO isolated, viewer glue in a child module.
- Live reload re-anchors marks via a prefix/suffix line diff.
- `nav_history` becomes source-anchored so `Backspace` is resize-safe too.
- Cost: ~4 new modules, ~50 mechanical literal edits, ~15 small commits.

Trims applied to the architect's full version (to keep it simple):

- No `flock` advisory lock (would add `unsafe` libc FFI). Delta-update (re-read, apply one mutation, atomic rename) already preserves other instances' marks except in a microsecond race.
- No `serde(flatten)` unknown-field preservation. A `version` field is enough.
- `''` jump-back position is session-only, never persisted.

## Design (B, trimmed)

### Module layout

| File | Kind | Responsibility |
|---|---|---|
| `src/source_map.rs` (new) | pure | `SourceLine = u32`, `LineStarts` (byte offset -> line), `SourceIndex` (wrapped row <-> source line) |
| `src/marks.rs` (new) | pure | `MarkName` (a-z only), `MarkSet`, `Prefix`, `KeyOutcome`, `interpret()`, `LineRemap` |
| `src/marks_store.rs` (new) | IO | `MarksStore`: load, prune, delta `update`, atomic write, path resolution |
| `src/viewer/marks_ctl.rs` (new) | glue | `MarkSession` + `impl ViewerState` methods for set/jump/render helpers |
| `src/style.rs` | edit | `Line.src` field; `wrap_lines` copies it to every wrapped row |
| `src/markdown.rs` | edit | Stamp `src` on every pushed line via one `push_line` choke point |
| `src/json.rs` | edit | Mechanical `..Default::default()` only |
| `src/viewer.rs` | edit | ~30 lines of call sites, `M` rebind, margin, status bar, help, `NavEntry` |
| `src/theme.rs` | edit | New `mark` color in dark + light themes |
| `src/main.rs` | edit | `mod` declarations; pass store into `ViewerOptions` |
| `README.md`, `CLAUDE.md` | edit | Controls table (incl. missing `M` row), bookmarks note, source file list |

### Key types

```rust
// source_map.rs
pub type SourceLine = u32;
pub struct LineStarts { starts: Vec<usize> }
impl LineStarts {
    pub fn new(source: &str) -> Self;
    pub fn line_of(&self, byte: usize) -> SourceLine;
}
pub struct SourceIndex { entries: Vec<(SourceLine, usize)> } // sorted, first row per line
impl SourceIndex {
    pub fn build(lines: &[Line]) -> Self;
    pub fn resolve(&self, line: SourceLine) -> Option<usize>; // first row with src >= line, else last row
    pub fn source_at(lines: &[Line], row: usize) -> Option<SourceLine>;
}

// marks.rs
pub struct MarkName(char);                    // TryFrom<char>, 'a'..='z' only
pub struct MarkSet { marks: BTreeMap<MarkName, SourceLine> }
pub enum Prefix { Set, Jump }
pub enum KeyOutcome { Arm(Prefix), Set(MarkName), Jump(MarkName), JumpBack, Cancel, Ignored }
pub fn interpret(pending: Option<Prefix>, key: Option<char>) -> KeyOutcome;
pub struct LineRemap { /* common prefix/suffix */ }
impl LineRemap {
    pub fn between(old: &str, new: &str) -> Self;
    pub fn map(&self, line: SourceLine) -> SourceLine;
}

// marks_store.rs
pub struct MarksStore { path: PathBuf }
impl MarksStore {
    pub fn new(path: PathBuf) -> Self;               // injectable for tests
    pub fn at_default_location() -> Option<Self>;    // MDTERM_MARKS_PATH, else state_dir, else data_dir
    pub fn load(&self, doc: &Path) -> Result<MarkSet, StoreError>;
    pub fn update(&self, doc: &Path, f: impl FnOnce(&mut MarkSet)) -> Result<(), StoreError>;
}

// viewer/marks_ctl.rs
pub(super) struct MarkSession {
    store: Option<MarksStore>,
    sets: HashMap<DocKey, MarkSet>,   // DocKey::File(PathBuf) | DocKey::Ephemeral (stdin)
    active: DocKey,
    pending: Option<Prefix>,
    last_jump: HashMap<DocKey, SourceLine>, // session-only, for ''
    rows: HashMap<usize, MarkName>,   // margin cache, rebuilt in finalize_layout
}
```

### Source line tracking

1. `Renderer` holds `LineStarts`; `process()` records `line_of(range.start)`.
2. Lines are stamped from the source line of their first span, not at flush time. Reason: a nested `Start(List)` flushes the parent item while the current range already points at the child.
3. Blank separator rows take the line after the block, so a mark on a gap resolves forward.
4. Code blocks are line-exact: fence -> top border, code row `i` -> `fence + 1 + i`. Mermaid rows take the block start.
5. `wrap_lines` copies `src` to all wrapped rows (blockquote and general paths, `src/style.rs:120-141`).
6. `finalize_layout` copies `src` onto every expanded image row, then builds `SourceIndex` and refreshes the margin cache. `rebuild()` ends in `finalize_layout`, so resize, theme toggle, image arrival and reload all stay correct.
7. Granularity: a paragraph or table maps to its first source line. A mark set mid-paragraph jumps to the paragraph start.

### Key handling

- In `handle_event`, before `is_help_toggle`: if mode is Normal and a prefix is pending, route the key to `try_mark_key`, set `dirty`, return. This keeps `mh` / `'h` working and stops Esc from quitting while pending.
- `interpret` truth table:
  - nothing pending: `m` -> `Arm(Set)`, `'` -> `Arm(Jump)`, else `Ignored`
  - `Set` pending: `a-z` -> `Set`, else `Cancel`
  - `Jump` pending: `a-z` -> `Jump`, `'` -> `JumpBack`, else `Cancel`
  - Ctrl/Alt/non-char keys arrive as `None`
- Gated by `marks_enabled()` = `!slide_mode && json_view.is_none()`.
- Pending cleared on mouse click and mode change.
- Status bar shows `m-` / `'-` in both the normal bar and the search-results bar.

### Set / jump flow

- Set `ma`: `src = source_at(offset)`, update in-memory set, `store.update(key, |s| s.set(a, src))`, refresh margin, toast `Mark a set`. Store failure keeps the mark in memory and toasts `Mark a set (not saved)` once.
- Jump `'a`: missing -> toast `Mark 'a' not set`. Else record `last_jump = source_at(offset)`, push `NavEntry`, `offset = resolve(line).min(max_offset)`, toast `Jumped to mark a`.
- `''`: swap with `last_jump`, also pushes `NavEntry`. None -> toast `No previous position`.

### Persistence

```json
{ "version": 1,
  "files": { "/abs/path/doc.md": { "marks": { "a": { "line": 12 }, "q": { "line": 340 } } } } }
```

- Key: `fs::canonicalize(path)`. Lines 0-based.
- Mark values are objects so a future text snippet for offline-edit relocation fits without a version bump.
- Write: `create_dir_all`, write `marks.json.tmp.<pid>`, `sync_all`, `rename`.
- `update` re-reads disk and applies a single mutation, so concurrent instances do not clobber each other's marks.
- `load` prunes missing files in memory only (`NotFound` only, so unmounted shares keep their marks); disk cleaned on next `update`. Read-only sessions never write.
- Corrupt JSON: load empty; on next write move the bad file to `marks.json.corrupt`.
- Newer `version`: session-only, one-time toast, never overwrite.

### Live reload

`poll_file_changes` computes `LineRemap::between(old, new)` before replacing `content`, applies it to the in-memory set and persists it. Marks above an edit stay, below shift by the delta, inside a deleted region clamp to its start.

### Navigation history

`nav_history: Vec<NavEntry { file_idx, src: Option<SourceLine>, offset }>`. Restore prefers `src` via `SourceIndex`, falls back to `offset`. Fixes the pre-existing resize drift on `Backspace`.

### Rendering

- Margin: `Print("│")` then the mark letter in `theme.mark` or a space. Lowest letter wins when two marks share a row.
- Help: `Navigation` section gets `m{a-z}` Set mark, `'{a-z}` Jump to mark, `''` Jump back. `Actions` entry becomes `M`. Must pass `help_sections_no_duplicate_keys`.

## Build sequence (one commit each)

1. Rebind mouse capture `m` -> `M`; help text; add missing README row.
2. `source_map.rs`: `SourceLine`, `LineStarts` + tests.
3. Add `Line.src` field; mechanical `..Default::default()` across literals. No behavior change.
4. `wrap_lines` propagates `src` + tests.
5. Renderer stamping via `push_line`, first-span rule, blank-row rule + tests (incl. non-decreasing property over a mixed doc).
6. Code-block line precision (fenced, indented) and mermaid rows + tests.
7. `finalize_layout` stamps image rows; `SourceIndex` built and held on `ViewerState` + tests.
8. `marks.rs`: `MarkName`, `MarkSet`, `interpret`, `LineRemap` + tests.
9. `marks_store.rs` + tests (tempdir helper); wire through `ViewerOptions` and `main.rs`; tests pass `None`.
10. `NavEntry` refactor for `dispatch_link` and `Backspace`.
11. `viewer/marks_ctl.rs`: `MarkSession`, pending guard, `switch_file` + `new` wiring, toasts, help entries + glue tests.
12. Rendering: `theme.mark`, margin glyph, pending label in status bars.
13. Live reload remap in `poll_file_changes`.
14. Docs: README controls + bookmarks note; CLAUDE.md module list.
15. Anchor `rebuild()` itself on `SourceIndex` so plain resize keeps the top source line (fixes pre-existing drift).

## Testing

- Unit tests in existing `#[cfg(test)] mod tests` style per module: `LineStarts`, `SourceIndex::resolve`, renderer fixtures per block type, `interpret` truth table, `LineRemap` cases, store round-trip / prune / corrupt / version / two-handle interleave, viewer glue (`mh` sets mark not help, Esc cancels not quits, `''` toggles, Backspace after jump, width change, per-file isolation after `switch_file`).
- E2E: tmux-driven run with `MDTERM_MARKS_PATH` at a temp file. Scroll, `ma`, resize pane, `'a`, assert top line; edit file externally, assert mark shifted; restart, assert persistence; stdin run writes nothing.
- `cargo fmt`, `cargo clippy`, `cargo test` clean.

## Risks

- Paragraph granularity: mid-paragraph marks snap to paragraph start. Accepted.
- Offline edits (file changed while mdterm closed) can only be clamped, not re-anchored. Object format leaves room for a text-snippet relocator later.
- `m` muscle memory for mouse capture breaks. Called out in README.
- Canonical path keys: moved or symlinked files lose marks. Matches vim.
- pulldown-cmark 0.11 `End` event ranges: design relies only on `Start`/leaf starts and `End.range.end`; verified by test in step 5.
- Race between two instances without a lock: atomic rename means the worst case is one lost update, never corruption.
