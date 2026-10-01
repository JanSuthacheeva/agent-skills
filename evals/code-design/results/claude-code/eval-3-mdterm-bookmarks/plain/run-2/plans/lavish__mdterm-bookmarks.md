# mdterm bookmarks - implementation plan

## Goal

- `m` + letter sets a mark at the current position.
- `'` + letter jumps to that mark.
- Marks persist per file across sessions.

## Current state (verified)

- `m` is already bound: it toggles mouse capture (`src/viewer.rs:1647`, help entry at `src/viewer.rs:3637`). `'` and `M` are unbound everywhere.
- "Position" is `state.offset`, an index into `state.wrapped`, which holds lines after wrapping and image expansion. That index changes on resize (`Event::Resize` -> `rebuild()`), when an image loads (`finalize_layout()` shifts rows), when line numbers are toggled, and when the file is edited (auto-reload). Next session's terminal width will usually differ too. A raw offset can't be used as a mark.
- `Line` (`src/style.rs`) is `{ spans, meta }` and has no link back to the source. The renderer already gets byte ranges for every event (`parser.into_offset_iter()`, `src/markdown.rs:1585`), but throws them away. The one exception is `TaskItem.bracket_offset`.
- Key dispatch order in `handle_event`: Ctrl+C, then `is_help_toggle` (which grabs `h`/`?`), then the mode handler. Inside `handle_normal`, slide mode and JSON navigation take keys first (`h`, `l`, `j`, `k`, `L`, `H`, `D`). A two-key prefix has to be handled **before all of these**, or `m h` would open help.
- `nav_history: Vec<(file_idx, offset)>` plus Backspace already provides "go back".
- Persistence today is read-only config (`dirs::config_dir()/mdterm/config.toml`). There's no state file yet. `serde_json` is already a dependency.

## Proposed design

### 1. Source anchors on rendered lines (style.rs, markdown.rs)

Add `src: Option<usize>` to `Line`: the byte offset in the source markdown of the construct the line renders. `wrap_lines` already clones lines, so continuation rows inherit it. `finalize_layout` copies it onto expanded image rows.

- Renderer: record `line_src` when the first span of a pending line is pushed, and set it in `flush_line_with_meta`. Code blocks get an exact offset per line (block start plus the offset of each `\n`). Table rows use their `TableRow` start range. List items use their `Item` start.
- Synthetic lines (spacers, rules, JSON output, diagrams) get `None`.
- This also makes source positions available for future features (open-in-editor at line, sync scroll).

### 2. New module `src/marks.rs` (pure logic, no TUI)

```rust
pub struct Anchor { pub line: usize, pub text: String }   // 0-based source line + its trimmed text
pub struct FileMarks(BTreeMap<char, Anchor>);

pub fn anchor_at(content: &str, wrapped: &[Line], offset: usize) -> Option<Anchor>;
pub fn resolve(content: &str, wrapped: &[Line], a: &Anchor) -> usize; // wrapped index

pub struct MarkStore { path: PathBuf }
impl MarkStore {
    pub fn open_default() -> Option<Self>;              // state_dir() or data_local_dir()
    pub fn load(&self, file: &Path) -> FileMarks;       // missing or corrupt -> empty
    pub fn save(&self, file: &Path, marks: &FileMarks) -> io::Result<()>;
}
```

**anchor_at**: start at `wrapped[offset]` and walk forward to the first line where `src` is `Some`. Convert the byte offset to a source line number and record that line's trimmed text as a fingerprint.

**resolve** (runs at jump time, so it handles resize, image loads and edits the same way):
1. If `content` line `a.line` still has text `a.text`, use it.
2. Otherwise, search for the nearest line (by distance from `a.line`) whose trimmed text equals `a.text`. This handles lines inserted or deleted above the mark.
3. Otherwise, use `a.line` clamped to the end of the file.
4. Map the source line to a wrapped index: take the last wrapped line whose `src` line is <= the target, then step back to the first wrapped row of that block. Clamp the result to `max_offset()`.

### 3. Viewer integration (viewer.rs)

New state:
- `pending_key: Option<PendingKey>`, where `enum PendingKey { SetMark, JumpMark }`
- `marks: FileMarks` for the current file
- `mark_store: Option<MarkStore>`

