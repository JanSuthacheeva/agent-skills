# mdterm bookmarks - implementation plan

## Goal

Vim-style marks in the interactive viewer:

- `m` + `a-z` sets a mark at the current position.
- `'` + `a-z` jumps to it, recording the previous position so `Backspace` returns.
- Marks are per file, persist across sessions, and survive resizes, width/theme/line-number changes and small edits to the file.

## Current state (verified in code)

| Fact | Where |
|---|---|
| `m` toggles mouse capture; `M` is unbound | `src/viewer.rs:1647`, help entry `src/viewer.rs:3637` |
| No multi-key commands exist; every key in `handle_normal` acts on its own | `src/viewer.rs:1606` |
| `state.offset` is a wrapped-line index, so it changes meaning on resize, `-w`, theme and line-number toggles | `src/viewer.rs:294`, `rebuild` at `:485` |
| The renderer already sees source byte ranges for every event, but only task checkboxes keep them (`bracket_offset`) | `src/markdown.rs:1585`, `:1110`, `src/style.rs:42` |
| `wrap_lines` clones `Line` (including `meta`) onto every wrapped piece | `src/style.rs:89` |
| `nav_history: Vec<(file_idx, offset)>` + `Backspace` implement "go back" | `src/viewer.rs:365`, `:1765` |
| `config.rs` only reads `config.toml`; there is no state storage | `src/config.rs` |
| `dirs::state_dir()` is `Some` only on Linux (`$XDG_STATE_HOME` or `~/.local/state`); `None` on macOS and Windows | dirs 5 |
| Slide mode has its own key handler and status bar | `src/viewer.rs:1803`, `:2783` |
| README Controls does not list the mouse capture toggle at all | `README.md:68` |

## Decisions (agreed)

1. `m` = marks, mouse capture moves to `M`.
2. Anchor must survive small edits (approach chosen below).
3. Stored in the platform state directory, keyed by absolute path, saved immediately. Losing marks on rename/move is fine.
4. `a-z` per file only, no global `A-Z`.
5. Jumping pushes the old position onto `nav_history`; no `''`, no backtick alias.
6. Status bar shows the pending key; Esc / non-letter cancels; toasts for set / not set. No marks list in v1.
7. stdin: marks are kept for the current session only. Slide mode: jump goes to the slide containing the mark. JSON viewer: marks disabled with a toast. A mark past EOF clamps to the end.

## Anchor: line content plus a line-number hint

A mark stores two things: the 1-based source line number (`line`) and that line's trimmed text (`text`).

- **Capture:** take the source line of the top visible row. If that source line is blank, walk forward to the first non-blank source line.
- **Resolve** against the current file content:
  1. If line `line` still has text `text`, use it.
  2. Otherwise find every line whose trimmed text equals `text` and pick the one closest to `line` (earlier line wins a tie).
  3. Otherwise (the marked line itself was edited or deleted) fall back to `line`, clamped to the end of the file.

Why this over the alternatives:

| Option | Survives resize | Survives edits elsewhere | Survives edit to the marked line | Notes |
|---|---|---|---|---|
| Wrapped offset | no | no | no | Broken by any resize |
| Bare source line | yes | only below the mark | yes (same number) | Drifts by every line added/removed above |
| Heading + offset | yes | yes, except edits in the same section above the mark | yes | Useless in files without headings; two-level lookup; heading renames break it |
| **Content + line hint** | yes | yes | degrades to bare-line behaviour | Works with or without headings; one pure function, easy to test |

Known weak spot: low-information lines (`---`, a code fence, `}`) match many places. The "nearest to the hint" rule keeps the jump close, and the capture walks forward past blank lines so most anchors are real prose or code.

## Architecture

### New module `src/marks.rs`

Owns everything about marks that is not viewer UI: the anchor algorithm and persistence.

```rust
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Mark {
    pub line: usize,   // 1-based source line, used as a hint
    pub text: String,  // trimmed content of that line
}

impl Mark {
    /// First non-blank source line at or after `line` (0-based).
    pub fn capture(source: &str, line: usize) -> Option<Mark>;
    /// 0-based source line this mark points to in `source`.
    pub fn resolve(&self, source: &str) -> usize;
}

/// Marks for the file currently on screen.
pub struct FileMarks {
    key: Option<String>,          // canonical absolute path; None for stdin
    store: Option<PathBuf>,       // marks.toml path; None if no state dir
    marks: BTreeMap<char, Mark>,
}

impl FileMarks {
    pub fn for_file(path: Option<&Path>) -> Self;   // loads from disk
    pub fn session_only() -> Self;                  // stdin
    pub fn get(&self, letter: char) -> Option<&Mark>;
    /// Always updates memory; persists when the file has a key.
    pub fn set(&mut self, letter: char, mark: Mark) -> io::Result<()>;
}
```

