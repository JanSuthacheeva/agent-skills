# mdterm bookmarks - plan

## Goal

- `m` + letter sets a mark at the current position. `'` + letter jumps to it.
- Marks are stored per file and survive restarts.
- A mark must still land in the right place after the terminal is resized, line numbers are toggled, images load, or the file is edited.

## Current state (verified)

- `m` is already bound: it toggles mouse capture (`src/viewer.rs:1647`, help entry at `src/viewer.rs:3643`). `'` and `M` are free in every handler.
- Position is `ViewerState.offset`, which is an index into `wrapped`, the list of lines after word-wrapping. That index changes with terminal width, line-number toggling and image row expansion (`finalize_layout`). **Saving `offset` to disk would be wrong.**
- `Line` has no link back to the source text. `markdown::render_with` already gets byte ranges from `parser.into_offset_iter()` (`src/markdown.rs:1585`), but those ranges are thrown away.
- Persistence today only covers config (`config.rs`, read-only TOML). Navigation history (`nav_history: Vec<(file_idx, offset)>`) is kept in memory and `Backspace` pops from it.

## Core decision: what a mark points to

A mark is a **source anchor**, not a wrapped-line index:

```rust
struct Anchor { line: usize, text: String }   // 0-based source line + its trimmed text
```

- **Set:** take the top visible wrapped line, look up its source byte offset, convert that to a source line, and save that line's number and trimmed text.
- **Jump:** look at the stored line in the current content.
  1. If the text there still matches, use it.
  2. If it doesn't, find the line with the same text that is nearest to the stored line number. This handles text added or removed above the mark.
  3. If no line matches, fall back to the stored line number, clamped to the end of the file.
  Then map the source line to the first wrapped line of the block that contains it, clamped to `max_offset`.

This doesn't depend on width, line numbers or images, and it survives ordinary edits. Other options I rejected:
- Storing the wrapped offset breaks on any resize.
- Storing the offset plus the width it was taken at is still wrong after an edit or a line-number toggle.
- Anchoring to a heading plus a distance is coarse and fails in files without headings.

## Architecture

```
keys -> handle_normal / handle_slide_keys
          |  pending_mark: Option<MarkAction>
          v
ViewerState  --(source_at_offset / offset_for_source)-->  wrapped[i].source
          |
          v
marks.rs: anchor_at / resolve (pure)  +  MarkStore (load / save JSON)
          |
          v
<state_dir>/mdterm/marks.json
```

### 1. `style.rs` + `markdown.rs` - source mapping on `Line`

- Add `pub source: Option<usize>` to `Line`. It holds the byte offset of the source construct that produced the line. Update every `Line { .. }` literal (markdown.rs, json.rs, style.rs). JSON lines get `None`.
- `word_wrap` / `wrap_lines`: copy `source` onto every line split from the same source line, the same way `meta` is copied for headings and lists today. Image placeholder rows created in `finalize_layout` keep the source of the line they came from.
- In the `render_with` loop, stamp lines automatically instead of changing every push site:
  ```rust
  for (event, range) in parser.into_offset_iter() {
      let before = renderer.lines.len();
      renderer.process(event, range.clone());
      renderer.stamp_source(before, range.start); // fills only None, non-blank lines
  }
  ```
  Blank spacer lines stay `None`, so they are never used as anchors.
- Code blocks get exact per-line offsets: each emitted content line is set to its own source line offset at the push site. Because the stamp loop only fills `None`, it won't overwrite these. Without this, marks inside long code blocks would snap to the opening fence.
- Resulting precision: one anchor per paragraph, list item and heading; one per line in code blocks; one per table. Tables are acceptable for v1.

### 2. New `src/marks.rs`

```rust
#[derive(Serialize, Deserialize, Clone)]
pub struct Anchor { pub line: usize, pub text: String }
pub type FileMarks = BTreeMap<char, Anchor>;

pub fn anchor_at(content: &str, byte: usize) -> Anchor;
pub fn resolve(content: &str, anchor: &Anchor) -> usize; // byte offset of resolved line start

pub struct MarkStore { path: Option<PathBuf> }
impl MarkStore {
    pub fn open() -> Self;                 // default location
    pub fn at(path: PathBuf) -> Self;      // tests
    pub fn load(&self, file: &Path) -> FileMarks;
    pub fn save(&self, file: &Path, marks: &FileMarks) -> io::Result<()>;
}
```

- **Location:** `dirs::state_dir().or_else(dirs::data_local_dir)/mdterm/marks.json`. That is `~/.local/state/mdterm/marks.json` on Linux and `~/Library/Application Support/mdterm/marks.json` on macOS. Marks are state written by the program, not config, so they don't belong in `config.toml`.
- **Format:**
  ```json
  { "version": 1,
    "files": { "/abs/canonical/notes.md": { "a": { "line": 42, "text": "## Install" } } } }
  ```
  JSON because `serde_json` is already a dependency and the file is machine-written. The `version` field allows a later migration.
