## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I wrote the approaches page to `.lavish/bookmarks-approaches.html`. I didn't open it in a browser, as instructed. It uses the DaisyUI `nord` fallback styling, because mdterm is a terminal app and has no web design system to copy.

**What I found in the code**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`, and the help entry at `src/viewer.rs:3637`). `'` is free.
- **No key in the viewer starts a two-key sequence yet.** `handle_normal` handles one key at a time (`src/viewer.rs:1606`), so "m then a letter" needs a new pending-prefix state.
- **The scroll position isn't stable.** `ViewerState.offset` counts lines after word-wrapping, so it changes on terminal resize, the `l` line-number toggle, images loading and file reloads (`src/viewer.rs:605-657`).
- **Rendered lines don't know where they came from in the file.** The one exception is `TaskItem.bracket_offset` (`src/style.rs:39`), which shows the renderer could record source positions.

**The three approaches** differ in what a saved mark points to:
- **A. Save the scroll offset as-is.** This is the smallest change, but a saved mark is wrong whenever the terminal width differs from when it was set. That's the normal case between sessions, so I wouldn't ship it.
- **B. Save the enclosing heading plus how far into that section you were.** The renderer stays untouched, but marks are only approximate. They also break if the heading is renamed.
- **C. Save the source line number (recommended).** Each rendered line records which source line it came from, and a mark stores that line number plus a short snippet of its text. Marks land exactly regardless of resize, and the snippet lets them find their line again after edits. The cost is about 50 mechanical updates where `Line` structs are created, in `style.rs`, `markdown.rs` and `json.rs`.

**Please answer before I design the details:**
1. **Approach:** A, B, C or a mix? I recommend C.
2. **The `m` conflict:** should mouse capture move to another key, or should marks use a different key than `m`? I'd move mouse capture to `M`.
3. **Where marks are saved:** I'd use one JSON file at `dirs::data_dir()/mdterm/marks.json` (`~/Library/Application Support/mdterm/` on macOS, `~/.local/share/mdterm/` on Linux), keyed by the file's full path. Would you rather use a sidecar file next to each document, or a different location?
4. **Scope:** only lowercase per-file marks `a-z` as you described, or also vim-style uppercase marks that work across files, and `''` to jump back to where you were before the last jump? I'd do `a-z` plus `''` now. Uppercase marks would change what gets saved, so I need to know now if you want them later.

## Simulated user turn 1

1. Approach C, since marks should survive resizes and small edits.
2. Yes, move mouse capture to `M`.
3. Your location is fine: the platform state directory, not config.toml. Use `marks.json` there.
4. Only `a-z`, per file. No uppercase marks for now. Skip `''` too.

## Executor turn 2

I wrote the implementation design to `.lavish/bookmarks-implementation.html`. I didn't open it in a browser, as instructed. I only checked that its inline scripts parse, so I haven't seen how it renders.

**How it fits together**
- **`style.rs`:** `Line` gets a new field, `source_line: Option<usize>`, holding the 1-based line in the markdown file. `wrap_lines` copies it to every wrapped piece. The ~50 places that build a `Line` add `..Default::default()`, the same way `Style` is already built.
- **`markdown.rs`:** the renderer fills in that field. Code blocks map each row to its own source line, text lines get the line of their first text, and everything else gets the line where the block starts.
- **New `src/marks.rs`:**
  - `Mark { line, text }`: the source line and its trimmed text.
  - `Mark::capture` and `Mark::resolve`. `resolve` returns `Exact`, `Moved` or `Approximate`, depending on whether the text is still on that line, was found nearby, or is gone.
  - `FileMarks::load` and `FileMarks::save`. Loading falls back to empty marks without an error, like `Config::load`. Saving reads the file again before writing and writes atomically.
  - It never overwrites a `marks.json` it can't parse, so a corrupt file doesn't wipe other files' marks.
- **`viewer.rs`:**
  - A new mode, `ViewMode::Mark(Set | Jump)`, waits for the letter, and a new `handle_mark` handles it.
  - `ViewerState` gets `marks: FileMarks`, plus `set_mark`, `jump_to_mark` and two functions that convert between source lines and wrapped lines.
  - Mouse capture moves to `M`, and the help screen and status bar are updated.

**Call chains.** The page has four, each with a diagram and numbered steps including failures: rendering, `m`+letter, `'`+letter, and opening or switching files. Failures show as toasts:
- Pressing `m` in a JSON view says "Nothing to mark here".
- If saving fails, the mark still works for this session and the toast says it wasn't saved.
- Jumping to a mark that was never set says "Mark a not set".
- If the marked text is gone, it still jumps and says it landed on the nearest line.

**Assumptions to confirm or overrule**
1. A mark records the top line of the screen, and jumping puts that line back at the top.
2. Setting a letter that's already used overwrites it without asking.
3. A successful jump shows no message.
4. If a mark's text is found on a different line, the stored line is updated during the jump.
5. Jumps don't affect `Backspace`, which stays "go back after following a link".
6. Marks don't work in slide mode or JSON views.
7. Inside a long paragraph, a mark lands on the paragraph's first line. Code blocks are exact to the line.
8. Entries for deleted files are never cleaned up.

**Open questions**
1. **macOS and Windows have no state directory** (`dirs::state_dir()` returns `None` there). My recommendation is to fall back to `dirs::data_dir()`, which is `~/Library/Application Support/mdterm/marks.json` on macOS. On Linux it stays `~/.local/state/mdterm/marks.json`.
2. **Renamed or moved files lose their marks,** because marks are keyed by the file's full resolved path. Is that acceptable? I recommend yes. Keying by content breaks on edits, and keying by inode isn't portable and breaks on atomic saves.

Once you approve or send changes, I'll update the page and write the Markdown plan to `.lavish/bookmarks.md`.

## Simulated user turn 2

APPROVED. Q1: fall back to `data_dir()`. Q2: canonical path is fine. Assumptions 1-8 are all fine.

## Executor turn 3

The design is finished and approved, and both plan files are written. No code has been written yet.

- **Review page:** `.lavish/bookmarks-implementation.html`. It now lists your answers in place of the two open questions.
- **Markdown plan:** `.lavish/bookmarks.md`, for a later implementation session. It has the decision, every new unit with its signatures, the data structures and file format, the four call chains with their error cases, test seams, and the eight confirmed assumptions.

Your review answers, now in both files:
- **Storage:** marks go in the platform state directory, falling back to `dirs::data_dir()` where there isn't one. That's `~/.local/state/mdterm/marks.json` on Linux and `~/Library/Application Support/mdterm/marks.json` on macOS.
- **File identity:** marks are keyed by the file's canonical path, so renaming or moving a file loses its marks.

I didn't run the `lavish-axi` open, poll or end commands, so there's no review session left open. The earlier approaches page is still at `.lavish/bookmarks-approaches.html`.
