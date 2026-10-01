## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've built the approaches page at `.lavish/bookmarks-approaches.html`. It uses mdterm's own dark/light colours from `src/theme.rs`, so it looks like the viewer. I need two decisions from you before I design the code.

**What I found in the codebase**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`). That toggle is also missing from the README controls table, which I'd fix alongside this. `'` is free in every mode.
- **No key sequences exist yet.** Every binding is a single key. Flows that need more than one key are modelled as `ViewMode` variants (`src/viewer.rs:230`), so "waiting for the letter" fits there.
- **The current position doesn't survive a width change.** `offset` counts screen rows after line wrapping, so resizing, a different terminal width or toggling line numbers changes what it points at. That matters most for marks that persist across sessions.
- **The closest existing feature is `Backspace` back-navigation** (`nav_history`, `src/viewer.rs:365, 1765`). It stores raw offsets and only lives in memory.
- **Nothing is saved to disk today except reading config.** `Config::load` falls back to defaults silently on any error (`src/config.rs:29`).

**The approaches**
- **A. Marks as screen-row offsets.** This is the smallest change, but a saved mark points somewhere else once the terminal width differs. Since persistence is the whole point, I don't recommend it.
- **B. Marks as source line numbers (recommended).** The renderer records the source line on each rendered line, and wrapping keeps it.
  - Marks then stay put across width changes, resizes, theme or line-number toggles, and sessions. Like vim, edits above a mark shift it.
  - The cost is a new field on `Line`, which is built in about 50 places across 4 files. The change is mechanical.
  - A mark inside a long paragraph returns to the paragraph's first row.
  - Marks only work for Markdown, not JSON files.
- **C. Marks as heading plus rows below it.** The renderer doesn't change. But the mark still drifts with width inside long sections, and it breaks when a heading is renamed or duplicated.

**Common to all three**
- A new `src/marks.rs` saves marks to `marks.json` in the user's data directory, keyed by the file's full path.
- Jumping to a mark adds to the back history, so `Backspace` returns you.
- Marks for stdin input last only for the session.

**Decisions needed**
1. **Approach:** A, B or C, or a mix. I recommend B.
2. **Mouse capture:** move it to `M` (my recommendation), or keep `m` for mouse and choose another key for setting marks.

Once you answer, I'll write the implementation page with full signatures and call chains.

## Simulated user turn 1

1. Approach B, source-anchored marks. That matches wanting marks to survive resizes and small edits.
2. Move mouse capture to `M`.

## Executor turn 2

I've written the implementation design to `.lavish/bookmarks-implementation.html`. It has signatures only, no function bodies, plus call chains with error paths, tests, assumptions and two open questions. I checked that the signatures match across the cards and call chains, and that the JavaScript parses, but I haven't looked at the rendered page in a browser.

**The shape**
- **`src/marks.rs` (new).** Owns the marks and saves them.
  - The API is `MarkStore::load()`, `load_from(Option<PathBuf>)`, `get(&MarkTarget, char) -> Option<usize>` and `set(&MarkTarget, char, usize) -> io::Result<()>`.
  - `MarkTarget` is either `File(PathBuf)` or `Stdin`.
  - Marks live in `dirs::data_dir()/mdterm/marks.json` as `{ version, files: { path: { letter: line } } }`.
  - Each `set` re-reads the file, merges in the one mark and writes atomically, so two running mdterm instances don't lose each other's marks. A corrupt file is never overwritten.
- **`style.rs`.** `Line` gets `source_line: Option<usize>`, and `wrap_lines` copies it onto every wrapped piece of a line.
- **`markdown.rs`.** The renderer records where each line came from in one place, the event loop in `render_with`, using three small helpers (`source_owner`, `stamp_new_lines`, `source_line_of`). None of the existing places that push lines need new logic; their struct literals just add `source_line: None`, like the 20 in `json.rs`.
- **`viewer.rs`.**
  - A new mode, `ViewMode::MarkPending(MarkAction::Set | Jump)`, waits for the letter, handled by `handle_mark_pending`, `set_mark` and `jump_to_mark`.
  - Two helpers convert between the screen and the source: `source_line_at_offset` and `offset_for_source_line`.
  - Jumping adds to the back history, so `Backspace` returns you.
  - While waiting for the letter, the status bar shows a hint. Mouse capture moves to `M`, and the help screen is updated.
- **`main.rs`.** Loads the store and passes it to the viewer the same way config is handled.
- **Docs.** The README gets the mark keys and the previously undocumented `M` mouse toggle. `CLAUDE.md` gets the new file.

**Two places this breaks existing patterns**
- It is the first time mdterm writes into a user directory.
- The source line is a field on `Line`, not a `LineMeta` variant, because every line has one.

**Open questions (my recommendation first)**
1. **Which letters?** I recommend `a-z` and `A-Z`, all per file. The alternatives are `a-z` only, or vim-style uppercase marks that work across files.
2. **Marks for files that no longer exist?** I recommend keeping them in v1. The alternative is removing entries whose path is gone each time marks are saved.

Please review the units, call chains and the 17 assumptions (section 8), and answer the two questions. Once you approve, I'll write the Markdown plan to `.lavish/bookmarks.md`.

## Simulated user turn 2

APPROVED
Q1: a-z only, per file. Q2: keep stale entries in v1.

## Executor turn 3

The plan is finished and saved in two files. No code has been written.

- **Review page:** `.lavish/bookmarks-implementation.html`. Both of your answers are folded in and the open-questions section is replaced by a "Review decisions" summary.
- **Markdown plan:** `.lavish/bookmarks.md`. It has every unit's signatures, the data types, the call chains with their error paths, the test plan, 18 assumptions and the decisions made. A later session can implement from it without the browser.

Your answers changed two things in the design:
- **Letters:** marks use `a-z` only, one set per file. After `m` or `'`, an uppercase key cancels just like any other non-letter key.
- **Old entries:** marks for files that no longer exist are kept in v1; nothing is pruned.

The earlier comparison page is still at `.lavish/bookmarks-approaches.html`. I didn't open a browser or start or end a lavish session.