- **Key:** `fs::canonicalize(path)`, so `./a.md`, `a.md` and symlinks all share one set of marks.
- **Save:** read the file from disk, replace only this file's entry, drop entries whose paths no longer exist, then write to `marks.json.tmp` and rename it over `marks.json`. Two mdterm instances open on different files won't overwrite each other's marks, and a crash can't leave a half-written file.
- **Corrupt file:** rename it to `marks.json.corrupt`, start empty, and show a toast once. This keeps the bad data for inspection without blocking persistence forever.
- **Stdin:** there is no path, so marks work only for the session and are never saved.

### 3. `viewer.rs` - wiring

New state:

```rust
enum MarkAction { Set, Jump }

mark_store: MarkStore,
marks: FileMarks,                 // marks of the current file
pending_mark: Option<MarkAction>, // waiting for the letter
```

- **Loading:** marks load in `ViewerState::new` and again in `switch_file` for the new file.
- **Keys:** at the top of `handle_normal`, before the slide or JSON dispatch:
  - If `pending_mark` is set, take it. `a`-`z` sets or jumps. `Esc` or any other key cancels without doing anything.
  - Otherwise `m` sets `pending_mark = Some(Set)` and `'` sets `Some(Jump)`.
- **Helpers:**
  - `source_at_offset()`: scans forward from the top visible line to the first line whose `source` is `Some`.
  - `offset_for_source(byte)`: binary search over the stamped wrapped lines.
- **Set:** compute the anchor, insert it, save, then toast `Mark a set`. If saving fails, toast `Mark a set (not saved: <err>)`.
- **Jump:** push `(current_file_idx, offset)` onto `nav_history`, so `Backspace` returns to where you were, the same as after following a link. Then resolve the anchor and set `offset`. A missing mark gives the toast `Mark a not set`.
- **Slide mode:** set uses the first line of the current slide. Jump goes to the slide that contains the resolved line, found via `slide_boundaries`.
- **JSON view:** JSON lines have no source offsets, so both keys show `Marks are not available for JSON`.
- **Status bar:** while a mark key is pending, the hint area shows `m_ set mark`, or `' jump: a c f` listing the marks that exist. This gives visible feedback for the two-key sequence.
- **Mouse capture toggle:** moves from `m` to `M` (approved).
- **Docs:** add a "Marks" section to `help_sections()`, update the key table in the README, and update the source file list in CLAUDE.md (now 11 files).

## Scope decisions (defaults, overridable)

- Only `a`-`z`. `A`-`Z` stay free in case global marks across files (vim-style) are wanted later.
- No `''` (jump back to the previous position). `Backspace` already does that through `nav_history`.
- No marks list overlay in v1. The status bar hint shows which letters are set.
- Setting a mark on a letter that is already used overwrites it silently, as in vim.

## Risks / failure modes

- Adding `Line.source` touches about 40 struct literals. The changes are mechanical and the compiler finds every one.
- In files with many identical lines (for example `---`), the text fingerprint can match the wrong line. Searching for the nearest match keeps this local.
- Marks in a long paragraph or a table snap to the start of that block. This is documented as expected behavior.
- If the store directory can't be written (read-only home), marks still work for the session and a toast explains why they weren't saved.

## Tests

- `marks.rs`:
  - The anchor round-trips on unchanged content.
  - A line inserted above the mark moves it to the shifted line.
  - A deleted line falls back to the clamped line number.
  - With duplicate text, the nearest match wins.
  - The store round-trips.
  - Saving one file keeps the other files' entries.
  - A corrupt file is backed up and the store starts empty.
- `markdown.rs`: headings, paragraphs and code-block lines get the expected source offsets.
- `style.rs`: wrapping copies `source` onto every continuation line.
- `viewer.rs`:
  - A mark set at 80 columns lands on the same heading after a rebuild at 40 columns and with line numbers on.
  - Pending state is cancelled by `Esc` or a non-letter key.
  - Mouse toggle now works on `M`.
- E2E: run the real binary in tmux. Set `ma` partway down `test.md`, quit, reopen in a narrower pane, press `'a` and confirm it lands on the same content. Then insert lines above the mark in an editor and confirm auto-reload plus `'a` still find it.

## Commits

1. `feat(render): track source offsets on rendered lines` (style.rs, markdown.rs, json.rs, tests)
2. `feat(marks): add anchor resolution and persistent mark store` (marks.rs, tests)
3. `feat(viewer): add m/' bookmarks, move mouse toggle to M` (viewer.rs, help, README, CLAUDE.md, tests)

## Decisions

- **Mouse capture toggle moves from `m` to `M`** (approved). `m`/`'` now set and jump to marks, as in vim. The help entry, README and tests are updated to match.
