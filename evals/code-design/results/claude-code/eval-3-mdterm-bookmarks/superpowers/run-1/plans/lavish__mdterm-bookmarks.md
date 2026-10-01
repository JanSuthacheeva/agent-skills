# mdterm bookmarks - design spec

Date: 2026-10-01
Status: approved 2026-10-01 (warning toasts kept)

## 1. Goal

Let a reader drop vim-style marks in a long Markdown document and come back to them later, including in a future session.

- `m{a-z}` sets mark `{letter}` at the current position.
- `'{a-z}` jumps to mark `{letter}`.
- Marks are saved per file and persist between sessions.
- A mark must keep pointing at the same content after the file is edited (including external edits picked up by auto-reload), after a terminal resize, and after toggling line numbers.

### Decisions already made

| Topic | Decision |
|---|---|
| `m` conflict | `m` becomes the mark prefix. Mouse capture moves to `M`. |
| Mark scope | Lowercase `a-z` only, local to each file. No global `A-Z` marks. |
| "Current position" | The top line of the viewport, same as `offset` and `nav_history`. |
| Edit robustness | Source line + text snippet, re-located nearest-first on jump (healing). |
| Back navigation | A jump pushes onto the existing `nav_history`, so `Backspace` returns. |
| Feedback | Toasts only. No gutter or status-bar indicator. |
| Mark list overlay | Out of scope. |
| Deleting marks | Out of scope (overwrite only). |
| Slide mode, JSON viewer, stdin | Marks disabled, with an explanatory toast. |
| Storage | Separate from `config.toml`, in the platform state dir. |

### Non-goals (v1)

Global marks, a mark list, deleting marks, a gutter indicator, marks in slide mode or the JSON viewer, pruning entries for deleted files.

## 2. Current state (verified in code)

- `m` toggles mouse capture: `src/viewer.rs:1647`, help entry at `src/viewer.rs:3637`. `M` and `'` are unbound.
- `state.offset` is an index into `state.wrapped` (wrapped visual rows). It changes meaning on resize, line-number toggle (`l`), image row expansion (`finalize_layout`), and any file edit, so it cannot be persisted.
- `Line` (`src/style.rs`) has `spans` and `meta` only. No source position is carried through rendering, although `render_with` already iterates `parser.into_offset_iter()` (`src/markdown.rs:1585`) and passes byte ranges to `Renderer::process`.
- `handle_event` checks `is_help_toggle` (`src/viewer.rs:999`) before dispatching to `handle_normal`, so `h` and `?` are intercepted before `handle_normal` runs.
- `handle_normal` returns early for slide mode and interactive JSON before reaching the general key match (`src/viewer.rs:1610-1617`).
- `nav_history: Vec<(usize, usize)>` stores `(file_idx, offset)`. `Backspace` pops it (`src/viewer.rs:1765`).
- The toast renderer always prefixes `✓` (`src/viewer.rs:3023`), including for failure messages such as "Invalid JSON - showing as plain text".
- `Config` (`src/config.rs`) is user-edited TOML. `serde_json` and `dirs` are already dependencies. There are no dev-dependencies.
- README key table (`README.md:74-110`) does not list the mouse capture key at all.

## 3. Architecture

```
markdown text
  -> pulldown-cmark (event, byte range)
  -> Renderer                       stamps Line.source_line
  -> wrap_lines                     copies source_line to every row
  -> finalize_layout                copies source_line to expanded image rows
  -> ViewerState.wrapped

m{c}:  wrapped[offset].source_line -> Anchor::capture -> MarkStore::set -> marks.json
'{c}:  MarkStore::get -> Anchor::resolve(content) -> offset_for_source_line -> offset
```

Units and their boundaries:

| Unit | Responsibility | Depends on |
|---|---|---|
| `marks.rs` - `Anchor` | Capture and re-locate a position in source text. Pure functions. | nothing |
| `marks.rs` - `MarkStore` | Load, merge and atomically save `marks.json`. | `serde`, `serde_json`, `dirs` |
| `style.rs` / `markdown.rs` | Attach `source_line` to every rendered row. | nothing new |
| `viewer.rs` | Key handling, position lookups, toasts. | `marks.rs` API only |

## 4. Source lines through rendering

### 4.1 `Line` (`src/style.rs`)

