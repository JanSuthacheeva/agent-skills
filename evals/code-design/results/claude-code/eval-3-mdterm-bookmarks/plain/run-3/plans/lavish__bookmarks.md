# mdterm bookmarks - plan

## Goal

- `m` + letter: set a mark at the current position.
- `'` + letter: jump to that mark.
- Marks persist per file across sessions.

## Decisions

- Mouse capture moves from `m` to `M`.
- Letters `a-z`, per file only. No global `A-Z` marks; uppercase after `m`/`'` cancels like any other non-mark key.
- Marked lines show their letter in the left margin.

## Current state (verified in code)

- `m` is already bound: it toggles mouse capture (`src/viewer.rs:1647`, help entry at `:3637`). `'` and `M` are free.
- Position is `ViewerState.offset`, an index into `wrapped` (lines after word-wrap). It shifts on terminal resize, `-w`, line-number toggle, image row expansion and file edits. Persisting it raw would land on the wrong line next session.
- The renderer already sees source byte ranges (`parser.into_offset_iter()` at `src/markdown.rs:1585`), but `Line` does not carry them.
- There is no multi-key input state. `is_help_toggle` runs before `handle_normal`, so `m` then `h` would open help instead of setting mark `h`.
- `nav_history: Vec<(usize, usize)>` + Backspace already implements "go back".
- Only one persisted file today: `config.toml` (read-only).

## Approach

### 1. Width-independent anchors

Add `pub source: usize` (byte offset of the source block that produced the line) to `Line` in `style.rs`. Stamp it in `markdown::render_with`'s event loop: after each `renderer.process(event, range)`, set `source = range.start` on the lines that call just pushed. `wrap_lines` copies it onto every wrapped piece. No renderer internals change; the ~50 `Line { .. }` literals get `source: 0` (or a `Line::new(spans, meta)` constructor).

A mark is an `Anchor`:

```rust
#[derive(Serialize, Deserialize, Clone)]
pub struct Anchor {
    pub line: usize,  // 1-based source line of the block start
    pub row: usize,   // wrapped row within that block
    pub text: String, // trimmed source line, max 80 chars, for re-anchoring
}
```

