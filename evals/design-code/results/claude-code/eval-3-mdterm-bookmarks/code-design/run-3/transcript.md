## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've written the approaches page at `.lavish/bookmarks-approaches.html`. I haven't opened it or started a review session, as instructed. It uses mdterm's own dark and light palettes from `src/theme.rs` so it matches the project.

**The key point:** mdterm's only idea of "where you are" is `ViewerState.offset`, a position counted in screen lines after word-wrapping (`viewer.rs:292-294`). That count changes when you resize the terminal, use `-w` or `l`, or when images above you finish loading. So the real design question is what a saved position means.

**The three approaches:**
- **A - store the screen-line position.** Works the same way as the Backspace history (`viewer.rs:365`). It's the smallest change, but the next session almost never has the same terminal width, so saved marks would usually land in the wrong place.
- **B - store the source line in the file (recommended).** The markdown renderer records which source line each rendered line came from, in one place (the `into_offset_iter` loop, `markdown.rs:1585`). That's the same trick the task checkboxes already use (`bracket_offset`, `style.rs:42`). A new `marks.rs` handles saving, loading and converting positions, and `viewer.rs` only handles the keys. Marks survive resizing and every other layout change.
  - **Weak spot:** edits above a mark shift it down or up.
  - **Weak spot:** a mark inside a long paragraph or code block lands on its first line.
  - **Weak spot:** the JSON viewer has no source lines.

  All three can be fixed inside `marks.rs` without changing the structure.
- **C - store the nearest heading above you.** No renderer change, but the distance below the heading still drifts on resize, renaming the heading loses the mark, and files without headings fall back to A.

**Problems I found:**
- **`m` is already taken.** It toggles mouse capture (`viewer.rs:1647`). I suggest moving that to `M`, which is free.
- **Help keys get in the way.** `h` and `?` are handled before anything else (`viewer.rs:999`), so `m` followed by `h` would open help instead of setting mark `h`. The waiting-for-a-letter check has to run first, which affects where it goes in the code.
- **The README is wrong on macOS.** It says the config lives at `~/.config/mdterm/config.toml`, but `dirs::config_dir()` points to `~/Library/Application Support` there. I'll fix it along the way unless you object.

