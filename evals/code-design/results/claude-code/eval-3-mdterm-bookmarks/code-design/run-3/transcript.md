## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

The approaches page is ready at `.lavish/bookmarks-approaches.html`. I haven't opened it for you, and I haven't screenshotted it to check how it renders. Its colours come from mdterm's own dark and light themes (`src/theme.rs:97`).

**What I found first:**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`, and the help entry at `:3637`). `'` and `M` are free.
- **The scroll position is tied to the current width.** It's stored as `ViewerState.offset`, which counts lines after word-wrapping and after images are expanded. A different terminal width next session, or images loading, would put a saved mark in the wrong place.

**Shared by all three approaches:**
- A new `src/marks.rs` with a `MarkStore`, built like `config.rs`. Marks are saved in `dirs::data_dir()/mdterm/marks.json`, not in the config file, keyed by the file's full path. The file is rewritten every time you set a mark.
- After you press `m` or `'`, a field on `ViewerState` (`pending_mark`) waits for the letter. It isn't a new `ViewMode`, because those represent open overlays.
- A jump saves your current spot in the existing back-navigation history (`nav_history`), so Backspace takes you back.

**The real decision is how a mark remembers its position:**

| | Idea | Main cost |
|---|---|---|
| **A. Wrapped offset** | Save the raw scroll position | Wrong after any width change, so it doesn't really meet "persist between sessions" |
| **B. Source line** (recommended) | Each rendered line records which source line it came from. A mark saves the source line at the top of the screen. | One new field on `Line`, so about 49 places that build a `Line` need a mechanical update, and wrapping and image expansion have to carry it through |
| **C. Nearest heading + offset** | Save the heading you're under, plus how far below it you are | Still drifts with width inside long sections, and renaming the heading loses the mark |

I recommend **B**. It's the only option where a mark means the same thing every session, and the renderer already keeps a source position for task checkboxes (`bracket_offset`), so it extends an existing pattern.

**Two decisions for you:**
1. **Approach:** A, B, C, or a mix?
2. **Mouse-capture toggle:** should it move to `M`? That's what I recommend. Or should `m` stay as it is and marks use a different key?

You can answer here or with the form at the bottom of the page. Once you've chosen, I'll write the implementation page with signatures, call chains, assumptions and open questions.

## Simulated user turn 1

B (source line), and yes, move mouse capture to M.

## Executor turn 2

The implementation page is ready at `.lavish/bookmarks-implementation.html`. As before, I haven't opened it or checked how it renders in a browser. The code snippets get syntax highlighting from a CDN and fall back to plain text offline.

**Shape of the design:**
- **New `src/marks.rs`:**
  - `DocKey` identifies a file by its full resolved path. `DocKey::for_file(&str) -> Option<DocKey>` returns `None` for stdin.
  - `Mark { source_line: usize }` is a saved position.
  - `MarkStore` has `load()`, `get(&DocKey, char) -> Option<Mark>` and `set(&DocKey, char, Mark) -> io::Result<()>`.
  - It's stored in `dirs::data_dir()/mdterm/marks.json`. Each `set` re-reads the file, merges in the new mark and writes it atomically (temp file, then rename). A corrupt file is never overwritten.
- **`Line` gets a new field**, `source_line: Option<usize>` (`style.rs`).
  - The renderer fills it in one central place: after each event in `render_with`, `Renderer::stamp_source_lines(from, range.start)` stamps the lines just produced.
  - Lines inside code blocks get their exact source line in `emit_code_block`.
  - Wrapping and image-row expansion copy the field to the lines they create.
  - JSON lines stay `None`.
- **Viewer:**
  - `ViewerState` gains `marks`, `mark_doc` and `pending_mark`, plus four methods: `top_source_line`, `offset_for_source_line`, `set_mark` and `jump_to_mark`.
  - A new `handle_mark_key` handles the letter. `handle_event` hands a pending mark key to it before the help-key check; otherwise `m` then `h` would open help.
  - The mouse-capture toggle body moves unchanged from `m` to an `M` arm.