- `anchor_at(wrapped, offset, source) -> Anchor`: take `wrapped[offset].source`, convert to line number, count rows back to the first wrapped line with the same `source`.
- `resolve(anchor, wrapped, source) -> usize`: if the source line still equals `text`, use it; otherwise search for the nearest line with identical text (file was edited); otherwise fall back to `line` clamped. Find the first wrapped line whose block covers that line, add `row` (clamped to the block's rows), clamp to `max_offset`.

Marks are resolved lazily at jump time, so resize and live reload need no extra handling.

### 2. New module `src/marks.rs`

Owns everything mark-related so `viewer.rs` only wires keys:

- `Anchor`, `anchor_at`, `resolve` (pure, unit-tested).
- `MarkStore` - persistence:
  - Path: `dirs::state_dir()` (Linux `~/.local/state/mdterm/marks.json`), falling back to `dirs::data_dir()` (macOS `~/Library/Application Support/mdterm/marks.json`). Not under `config_dir`, since this is state, not config.
  - Format (serde_json, already a dependency; `BTreeMap` for stable diffs):
    ```json
    { "version": 1,
      "files": { "/abs/canonical/path.md": { "a": { "line": 42, "row": 0, "text": "## Install" } } } }
    ```
  - Key = `fs::canonicalize(path)`, so `./a.md` and `../repo/a.md` share marks.
  - `load(path) -> BTreeMap<char, Anchor>`.
  - `set(path, letter, anchor)`: read-modify-write of the whole file, then write `marks.json.tmp` + `rename` (atomic). Re-reading before writing means two mdterm instances never clobber each other's other files' marks. Saved immediately on `m`, not on exit, so marks survive crashes / Ctrl+C.
  - Prune entries whose path no longer exists on each write.
  - All IO errors are non-fatal: toast "Could not save mark", in-session mark still works.

### 3. Viewer wiring (`viewer.rs`)

New state:

```rust
enum PendingKey { SetMark, JumpMark }

pending_key: Option<PendingKey>,
marks: BTreeMap<char, Anchor>,   // current file
mark_store: Option<MarkStore>,   // None if no state dir
```

- Load `marks` in `ViewerState::new` and in `switch_file`.
- In `handle_event`, for Normal mode, check `pending_key` **before** `is_help_toggle` so the second key is always consumed by the mark command. Then:
  - letter `a-z` -> set or jump; anything else (incl. Esc and `A-Z`) cancels silently.
  - Ctrl+C still quits (checked first).
- `m` sets `pending_key = Some(SetMark)`, `'` sets `Some(JumpMark)`, in both `handle_normal` and `handle_slide_keys`.
- Set: `anchor_at(..)`, insert, `mark_store.set(..)`, toast `Mark 'a' set`.
- Jump: `resolve(..)`, push `(current_file_idx, offset)` onto `nav_history` (so Backspace returns, same as following a link), set offset, toast `Jumped to 'a'`. Unknown mark: toast `Mark 'a' not set`.
- Slide mode: set uses the top line of the current slide; jump selects the slide containing the resolved line.
- Status bar shows `m-` / `'-` while a key is pending.
- Mouse capture moves from `m` to `M`; help overlay gets a "Marks" section (`m{a-z}`, `'{a-z}`, `M`).

### 4. Margin marker

Each content row is drawn as `│ ` + content (`src/viewer.rs:2528`). The letter **replaces the `│` border glyph** on marked rows: `a ## Ownership`. The space column stays, so content never touches the letter, and content width does not change (no reflow when the first mark is set).

- New theme field `mark: Color`. Dark uses the h5 yellow `rgb(249,226,175)`, light uses `rgb(223,142,29)`. Drawn bold.
- `ViewerState.mark_rows: HashMap<usize, char>` (wrapped line index -> letter), recomputed by resolving every mark at the end of `finalize_layout()` and after each set. This covers resize, reload, line-number toggle and image row expansion, since all of them go through `finalize_layout`. Rendering is a hash lookup per row.
- Only the resolved row is marked, not every wrapped row of the block.
- Several marks on one row: show the lowest letter.
- Works in slide mode for free, since slides use the same row loop.
- Not shown in HTML export or piped output.

### 5. Scope limits

- stdin (`<stdin>`): marks work in-session, never persisted (no stable key). No toast spam; just not saved.
- JSON view: `m` / `'` toast "Marks not available in JSON view". JSON lines have no stable source mapping and expand/collapse changes layout; revisit if needed.

## Tests

- `marks.rs` unit tests: `anchor_at` / `resolve` round-trip at widths 40/80/120; resolve after inserting lines above the mark (fingerprint search); resolve when the marked line was deleted (clamp); row clamping.
- `MarkStore` with a temp dir: save/load, merge with a concurrent write, prune missing files, corrupt JSON -> empty, not a panic.
- `style.rs`: `wrap_lines` propagates `source` to all pieces.
- `viewer.rs`: pending-key routing - `m` then `h` sets mark `h` (does not open help), `m` then `Esc` cancels, `'` then unknown letter toasts.
- `mark_rows`: recomputed after a width change; lowest letter wins on a shared row.
- E2E: run `cargo run -- test.md`, set `a`, quit, resize terminal, reopen, `'a` lands on the same heading and the `a` shows in the margin. Check both themes.

## Commits

1. `feat(style): track source offset on rendered lines`
2. `feat(marks): anchors and persistent mark store`
3. `feat(viewer): m/' bookmarks with per-file persistence` (incl. `m` -> `M` move, help, README)
4. `feat(viewer): show mark letters in the left margin`

## Risks

- Stamping by event: a line flushed lazily at the *next* block's Start event gets the next block's offset. Effect is at most one block off; covered by the round-trip tests, fix in the renderer if they show it.
- Moving mouse capture to `M` breaks muscle memory for existing users. Call it out in the README/changelog.