Key handling, at the top of the `Event::Key` branch in `handle_event`, right after Ctrl+C:
- If `pending_key.take()` is `Some` and the mode is Normal, the key is consumed. If it's `a-z`, set or jump. Anything else (including Esc) cancels silently, like vim.
- Otherwise, in Normal mode (both regular and slide mode), `m` sets `PendingKey::SetMark` and `'` sets `PendingKey::JumpMark`.
- Set: `anchor_at(content, wrapped, top_line)`. In slide mode, `top_line` is `slide_boundaries[current_slide]`. Insert the mark, call `store.save(...)`, toast `Mark a set`.
- Jump: `resolve(...)`, push `(current_file_idx, offset)` onto `nav_history` so Backspace returns to where you were, set `offset`. In slide mode, set `current_slide` to the slide containing the target. Toast `Mark a not set` if the mark is missing.
- `switch_file`: reload `marks` from the store. File auto-reload needs nothing extra, because anchors resolve lazily.
- Status bar: while a prefix is pending, show ` m_ ` or ` '_ ` in the bottom border, using the same pattern as the search label.

Rebinds and help:
- Mouse capture toggle moves from `m` to `M`. Update the help entry, README and toast text.
- New help section "Marks": `m a-z` = set mark, `' a-z` = jump to mark, `Backspace` = back (after a jump). The existing `help_sections_no_duplicate_keys` test keeps the help entries honest.

### 4. Persistence format and behavior

- Path: `dirs::state_dir()` (Linux: `~/.local/state/mdterm/marks.json`), falling back to `dirs::data_local_dir()` (macOS: `~/Library/Application Support/mdterm/marks.json`). It's state, not config, so it stays out of `config.toml`.
- Key: `fs::canonicalize(path)`, so `./a.md` and `/abs/a.md` share marks.
- Schema:
  ```json
  { "version": 1,
    "files": { "/abs/README.md": { "a": { "line": 120, "text": "## Install" } } } }
  ```
- Writes: on every mark set, do a read-modify-write of only this file's entry, then write atomically (temp file in the same dir, then `rename`). Two mdterm instances won't overwrite each other's files, and a crash can't corrupt the store. On write, drop entries whose file no longer exists.
- Failures never crash the viewer. Corrupt or unreadable store -> empty marks. Save error -> toast `Could not save marks`.
- stdin input (no path): marks work for the session but aren't persisted.

### Scope limits (v1)

- JSON files: `m` and `'` show the toast `Marks are not supported for JSON`. JSON output has no source anchors, and expand/collapse changes line indices, so a stored offset would point at the wrong place.
- No mark list overlay or gutter indicator. Both can be added later on top of the same `FileMarks`.

## Test plan

- `marks.rs` unit tests: anchor and resolve round-trip on an unchanged doc; the same anchor resolves to the same block at widths 40/80/120; lines inserted above (fingerprint search); anchored line deleted (clamp fallback); mark on a blank spacer snaps to the next block; code block line precision.
- Store tests (temp dir under `std::env::temp_dir()`, no new dev-dependencies): round-trip; corrupt JSON -> empty; two stores saving different files merge; missing files are pruned.
- `markdown.rs` tests: every non-synthetic line has a `src` whose source line contains the rendered text (paragraphs, headings, lists, tables, code).
- Viewer key tests, in the same style as the `is_help_toggle` tests: `m h` sets mark `h` instead of opening help; `m Esc` cancels; `' x` unset -> toast; JSON nav doesn't eat the letter after a prefix; the slide-mode prefix works.
- E2E: drive the release binary in tmux. Set a mark, resize the pane, jump. Quit and relaunch, then jump. Edit the file above the mark while it's open, then jump.

## Implementation order (one commit each)

1. `Line.src` plus renderer tracking plus tests.
2. `marks.rs` anchor/resolve plus tests.
3. `MarkStore` persistence plus tests.
4. Viewer prefix keys, `M` rebind, status bar hint, help, README, and CLAUDE.md (now eleven source files).

## Risks

- Moving mouse capture from `m` to `M` breaks muscle memory for existing users. Call it out in the release notes.
- Anchors have block-level precision inside a long wrapped paragraph: a jump lands on the paragraph's first row. That's acceptable for prose, and code blocks are exact per line.
- Fingerprint collisions (for example, many identical `---` lines): the nearest match wins, which is the correct bias.

## Decisions

1. Mouse capture moves from `m` to `M`.
2. Mark letters are `a-z` only. `A-Z` stays free for possible future cross-file marks. After `m` or `'`, an uppercase letter cancels like any other non-mark key.
3. JSON files are out of v1. `m` and `'` show the toast `Marks are not supported for JSON`.