- **Smaller edits:**
  - The status bar shows `m█` or `'█` while waiting for the letter.
  - The help screen gets the new keys.
  - `main.rs` loads the store and passes it in through `ViewerOptions`.
  - README and CLAUDE.md are updated. The README never listed the old `m` binding, so I'm adding that too.

The page also has sequence diagrams for setting a mark, jumping, rendering and startup, each with numbered steps including error paths. It lists 21 assumptions: for example, any non-letter key after `m` cancels silently, marks don't work in slide mode, stdin or JSON view, and moving a file loses its marks.

**Open questions (my recommendation first):**
1. **Uppercase letters:** per-file like lowercase (recommended), vim-style global marks that jump to another file, or lowercase only?
2. **Resize drift:** today a resize keeps the same line index, so the visible text shifts. Fix it in this change, as its own commit (recommended), using the same `top_source_line` / `offset_for_source_line` pair? Or leave it for a follow-up?
3. **JSON view:** no marks, just a message saying so (recommended), or anchor JSON marks to the node path, which is a bigger change?

You can answer here or with the forms on the page, plus any changes to names or assumptions. Once you approve, I'll write the Markdown plan to `.lavish/bookmarks.md`.

## Simulated user turn 2

Q1: lowercase only. a-z, per file, and A-Z should cancel like any other non-letter key. Please update assumption 1 and `handle_mark_key` to match.
Q2: yes, as its own commit.
Q3: unsupported, with a toast.

## Executor turn 3

I've updated `.lavish/bookmarks-implementation.html` with your three answers. Each is now built into the design, and the open-questions section is empty.

- **Q1, lowercase only:**
  - Assumption 1 now reads "`a-z` only, per file (26 per file); `A-Z` cancel like any other key". Assumption 7 matches it.
  - `handle_mark_key` now accepts only `KeyCode::Char(c) if c.is_ascii_lowercase()`, and its doc comment says `A-Z` cancel.
  - The set-mark diagram and its steps say "not a-z → cancel". The help entries became `m a-z` / `' a-z`.
  - I added a test case that `m` followed by `A` cancels.
- **Q2, resize drift, as its own commit:**
  - `ViewerState::rebuild()` now saves the source line at the top of the screen before re-rendering and scrolls back to it afterwards, using `top_source_line()` and `offset_for_source_line()`.
  - This replaces the current behaviour of restoring the old scroll index (`saved_offset`). The JSON view has no source lines, so it falls back to `saved_offset`, as today.
  - The render diagram and its steps show the new steps, and there's a new assumption plus a test case: after a `rebuild()` at a different width, the same source line is still at the top.
- **Q3, JSON view unsupported with a message:** this was already the design. I only removed the "See Q3" pointer.

All three answers are also listed under "Decided in review" in the recap. No signatures changed apart from the `handle_mark_key` condition.

Do you approve the design? Once you do, I'll write the Markdown plan to `.lavish/bookmarks.md`.

## Simulated user turn 3

APPROVED. The plan matches my answers: marks are a-z per file, mouse capture moves to M, state is stored in the data dir, and the resize fix is its own commit.

## Executor turn 4

The plan is saved and planning is finished. I haven't implemented anything.

- **Markdown plan:** `.lavish/bookmarks.md`. It's written so a later session can implement from it without the browser pages. It links to the HTML pages and covers:
  - the decisions you made in review;
  - a three-commit order, with the resize fix as its own commit 3;
  - every unit's file path and signatures;
  - the data types and the `marks.json` format;
  - each call chain with its error paths;
  - test seams and the 22 assumptions.
- **Review pages:** `.lavish/bookmarks-implementation.html` (the approved design) and `.lavish/bookmarks-approaches.html` (the approach comparison).

Per your instructions I didn't open these pages in a browser or start or end a lavish session.