`for_file` and `set` take the store path through an internal constructor (`with_store(store, key)`) so tests can point at a temp directory.

**Store location:** `state_dir()/mdterm/marks.toml`, where `state_dir()` is `dirs::state_dir()`, falling back to `~/.local/state` when that returns `None` (macOS, Windows).

**File format** (human-readable, editable):

```toml
["/Users/jan/notes/rust.md"]
a = { line = 42, text = "## Ownership and borrowing" }
t = { line = 118, text = "fn main() {" }
```

Deserialized as `BTreeMap<String, BTreeMap<String, Mark>>`. Entries whose key is not a single `a-z` letter are ignored on load.

**Save (on every `set`):** re-read `marks.toml`, replace this file's entry, write to `marks.toml.tmp-<pid>`, `rename` over the original. Re-reading first means two mdterm sessions on different files don't overwrite each other's marks. Creates the directory if missing.

**Corrupt store:** if `marks.toml` exists but does not parse, `for_file` starts with no marks and `set` refuses to write (returns an error) so we never destroy data the user may want to fix by hand. The mark still works for the session; the toast says it was not saved.

### Source line numbers on rendered lines (`style.rs`, `markdown.rs`)

- `Line` gains `pub source_line: Option<usize>` (0-based). JSON and diagram lines leave it `None`.
- `wrap_lines` / `word_wrap` copy it onto every wrapped piece, the same way `meta` is carried today.
- `Renderer` gets:
  - `line_starts: Vec<usize>`: byte offsets of each source line, computed once; `line_of(byte)` via `partition_point`.
  - `block_line: Option<usize>`: set from `range.start` on every block-level `Start` event (paragraph, heading, list item, block quote, table row, code block, math block, rule, HTML block).
  - `push_line(&mut self, line: Line)`: stamps `block_line` when the line has none, then pushes. All `self.lines.push(...)` sites in `markdown.rs` go through it.
  - `emit_code_block` stamps each content row with `fence_line + 1 + i` (fenced) or `start_line + i` (indented), so marks inside long code blocks are precise. Border rows get the fence line.
- Existing `Line { spans, meta }` literals (about 40 across `markdown.rs` / `json.rs`) gain `..Default::default()` or go through a `Line::new(spans, meta)` constructor. `Line` already derives `Default`.

### Viewer (`viewer.rs`)

New state:

```rust
#[derive(Copy, Clone, PartialEq, Debug)]
enum PendingKey { SetMark, JumpMark }

// ViewerState
pending_key: Option<PendingKey>,
marks: crate::marks::FileMarks,
```

Key flow in `handle_event`, right after the Ctrl+C check and before the help toggle (so `m` then `h` sets mark `h` instead of opening help):

1. If `pending_key.take()` is `Some(p)`: if the key is `a-z` without Ctrl/Alt, run `set_mark` or `jump_to_mark`; otherwise cancel silently. Mark dirty, return.
2. In `ViewMode::Normal`, `m` / `'` (no Ctrl/Alt) start a pending key. This is checked before dispatching to `handle_normal`, so it covers both normal and slide mode in one place. If `json_view.is_some()`, toast "Marks are not available in JSON view" instead.
3. `M` replaces `m` as the mouse capture toggle in `handle_normal`.

`set_mark(letter)`:
- Top row: `slide_boundaries[current_slide]` in slide mode, else `offset`.
- `source_line_at(row)`: first wrapped line at or after `row` with `Some(source_line)`.
- `Mark::capture(&content, src)`, then `marks.set(letter, mark)`.
- Toast: `Mark a set`, or `Mark a set (not saved: <reason>)` on I/O error.

`jump_to_mark(letter)`:
- Missing: toast `Mark a not set`.
- `mark.resolve(&content)` gives a source line; target row = first wrapped line whose `source_line >= target`, else the last line.
- Normal mode: push `(current_file_idx, offset)` onto `nav_history`, then `offset = row.min(max_offset())`. Silent on success, like `[` / `]`.
- Slide mode: `current_slide` = last boundary `<= row`. No history push (Backspace is not bound in slide mode).