```rust
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    pub source_line: Option<usize>, // 0-based; None for synthetic or JSON lines
}

impl Line {
    pub fn new(spans: Vec<StyledSpan>, meta: LineMeta) -> Self; // source_line: None
}
```

All ~51 `Line { .. }` literals across `markdown.rs`, `style.rs`, `json.rs` and `viewer.rs` move to `Line::new(..)` so the new field is set in one place.

### 4.2 Stamping (`src/markdown.rs`)

The `Renderer` builds a line-start index of the source once (`Vec<usize>` of byte offsets) and maps byte offsets to line numbers with binary search. Three rules, in priority order:

1. **Span-buffer lines.** When `current_spans` goes from empty to non-empty, the renderer records `buffer_line` = source line of the current event's `range.start`. `flush_line_with_meta` stamps the flushed line with `buffer_line`. This is what makes lazily flushed lines correct: list items are flushed when the *next* `Start(Item)` arrives (see the comment at `src/markdown.rs:1101`), and without this rule they would get the next item's line.
2. **Code blocks.** `emit_code_block` stamps each code row with `fence_line + 1 + i`, where `fence_line` is the line of the block's `range.start`. Long code blocks are a prime place for marks; block-level precision would snap them to the fence.
3. **Everything else.** The loop in `render_with` records `lines.len()` before each `process(event, range)`. Afterwards, every new line whose `source_line` is still `None` is stamped with the line of `range.start`. This covers blank lines, heading separators (pushed in `Start(Heading)`, so they get the heading's line), rules, tables, images, diagrams and math blocks.

Precision: paragraphs and tables resolve to their first row. A mark inside a long paragraph or table lands at its start, which is at most a few rows off. Acceptable for v1.

### 4.3 Wrapping (`src/style.rs`)

`wrap_lines` copies `source_line` to every wrapped row, in both the blockquote branch and the plain branch. Unlike `meta`, which is propagated selectively on purpose, every visual row should know its source line.

### 4.4 Image rows (`src/viewer.rs` `finalize_layout`)

Expanded image rows take the placeholder's `source_line`.

### 4.5 JSON (`src/json.rs`)

Always `None`. Marks are disabled for the JSON viewer.

### 4.6 Lookups on `ViewerState`

```rust
/// Source line of the top visible row. Walks forward to the next stamped row;
/// returns 0 if no row is stamped (empty document).
fn source_line_at(&self, offset: usize) -> usize;

/// First wrapped index whose source_line >= line, clamped to max_offset().
/// Returns max_offset() if no row qualifies.
fn offset_for_source_line(&self, line: usize) -> usize;
```

## 5. `src/marks.rs`

### 5.1 `Anchor`

```rust
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Anchor {
    pub line: usize,     // 0-based source line
    pub snippet: String, // trimmed source line, max 80 chars
}

impl Anchor {
    pub fn capture(source: &str, line: usize) -> Self;
    pub fn resolve(&self, source: &str) -> usize;
}
```

- `capture`: snippet is the source line at `line`, trimmed of leading and trailing whitespace, truncated to 80 characters on a `char` boundary. An out-of-range line yields an empty snippet.
- `resolve`, comparing each candidate line trimmed and truncated the same way:
  1. If `line` is in range and matches `snippet`, return `line`.
  2. Otherwise search outward over the whole file in the order `line-1, line+1, line-2, line+2, ...` and return the first exact match. Equal distance resolves to the earlier line because it is checked first.
  3. If nothing matches, or the snippet is empty, return `line.min(last_line)` (0 for an empty file).
- Healing: when `resolve` returns a line different from `anchor.line`, the viewer saves `Anchor::capture(source, resolved)` for that letter, so later edits are measured from the current position.

### 5.2 `MarkStore`

```rust
pub struct MarkStore {
    path: Option<PathBuf>,                               // None: session only
    read_only: bool,                                     // file is from a newer version
    files: BTreeMap<String, BTreeMap<char, Anchor>>,     // canonical path -> letter -> anchor
    notice: Option<String>,                              // one-time message for the viewer
}

pub enum SaveError { NoStateDir, ReadOnly, Io(io::Error) } // impl Display

impl MarkStore {
    pub fn load() -> Self;                 // default location
    pub fn at(path: PathBuf) -> Self;      // explicit location (tests)
    pub fn get(&self, file: &str, letter: char) -> Option<&Anchor>;
    pub fn set(&mut self, file: &str, letter: char, anchor: Anchor) -> Result<(), SaveError>;
    pub fn take_notice(&mut self) -> Option<String>;
}
```

- **Location:** `dirs::state_dir().or_else(dirs::data_local_dir)` + `mdterm/marks.json`. On macOS (no state dir): `~/Library/Application Support/mdterm/marks.json`. On Linux: `~/.local/state/mdterm/marks.json`.
- **Format:** pretty-printed JSON.

  ```json
  {
    "version": 1,
    "files": {
      "/Users/jan/notes/rollout.md": {
        "a": { "line": 41, "snippet": "## Rollout" }
      }
    }
  }
  ```

- **`set` writes through immediately:** update memory, then re-read the file from disk, merge only this `(file, letter)` entry, `create_dir_all` the parent, write `marks.json.tmp`, `rename` over `marks.json`. Concurrent mdterm instances never lose each other's marks; for the same `(file, letter)` the last write wins. The rename makes a crash unable to leave a truncated file.
- **No pruning** of entries for missing files in v1. Entries are tiny, and pruning would erase marks on temporarily unmounted volumes.

### 5.3 Error handling

| Situation | Behavior |
|---|---|
| No state or data dir resolvable | `path = None`. Marks work for the session. `set` returns `NoStateDir`. |
| `marks.json` missing | Empty store. Created on first `set`. |
| `marks.json` unparsable (on load or on the re-read inside `set`) | Rename to `marks.json.corrupt` (overwriting an older one), continue with an empty store, set `notice` to "Marks file was unreadable, moved to marks.json.corrupt". |
| `version` greater than 1 | Load the entries that parse, set `read_only = true`. `set` updates memory and returns `ReadOnly`. Older binaries never overwrite newer data. |
| Write or rename fails | Memory is already updated. `set` returns `Io(err)`. |
| `canonicalize` of the viewed file fails | Use the path as given. |

## 6. Viewer integration (`src/viewer.rs`, `src/main.rs`)

### 6.1 State and construction

- `ViewerOptions` gains `marks: MarkStore`. `main.rs` calls `MarkStore::load()` and passes it in; tests pass `MarkStore::at(tempdir)` and never touch real user data.
- `ViewerState` gains:
  - `marks: MarkStore`
  - `pending: Option<PendingKey>` with `enum PendingKey { SetMark, JumpMark }`
  - `mark_file: Option<String>` - canonical path of the current file, computed in `new()` and `switch_file()`; `None` when reading stdin.
- On the first frame, `marks.take_notice()` is shown as a warning toast if present.

### 6.2 Key flow

In `handle_event`, immediately after the Ctrl-C check and **before** `is_help_toggle`:

- If `pending` is `Some`, take it and call `handle_pending_mark(state, pending, code, mods)`, then return. This swallows every key:
  - `a-z` without Ctrl performs the set or jump.
  - Anything else (uppercase, digits, Esc, arrows) cancels silently.

This placement is required: otherwise `mh` and `'?` would open the help overlay.

In `handle_normal`, **before** the slide-mode and JSON early returns:

- `m` or `'` without Ctrl: if `marks_unavailable()` returns a reason, show it as a warning toast; otherwise set `pending`.
- `marks_unavailable()` reasons, checked in this order:
  - slide mode: "Marks unavailable in slide mode"
  - `json_view.is_some()`: "Marks unavailable for JSON files"
  - `mark_file.is_none()`: "Marks unavailable for stdin"

The existing `m` arm becomes `M`.

### 6.3 Set (`m{c}`)

1. `line = source_line_at(offset)`; `anchor = Anchor::capture(&content, line)`.
2. `marks.set(file, c, anchor)`.
3. Success: toast "Mark c set". Failure: warning toast "Mark c set (not saved: {err})".

### 6.4 Jump (`'{c}`)

1. No anchor: warning toast "Mark c not set".
2. `resolved = anchor.resolve(&content)`; `target = offset_for_source_line(resolved)`.
3. If `target != offset`: push `(current_file_idx, offset)` onto `nav_history`, set `offset = target`.
4. If `resolved != anchor.line`: `marks.set(file, c, Anchor::capture(&content, resolved))`, ignoring the error.
5. No toast on success; the view moving is the feedback.

Auto-reload, resize and the line-number toggle need no handling: anchors are resolved against the current `content` at jump time and `source_line` survives every rebuild.

### 6.5 Toast kinds (targeted improvement)

Failure toasts would otherwise render as "✓ Mark a not set". `set_toast` keeps its success meaning; a new `set_warning` shows the `!` prefix in a new theme color `toast_warning` (dark `#f9e2af`, light `#df8e1d`, both matching each theme's `search_prompt`). The existing "Invalid JSON - showing as plain text" toast moves to `set_warning`.

### 6.6 Help overlay and docs

- Help entries: `("m a-z", "Set mark")`, `("' a-z", "Jump to mark")`, `("M", "Toggle mouse capture (for text select)")`.
- README key table: add `m` + letter, `'` + letter, and `M`; note that marks persist per file.
- CLAUDE.md architecture: list `marks.rs` (eleven source files) and add the `source_line` step to the data flow.

## 7. Files touched

| File | Change |
|---|---|
| `src/marks.rs` | New: `Anchor`, `MarkStore`, `SaveError`, unit tests |
| `src/style.rs` | `Line.source_line`, `Line::new`, propagation in `wrap_lines` |
| `src/markdown.rs` | Line index, three stamping rules, `Line::new` adoption |
| `src/json.rs` | `Line::new` adoption |
| `src/viewer.rs` | Options/state fields, pending-key flow, `M` rebind, lookups, image-row propagation, toast kinds, help entries |
| `src/theme.rs` | `toast_warning` in both themes |
| `src/main.rs` | `mod marks`, `MarkStore::load()` into `ViewerOptions` |
| `Cargo.toml` | `[dev-dependencies] tempfile = "3"` |
| `README.md`, `CLAUDE.md` | Key table and architecture docs |

## 8. Testing

### Unit tests

- `marks.rs` `Anchor`: capture trims and truncates at 80 chars without splitting multi-byte text; resolve exact hit; content shifted down and up; 200 lines inserted above; nearest of several duplicates; equal-distance tie picks the earlier line; line deleted (clamp); empty snippet; empty file.
- `marks.rs` `MarkStore` (tempdir): set then reload round-trips; two stores on one path keep each other's marks; no `.tmp` left after `set`; corrupt file moved to `.corrupt` with a notice; version 2 file is read-only and unchanged on disk after `set`; no-path store returns `NoStateDir`.
- `markdown.rs`: `source_line` for headings (including the H1/H2 separator rows), paragraphs, every list item (the lazy-flush case), task items, each code row, tables, blockquotes, images.
- `style.rs`: `wrap_lines` copies `source_line` to every row, including blockquote rows.

### Viewer tests (existing `make_state_with_lines` helper)

- `ma`, scroll away, `'a` restores the offset.
- `mh` and `'?` set and jump instead of opening help.
- Esc after `m` cancels; the next key behaves normally.
- A jump pushes onto `nav_history`; `Backspace` returns.
- `M` toggles mouse capture; `m` no longer does.
- `m` shows the unavailable warning in slide mode, for JSON and for stdin.
- The mark resolves to the same source line after changing width and after toggling line numbers.

### End-to-end (tmux, real binary, `HOME` set to a temp dir)

1. `cargo build`, open a fixture with a long code block and several headings in a tmux pane.
2. Scroll so a heading is on top, press `m` `a`, quit with `q`.
3. Insert 30 lines at the top of the file. Reopen with a different `--width`.
4. Press `'` `a`. `tmux capture-pane -p` shows the heading on the top content row.
5. With mdterm still open, insert lines above the heading from another shell (auto-reload), press `'` `a` again, verify again.
6. Inspect `$HOME/Library/Application Support/mdterm/marks.json` (macOS): the healed `line` matches the new position.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Some renderer path pushes lines in a way none of the three stamping rules covers, leaving rows with the wrong source line. | Per-block-type unit tests in `markdown.rs`; `source_line_at` walks forward past unstamped rows rather than failing. |
| Short or repeated snippets (`}`, `---`, a closing fence) re-locate to the wrong copy after edits. | Nearest-first search keeps the match close to the original; healing keeps the stored line current. Accepted for v1. |
| `Line::new` migration touches many call sites in a 4,356-line `viewer.rs` and 2,293-line `json.rs`. | Mechanical change done as its own commit before any behavior change. |
| Users with muscle memory for `m` = mouse capture. | `M` is adjacent; help overlay and README updated. |
