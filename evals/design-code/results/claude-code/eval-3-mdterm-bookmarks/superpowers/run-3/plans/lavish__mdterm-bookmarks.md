# mdterm bookmarks - design spec

Date: 2026-10-01. Status: awaiting review.

## Goal

Vim-style bookmarks for long Markdown documents the user returns to (specs, notes, books).

- `m` + `a-z` sets a mark at the current position.
- `'` + `a-z` jumps to it.
- Marks persist per file between sessions.

**Success criterion:** set a mark, quit, change the terminal width or edit text above the mark, reopen, press `'a`, and the same passage is at the top of the viewport.

## Decisions

| Decision | Choice |
|---|---|
| `m` conflict | Mouse capture moves from `m` to `M`. `m` becomes the mark prefix. |
| Mark scope | Lowercase `a-z`, per file. No global (uppercase) marks. |
| Anchor | Source line + trimmed text fingerprint, resolved at jump time. |
| Storage | `dirs::data_dir()/mdterm/marks.toml` (state, not config). |
| Position marked | Top of the viewport (mdterm has no cursor). |
| Jump history | A jump pushes onto `nav_history`, so Backspace returns. |
| Supported views | Markdown files only. Stdin, JSON view and slide mode show a toast. |

## Out of scope

Uppercase/global marks, a marks list overlay, deleting marks, pruning entries for deleted files.

## Current state (verified)

- `m` toggles mouse capture (`src/viewer.rs:1647`), listed in `help_sections()` (`src/viewer.rs:3637`). `M` and `'` are unbound.
- `state.offset` is an index into `state.wrapped` (post-wrap lines). It shifts with terminal width, `l` line numbers, `width` config, image row expansion and file edits, so it cannot be persisted.
- `Line { spans, meta }` (`src/style.rs:56`) has no link back to the source.
- `render_with` already iterates `parser.into_offset_iter()` (`src/markdown.rs:1585`) and passes the byte range to `Renderer::process`.
- `config.rs` only reads. Nothing in mdterm writes to disk today.
- `nav_history: Vec<(usize, usize)>` (file index, offset) backs Backspace.

## Architecture

### 1. `src/style.rs` - source line on `Line`

- Add `pub source_line: Option<usize>` (1-based) to `Line`.
- `wrap_lines` and `word_wrap` copy `source_line` to **every** wrapped piece (unlike `meta`, which is only copied to the first piece for most types).
- Every `Line { .. }` literal gets `source_line: None` (markdown.rs, style.rs, json.rs, viewer.rs). The image row expansion in `finalize_layout` (`src/viewer.rs:639`) copies the image line's `source_line`.

### 2. `src/markdown.rs` - filling `source_line`

- `render_with` builds a line-start table once (`Vec<usize>` of byte offsets where each line begins). Byte offset to line uses `partition_point`.
- Default stamping: in the `into_offset_iter` loop, remember `lines.len()` before `process`. Afterwards, every new line whose `source_line` is `None` gets the line of `range.start`. One place, no per-site changes.
- Code blocks: they are emitted all at once, so default stamping would give every line the fence line. The emitter instead sets `fence_line + 1 + i` for content line `i`. The border lines get the fence line and the closing fence line.
- Tables: they are buffered and emitted at `End(Table)`. Record the source line at each `Start(TableHead)` / `Start(TableRow)` next to the buffered row, and stamp emitted rows and separators with it.
- Granularity: precision is per rendered logical line (heading, paragraph, list item, code line, table row). A mark set mid-paragraph lands at the paragraph's first line. This is accepted.

### 3. `src/marks.rs` - new module, no terminal code

```rust
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct Mark {
    pub line: usize,  // 1-based source line
    pub text: String, // trimmed text of that line
}

pub struct Resolved {
    pub line: usize,
    pub exact: bool,
}

pub fn resolve(mark: &Mark, source: &str) -> Resolved;

pub struct MarkStore { path: Option<PathBuf>, writable: bool, files: BTreeMap<String, BTreeMap<char, Mark>> }

impl MarkStore {
    pub fn load() -> Self;                  // default path from dirs::data_dir()
    pub fn load_from(path: PathBuf) -> Self; // used by tests
    pub fn get(&self, file: &Path, letter: char) -> Option<&Mark>;
    pub fn set(&mut self, file: &Path, letter: char, mark: Mark) -> Result<(), SaveError>;
}
```

**File format** (`marks.toml`), keyed by canonical absolute path:

```toml
["/Users/jan/notes/spec.md"]
a = { line = 120, text = "## Persistence" }
q = { line = 431, text = "The resolver prefers the nearest match." }
```

**`resolve` rules**, in order:

1. `mark.text` empty: return `mark.line` clamped to `[1, line_count]`. `exact` if not clamped.
2. The line at `mark.line` trims to `mark.text`: return it, `exact = true`.
3. Otherwise find every line that trims to `mark.text` and return the one with the smallest distance to `mark.line`. On a tie, the earlier line wins. `exact = true` (same passage, it only moved).
4. No match: return `mark.line` clamped to `[1, line_count]`, `exact = false`.

