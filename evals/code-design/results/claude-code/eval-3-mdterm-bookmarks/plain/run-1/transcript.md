## Eval Prompt

i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've written the plan to `.lavish/bookmarks.html` and `.lavish/bookmarks.md`. The HTML uses mdterm's own dark theme colours from `theme.rs`. No code has been written yet.

**What I found in the code:**
- **Key conflict:** `m` already toggles mouse capture (`src/viewer.rs:1647`). `'` and `M` aren't used anywhere.
- **Can't save the scroll position as is:** the current position, `offset`, counts lines after word-wrapping. That count changes with terminal width, line numbers and image loading, so a saved value would be wrong next time.
- **Source positions are thrown away:** the Markdown parser already reports where each block sits in the source file, but rendered lines don't keep it.

**Proposed structure:**
1. **Remember where each line came from.** Rendered lines get a new `source` field holding their position in the source file. It's filled in one place, the main render loop, rather than at all ~40 places that create lines. Code blocks get an exact position per line, so a mark inside a long code block doesn't jump to its top.
2. **A mark points at source text.** It stores the source line number plus that line's text. To jump, check whether the stored line still has that text. If not, use the nearest line with the same text, which handles edits above the mark. If nothing matches, use the stored line number. Marks then still land correctly after resizes, line-number toggles, images loading and normal edits.
3. **New `src/marks.rs`** for finding and saving marks. Marks go in `marks.json` in the state directory, keyed by the file's full resolved path:
   - Each save re-reads the file and replaces only the current file's entry, then writes atomically, so two mdterm windows don't overwrite each other.
   - A corrupt file is renamed to `marks.json.corrupt` and the store starts empty.
   - Input from stdin gets marks for that session only.
4. **Changes in `viewer.rs`:**
   - After `m` or `'`, mdterm waits for the letter and shows a hint in the status bar, e.g. `' jump: a c f`.
   - Jumping records where you were, so `Backspace` takes you back.
   - Slide mode jumps to the slide containing the mark.
   - In JSON files, `m` and `'` only show a message saying marks aren't available there.

**Defaults I picked (easy to change):** only `a`-`z` (leaving `A`-`Z` free for vim-style marks across files later), no `''` since `Backspace` already goes back, and no list of marks for now.

The plan also covers risks, the test list (including an end-to-end run in tmux) and three commits.

**Decision:** should I move the mouse-capture toggle from `m` to `M`? I recommend it: it's a rarely used toggle, and it keeps `m`/`'` working the way you asked, as in vim.

## Simulated user turn 1

APPROVED
Yes, move the mouse toggle to `M`. The plan is fine as written.

## Executor turn 2

The plan files are final and record your decision to move the mouse-capture toggle from `m` to `M`. I removed the open question, so the plan has nothing left unresolved.

- `.lavish/bookmarks.md`
- `.lavish/bookmarks.html`

I didn't implement anything.