Loading:
- `ViewerState::new`: `FileMarks::for_file(Some(path))` when `files` is non-empty, `FileMarks::session_only()` for stdin.
- `switch_file`: reload marks for the new path (covers Tab, Shift+Tab, link following and Backspace).
- File reload on disk change: nothing to do; marks resolve lazily against the current content at jump time.

Status bar: when `pending_key` is set, `render_status_bar` draws a prompt bar in the style of the search prompt (`search_prompt` colour) before the slide-mode early return:

```
╰─ m_  a-z set mark · Esc cancel ───────────────────╯
╰─ '_  a-z jump to mark · Esc cancel ───────────────╯
```

### Docs

- Help overlay (`help_sections`): Navigation gets `m a-z` "Set mark", `' a-z` "Jump to mark"; Actions changes `m` to `M` for mouse capture. The existing `help_sections_no_duplicate_keys` test guards collisions.
- README Controls: new "Marks" table; add the missing `M` mouse-capture row to Features.
- CLAUDE.md: eleven source files, add `marks.rs`.

## Data flow

```
set:   offset -> wrapped[row].source_line -> Mark::capture(content) -> FileMarks.set -> marks.toml
jump:  marks.toml -> FileMarks.get -> Mark::resolve(content) -> source line -> wrapped row -> offset
```

## Edge cases

| Case | Behaviour |
|---|---|
| stdin | Session-only marks; nothing written |
| JSON file | `m` / `'` toast "Marks are not available in JSON view" |
| Mark past EOF after file shrank | Clamp to last line |
| Marked line edited | Falls back to the stored line number |
| Identical lines (`---`, fences) | Nearest to the stored line wins |
| Top row is a blank spacer / has no source line | Walk forward to the next line with a source line |
| No state dir and no home dir | `store = None`; marks are session-only, `set` reports "not saved" |
| Corrupt `marks.toml` | Never overwritten; marks session-only with a toast |
| Two sessions, same file, setting marks concurrently | Last write wins for that file's entry (accepted) |
| Ctrl+C while pending | Still quits (checked first) |
| Resize / theme / line numbers while pending | Pending key stays; next key completes or cancels |

## Testing

- `marks.rs` unit tests: capture skips blank lines; resolve exact hit; resolve after lines inserted/removed above; resolve when the marked line was edited (fallback); nearest-duplicate tie-break; clamp past EOF; store round-trip in a temp dir; invalid letters ignored on load; corrupt store not overwritten; marks of other files preserved on save.
- `markdown.rs` tests: `source_line` for heading, paragraph, list items, table rows, each code-block content row; preserved by `wrap_lines`.
- `viewer.rs` tests (using `make_state_with_lines`): `m` then `a` sets; `m` then Esc cancels; `m` then `h` sets `h` and does not open help; `'` on an unset letter toasts; jump pushes `nav_history`; slide-mode jump selects the right slide; JSON view refuses.
- E2E in tmux: open a long file, `ma`, scroll away, `'a`; resize the pane and repeat; quit, insert lines above the mark in an editor, relaunch, `'a` lands on the same text; Backspace returns. Check `marks.toml` contents.
- `cargo fmt`, `cargo clippy`, `cargo test` clean.

## Build sequence (one commit each)

1. `feat(render): track source line numbers on rendered lines` - `Line.source_line`, renderer stamping, wrap propagation, tests.
2. `feat(marks): add mark anchoring and persistent store` - `src/marks.rs` + tests.
3. `refactor(viewer): move mouse capture toggle to M` - key, help, README.
4. `feat(viewer): add m/' bookmarks` - pending key, set/jump, status bar, help, README, CLAUDE.md, tests.

## Risks

- Stamping accuracy depends on every `lines.push` going through `push_line`; a missed site shows up as `None` and falls through to the next stamped line (degrades gracefully, covered by tests).
- `marks.toml` grows by one entry per marked file and is never pruned. Fine at human scale; pruning entries for missing files can come later.

## State directory on macOS / Windows (decided)

`dirs::state_dir()` returns `None` there, so marks fall back to `~/.local/state/mdterm/marks.toml`. Accepted consequence: on macOS `config.toml` stays under `~/Library/Application Support/mdterm/` (`dirs::config_dir()`), so config and marks live in different trees.

## Status

Plan approved. Not being implemented in this conversation.
