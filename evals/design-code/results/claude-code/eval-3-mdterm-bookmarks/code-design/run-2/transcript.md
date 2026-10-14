## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I looked through the viewer, renderer and config code and wrote the approaches page. I haven't designed the implementation yet. That comes after you pick an approach.

**Page:** `.lavish/bookmarks-approaches.html`. It uses custom CSS in mdterm's own dark/light theme colours from `src/theme.rs`, since the repo has no web design system. I haven't opened it or checked how it renders.

**What I found that shapes the design:**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`, help entry at `:3637`).
- **The current position is a row on screen, not a place in the file.** `state.offset` counts rows after line-wrapping (`src/viewer.rs:294`), and the wrapping is redone at the current width on every rebuild. A saved offset would point somewhere else after a resize, a `--width` change or toggling line numbers.
- **Image loads move rows during a session too.** When an image finishes loading, `finalize_layout` swaps its 3-row placeholder for the real height and only corrects `offset` (`:605-657`). Any other stored position would drift.
- **Rendered lines don't record where they came from.** `Line` holds only `spans` and `meta` (`src/style.rs:55`). The only source offset in the renderer is the checkbox position for task items (`src/markdown.rs:1110`).

**Approaches:**
- **A. Source-anchored (recommended).** Each rendered line records its source line number, and a mark stores that number. Width, line numbers and image heights stop affecting marks. The cost is about 50 mechanical edits where `Line` is built.
- **B. Heading-anchored.** A mark stores the nearest heading plus a row count below it. The rendering code doesn't change, but marks still drift after a resize or image load inside a long section, and break if the heading is renamed.
- **C. Raw offset.** Rejected for the reasons above: marks would be wrong in almost every new session.

All three add a new `src/marks.rs` module (its load/save follows `src/config.rs`) and a new view mode for the key after `m` or `'`, so `?` and `h` don't open help mid-command.

**Decisions I need from you** (the form at the bottom of the page asks the same):
1. **Approach:** A, B or C?
2. **The `m` conflict:** move mouse capture to `M` so `m` can be mark, like vim (my recommendation)? Or keep `m` for the mouse and pick another key for marks?
3. **Storage:** one `marks.json` in `dirs::data_dir()/mdterm/`, keyed by the file's full path (my recommendation)? Or a sidecar file next to each document? With the first, renaming or moving a file loses its marks.
4. **Edits to the file:** store the text of the marked line too, and find it again if lines shift (my recommendation, because mdterm reloads automatically while you edit)? Or store only the line number, like vim?

Mention anything else you want included, such as uppercase marks, `''` to jump back, marks in JSON files, or a list of marks. Once you answer, I'll write the implementation page with signatures and call chains.

## Simulated user turn 1

1. Approach A, source-anchored.
2. Move the mouse toggle to M so m becomes mark.
3. One marks.json in dirs::data_dir()/mdterm/, keyed by canonical path (state dir, not config.toml).
4. Re-anchor by stored line text, fall back to line number.

Marks are a-z only, per file, no uppercase for now.

## Executor turn 2

The implementation page is ready for review: `.lavish/bookmarks-implementation.html`. It uses the same mdterm theme colours as the approaches page. I haven't opened it or checked how it renders. The code panels load a highlighter from esm.sh and fall back to plain text offline.

**How it fits together:**
- **`src/marks.rs` (new).** It owns `Mark { line, row, text }`, the per-file map `FileMarks` (letter to `Mark`), and `MarkStore` with `open`, `at(path)`, `load` and `save`. `Mark::relocate(&self, source: &str) -> usize` finds the marked line again after edits: same line if its text still matches, else the nearest line with that text, else the stored line number.
- **Saving.** `save` re-reads `marks.json`, replaces only the current file's entry, and writes through a temp file plus rename. It refuses to overwrite a corrupt `marks.json` or one with a newer `version`, so other files' marks can't be lost.
- **`src/style.rs` and `src/markdown.rs`.** `Line` gets a new field `source_line: Option<usize>`. Stamping happens in one place, the `into_offset_iter` loop, and `wrap_lines` copies the value onto every wrapped row. The cost is adding `..Default::default()` to about 50 places that build a `Line`.
- **`src/viewer.rs`.**
  - Two new view modes, `MarkSet` and `MarkJump`, wait for the letter, and the status bar shows a ` m█ ` / ` '█ ` prompt like the search prompt.
  - `M` now toggles mouse capture.
  - `switch_file` loads the new file's marks.
  - Image rows keep their source line when images finish loading.
  - Two smaller fixes I found while tracing: images won't flicker while a mark prompt is showing, and `?` won't open help mid-command.
- **`src/main.rs`.** It creates the store and passes it in through `ViewerOptions`, which lets tests point it at a temp file.
- **`README.md`.** It gets the new keys. It never documented the old `m` mouse toggle, so this fills that gap too.

The page also has call chains for set, jump, load and rendering (including error paths and the toasts the user sees), conventions with file references, test seams, and eight assumptions. The assumptions worth checking:
- The position is the top visible row.
- Marks are off in slide mode and JSON views.
- Marks on stdin input last for the session only.
- Setting an existing letter overwrites it, and there is no delete command.

**One open question:** should a mark jump be undoable with Backspace? I recommend yes: it pushes onto the existing `nav_history`, so there's one way back and no separate vim `''` key.

Reply with your answer and any changes, or approve. Once you approve, I'll write the Markdown plan to `.lavish/bookmarks.md`. I haven't written it yet because the design isn't approved.

## Simulated user turn 2

APPROVED
Q1: yes, push mark jumps onto nav_history so Backspace returns.

## Executor turn 3

The plan is finished and written to two files. No code has been changed.

- **`.lavish/bookmarks-implementation.html`** is the approved design page. I removed the open question and added your answer: a mark jump pushes onto `nav_history`, so Backspace returns. The Backspace help text becomes "Go back (after a link or mark jump)".
- **`.lavish/bookmarks.md`** is the Markdown plan for the implementation session. It covers every unit with its file path and signatures, the `marks.json` format, the call chains with error paths, the test seams, the eight assumptions and the decisions you made. It links back to the design page.

The earlier `.lavish/bookmarks-approaches.html` is still there as the record of how A was chosen. Following your instruction, I didn't run any lavish-axi session commands.