**Decisions I need from you** (they're also in the form on the page):
1. **Approach:** A, B or C, or a mix. I recommend B.
2. **Mouse capture:** OK to move it to `M`?
3. **Where marks are saved:** I recommend one `marks.toml` in the platform state folder (falling back to the local data folder), keyed by the file's full path. That keeps machine-written data out of your hand-edited config. The alternatives are one file per document, or a small file saved next to each document.

Once you answer, I'll design the chosen approach in full: types and function signatures, the step-by-step calls for setting a mark, jumping to one, and loading after a restart, plus test points. I'll also bring a few smaller questions for that stage: what happens to marks when the file is edited, whether uppercase letters work across files, and whether jumping to a mark should be undoable with Backspace.

## Simulated user turn 1

1. Approach: B.
2. Mouse capture: yes, move it to `M`.
3. Storage: one marks.toml in the platform state dir, keyed by canonical path. Fine with the README fix too.

## Executor turn 2

I've written the implementation page at `.lavish/bookmarks-implementation.html`. Its inline scripts pass a syntax check and the sequence-diagram code runs, but I haven't viewed it in a browser. It uses the same mdterm palette as the approaches page. The Markdown plan `.lavish/bookmarks.md` comes once you approve.

**The structure:**
- **`style.rs`**: `Line` gets a new field, `source_line: Option<usize>`, holding the line number in the markdown file. `wrap_lines` copies it onto every wrapped row. A new `Line::new(spans, meta)` replaces the ~50 places that build `Line` directly, so the next field won't need touching all of them again.
- **`markdown.rs`**: `render_with` stamps the source line in one place, around each `renderer.process(event, range)` call, using a private byte-offset-to-line lookup. `Renderer` itself is untouched.
- **`marks.rs` (new)**:
  - `MarkStore` has `load`, `load_from`, `get` and `set`.
  - `set` re-reads the file, merges, and replaces it in one step (write a temp file, then rename), so two mdterm windows don't overwrite each other's marks.
  - `anchor_at` turns the current position into a `Mark`; `resolve` turns a `Mark` back into a position.
  - It only sees `&[Line]` and `&str`, never the viewer.
- **`viewer.rs`**:
  - The store arrives through `ViewerOptions`, loaded in `main.rs` the same way config values are, so tests can pass a temporary store.
  - Adds `PendingMark { Set, Jump }`, `handle_mark_key`, `set_mark`, `jump_to_mark`, `top_line` and `scroll_to_line`.
  - A half-typed `m` or `'` is handled before the help keys, so `m` then `h` sets mark `h` instead of opening help.
  - Mouse capture moves to `M`; while a sequence is pending the status bar shows ` m█ `.

**What gets saved:** each mark stores the source line, the number of wrapped rows into that block, and the trimmed text of the line. The text lets a jump find the mark again after you edit the file. The file has a `version = 1` field so a future format change can migrate old marks instead of dropping them.

**Error handling:**
- If the marks file is corrupt or was written by a newer mdterm version, it is never overwritten.
- The mark still works for the current session, and a toast says why it wasn't saved.
- Stdin and JSON files get "Marks need a markdown file".

**Design choices to check** (the page lists eight assumptions you can overturn):
- **Mark position:** a mark is the top line of the screen, since mdterm has no cursor.
- **Backspace:** jumping to a mark adds to the Backspace history, so Backspace takes you back.
- **Cancelling:** any non-letter after `m` or `'` cancels the sequence silently.
- **Slide mode:** marks work there too.
- **First custom error type:** `MarkStoreError` is the first custom error enum in mdterm, because the viewer has to explain why a save failed.
- **First disk write:** `marks.rs` is also the first module that writes to disk.
- **Docs:** the README gets the new keys and the corrected macOS config path. CLAUDE.md's "Ten source files" becomes eleven.

**Open questions.** The design already uses my recommendation for each; the page also has a form for them.
1. **Uppercase letters:** per-file and case-sensitive, giving 52 slots (recommended), or vim-style global marks that jump across files?
2. **Surviving edits:** store the line text and re-find the nearest matching line (recommended), or line number only?
3. **Reusing a letter:** overwrite with "Mark 'a' set" (recommended), or say which line it replaced?
4. **Files that no longer exist:** remove their marks on every save (recommended), or keep them forever?

Answer those, plus any names or splits you'd change, or say "approved" and I'll write `.lavish/bookmarks.md`.

## Simulated user turn 2

Q1: lowercase only, a-z. Uppercase cancels the sequence, like any other non-letter. No A-Z marks for now, so "ASCII letter" in the design should become a-z.
Q2: line + text fingerprint, re-anchor to the nearest match.
Q3: overwrite silently, toast "Mark 'a' set".
Q4: prune on every save.

Names and splits are fine as proposed.

## Executor turn 3

I've updated the implementation page with your answers and written the Markdown plan. No code is written yet.

**Files:**
- `.lavish/bookmarks-implementation.html` - the review page. The open-questions form is gone; section 9 now lists your four answers as decisions.
- `.lavish/bookmarks.md` - the plan a later session can implement from without the browser. It links the page and contains the signatures, data types, call chains with error paths, test points and assumptions. It goes in `.lavish/` rather than `docs/plans/` because your instructions for this session set that location.

**What changed on the page:**
- **Letters:** marks are `a`-`z` only. Uppercase now cancels the sequence like any other key outside `a`-`z`. I made that consistent everywhere it appears: the key-handling notes, the set-mark error path, the doc comment on `handle_mark_key`, and assumption 3. The help entries read `m + a-z` and `' + a-z`, and the example `marks.toml` no longer has an uppercase mark.
- **New test:** `m` followed by `A` must cancel.
- **The other three answers** were already the recommended defaults the design used, so they're now recorded as decisions:
  - Each mark stores its line plus the line's text, and a jump re-finds the nearest matching line.
  - Reusing a letter overwrites it silently with the toast "Mark 'a' set".
  - Every save removes marks for files that no longer exist.

As instructed, I didn't open a browser or run any lavish-axi commands, so the review page hasn't been checked visually and there's no session to end. When you want to start building, the plan is in implementation order, and the first thing to commit would be the `Line.source_line` change with its tests.

## Simulated user turn 3

APPROVED
The plan matches my answers and I have no further points.

## Executor turn 4

The plan is approved and finished. The final files are in place and I checked that each one exists:

- `.lavish/bookmarks-implementation.html` - the review page, with your answers recorded as decisions in section 9.
- `.lavish/bookmarks.md` - the plan an implementation session should follow.
- `.lavish/bookmarks-approaches.html` - the approaches comparison, kept for reference.

As instructed, nothing has been implemented and I didn't run any lavish-axi commands.