**`set`** re-reads the file from disk, updates only `files[file][letter]`, and writes atomically (write `marks.toml.tmp` in the same directory, then `rename`). Each `set` saves right away, so marks survive crashes, and two mdterm instances never overwrite each other's marks. The in-memory store is always updated, even if the save fails.

**File keys:** `fs::canonicalize(path)`, falling back to the path as given if that fails.

### 4. `src/viewer.rs` - thin glue

- New `enum MarkOp { Set, Jump }` and `pending_mark: Option<MarkOp>` on `ViewerState`, plus `marks: MarkStore` loaded once in `ViewerState::new`.
- A one-key prefix, not a `ViewMode`. At the top of the Normal-mode key path: if `pending_mark` is `Some`, take it and consume this key. `a-z` without Ctrl/Alt runs the op. Any other key (including Esc) cancels silently.
- `KeyCode::Char('m')` sets `pending_mark = Some(Set)`. `KeyCode::Char('\'')` sets `Some(Jump)`.
- The mouse capture toggle moves to `KeyCode::Char('M')` unchanged. The help entry becomes `("M", "Toggle mouse capture (for text select)")`, with new entries `("m a-z", "Set mark")` and `("' a-z", "Jump to mark")`.
- **Availability:** marks need a real file path and Markdown rendering. Stdin (`<stdin>`), the JSON view and slide mode get a toast and nothing else: `Marks unavailable for stdin` / `... in JSON view` / `... in slide mode`. Slide mode returns early in `handle_normal`, so its check happens before `handle_slide_keys` dispatch.
- The current file path is `state.files[state.current_file_idx]`.
- **Set:** take the first wrapped line at or after `state.offset` whose `source_line` is `Some`. Build `Mark { line, text: source_lines[line - 1].trim() }`. Call `marks.set`. On success, toast `Mark 'a' set`.
- **Jump:** `marks.get(file, letter)`, or toast `Mark 'a' not set`. Call `resolve(mark, &state.content)`. Find the first wrapped line whose `source_line >= resolved.line`, push `(current_file_idx, offset)` onto `nav_history`, then set `offset = idx.min(max_offset)`. Toast `Jumped to 'a'` if `exact`, otherwise `Mark 'a' moved - nearest position`.

## Data flow

```
Set:  m a -> top visible wrapped line -> source_line -> Mark{line,text} -> MarkStore::set -> marks.toml
Jump: ' a -> MarkStore::get -> resolve(mark, content) -> first wrapped line >= line -> offset
```

## Error handling

All failures are non-fatal: a toast, and the viewer keeps running.

| Situation | Behavior |
|---|---|
| Marks file missing | Empty store. File and directories created on the first save. |
| Marks file unparseable | Never overwritten (`writable = false`). Marks work for the session. Toast on set: `marks.toml unreadable - marks not saved`. |
| No data dir, or write fails | Mark kept for the session. Toast: `Could not save mark: <reason>`. |
| `canonicalize` fails | Path used as given. |
| `'x` with `x` unset | Toast `Mark 'x' not set`. |
| Stored line past end of file | Clamped, `exact = false`, "moved" toast. |
| Marked line is blank | Matched by line number only. |
| Several lines share the text | Nearest to stored line, earlier on a tie. |
| File auto-reloads | Nothing to do: marks resolve at jump time. |
| Pending prefix, then a non-letter key | Cancelled silently. The key is not processed further. |

## Testing

TDD per unit.

- **`marks.rs` unit tests**
  - `resolve`: exact match; line moved down; line moved up; duplicate text resolving to the nearest; tie resolving to the earlier; no match falling back and clamping; blank text.
  - `MarkStore` with `load_from` in a `tempfile::TempDir` (new dev-dependency): set then reload; two stores on one file merging; corrupt file left byte-identical after `set`; missing parent directory created.
- **`markdown.rs` / `style.rs` tests:** `source_line` correct for headings, paragraphs, list items, every code block content line, and table rows. Still present on every piece after wrapping at width 20.
- **`viewer.rs` tests:** `m a` stores a mark; `' a` moves `offset` and pushes `nav_history`; Esc and `1` cancel the prefix; unset letter toasts; stdin/JSON/slide toasts. If `ViewerState` cannot be built headless, extract the prefix handling into a pure function and test that. The existing `help_sections_no_duplicate_keys` test covers the rebinding.
- **End-to-end** (real binary in tmux, `HOME` set to a temp dir so the real marks file is untouched):
  1. `mdterm test.md`, scroll to a passage, `m a`, `q`.
  2. Resize the pane, insert 5 lines above the passage.
  3. Reopen, `' a`: the passage is at the top. `Backspace` returns to the start.
  4. `M` toggles mouse capture.

## Docs

- README keybinding table: add `m a-z`, `' a-z`, `M`.
- CLAUDE.md architecture list: add `marks.rs`, update the count to eleven files.

## Risks

- **Line literal churn:** adding a field to `Line` touches ~47 literals. It's mechanical and checked by the compiler.
- **Mid-paragraph precision:** marks snap to the paragraph start. Fine for the stated use, can be refined later with per-span source offsets.
- **Mouse muscle memory:** `m` stops toggling mouse capture. The help overlay and README document the move to `M`.
