## Eval Prompt

/code-design i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've written the approaches page to `.lavish/bookmarks-approaches.html`. I need two decisions from you before I design the code in detail.

**Two things in the code shape the design:**

- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`, help text at `:3637`), so one of the two has to move. `m` is also missing from the README's controls table, which I'd fix in the same change.
- **A scroll position can't be saved as-is.** `state.offset` counts lines after word-wrap at the current width, with image rows expanded. Open the file tomorrow in a narrower terminal, or toggle line numbers, and a saved offset points somewhere else.

**The three approaches:**

| | What a mark remembers | Where the code lives | Cost |
|---|---|---|---|
| **A** | The current scroll offset | All in `viewer.rs` | Smallest change, but wrong after reopening at another width. It doesn't meet the "persist between sessions" requirement. |
| **B** | Nearest heading above, plus a line count below it | New `marks.rs`; the renderer is unchanged | Still drifts with width inside long sections, and falls back to A when a document has no headings. |
| **C (recommended)** | The line in the markdown file | New `marks.rs`; `Line` gains a source-position field set by `markdown.rs`, which wrapping copies to every wrapped piece | Exact at any width or setting. Biggest diff: about 50 places that build a `Line` across `markdown.rs`, `json.rs` and `style.rs`. |

C copies something the code already does: task checkboxes carry their position in the source file from the renderer to the viewer (`TaskItem.bracket_offset`, `src/style.rs:42`). The extra cost is mechanical edits, and since you care more about quality than development cost, I think it's worth it.

B and C share these defaults, which go on the assumptions list next round:
- Marks are saved to `dirs::data_dir()/mdterm/marks.toml`, keyed by the file's full path.
- Each `m`+letter is written to disk straight away.
- Documents read from stdin get marks for the current session only.

**Please answer:**
1. **Approach:** A, B, C, or a mix?
2. **Mouse capture:** move it to `M` so `m` sets marks, as in vim and less (my recommendation)? Or keep `m` for the mouse and pick another key for setting marks?

After that I'll build the implementation page with signatures, call chains and test seams.

## Simulated user turn 1

1. Approach C.
2. Move mouse capture to M, so m sets marks.

## Executor turn 2

I've written the full design to `.lavish/bookmarks-implementation.html`. It has signatures only, no method bodies, and I checked the file references it cites against the code. Two questions need your answer, then approval; after that I'll write the Markdown plan to `.lavish/bookmarks.md`.

**How it works:**
- **A mark is a source line.** Each rendered `Line` gets a new `source_line: Option<usize>` field. The renderer fills it in at one place, right after it handles each parser event, using the byte positions the parser already reports. Word-wrapping and image-row expansion copy it to every piece. A mark stores that number, so it points to the same text at any terminal width, theme or line-numbers setting.
- **Inside code blocks marks are exact to the line.** For paragraphs, list items and tables a mark returns to the start of the block.
- **`src/marks.rs` (new) handles saving and loading.** `MarkStore` has `open`, `at`, `load` and `save`, and the mark data is `FileMarks` and `Mark`. It writes `marks.toml` in the platform data folder (`~/Library/Application Support/mdterm/` on macOS), keyed by the file's full path. Each save re-reads the file, replaces only the current document's entry, and writes via a temp file and rename. If the existing file is corrupt, it refuses to overwrite it.
- **`viewer.rs` handles the keys.** A `pending_mark: Option<MarkAction>` field remembers that `m` or `'` was pressed. `handle_event` hands the next key to the new `handle_mark_key` before the help-toggle check, so `m` followed by `Esc` or `?` just cancels instead of quitting or opening help.
- **Jumping and history.** A jump records your position in the existing Backspace history first, so Backspace takes you back.
- **The `MarkStore` is created in `main`** and passed in through `ViewerOptions`, so tests can point it at a temp file.
- **Status bar and other keys.** While a key is pending, the status bar shows a hint. Mouse capture moves to `M`, and the help text, README and CLAUDE.md are updated to match.

**What it costs:**
- About 50 places that build a `Line` need the new field. These are mechanical edits in `markdown.rs`, `json.rs` and `style.rs`.
- It adds `tempfile` as a dev-dependency. No test writes to disk today.

The page also lists 15 assumptions, one line each, for you to confirm or overturn. Among them: the mark is the top line of the screen, marks do nothing in slide mode, the JSON view shows a toast instead, and stdin documents get marks for the session only.

**Please answer:**
1. **What should uppercase `A`-`Z` do?** I recommend treating them as invalid for now and keeping them for possible vim-style marks that work across files later. The alternatives are extra letters per file, or building cross-file marks now.
2. **What happens when the file is edited outside mdterm?** Marks drift if lines are added above them. I recommend accepting that for now, as vim does; `Mark` is a struct, so a text fingerprint to re-find the line can be added later. The alternative is adding that fingerprint now.

Tell me your answers and any changes to names, signatures or assumptions.

## Simulated user turn 2

1. Uppercase: reserve A-Z, treat as invalid for now. Marks are a-z only, per file.
2. Edits outside mdterm: marks should survive small edits to the file, so add the text fingerprint and re-anchor on jump now. Accepting drift contradicts that.

## Executor turn 3

I've updated `.lavish/bookmarks-implementation.html` with both decisions. The changed parts are tagged "Round 2" on the page, and both open questions are removed. The inline script still passes a syntax check, and the method names used in the call chains match the unit cards.

**1. Marks are `a`-`z` only, per file.** `A`-`Z` cancel silently, like any other invalid key.

**2. Each mark stores the text of its line and re-finds it on jump.** This all lives in `marks.rs` as functions of the source text, with no disk or UI code:

```rust
pub struct Mark { pub source_line: usize, pub fingerprint: String }
pub enum MarkTarget { Unchanged(usize), Moved(usize), NotFound(usize) }

impl Mark {
    pub fn capture(source: &str, source_line: usize) -> Mark;
    pub fn resolve(&self, source: &str) -> MarkTarget;
}
```

- **Setting a mark:** the fingerprint is the marked source line with whitespace trimmed, capped at 120 characters.
- **Jumping:** `resolve` checks whether the stored line still has that text.
  - If it does, the jump goes there.
  - If not, it searches the whole file and picks the matching line nearest the stored position (the line above wins a tie), so a repeated line like `- [ ] todo` resolves to the right copy.
  - If no line matches, it jumps to the stored line and shows the toast "Mark 'a': text changed, jumped to saved line".
- **Keeping marks current:** when a mark has moved, the jump also saves the new line number, so later edits start from the corrected spot. A mark whose text can't be found is left unchanged, so it can re-anchor if the text comes back.
- **Saving:** a new `ViewerState::save_marks` does the saving for both setting and jumping, and is a no-op for stdin.

Tests are added for both: unit tests for `capture` and `resolve`, plus a scripted `tmux` run that inserts lines above a mark, reopens the file and checks the jump.

**Limits to confirm** (also on the assumptions list):
- **Exact match only.** Adding or deleting lines anywhere is handled. If you reword the marked line itself, the mark falls back to its saved line with a toast. There is no fuzzy matching.
- **Only on jump.** Marks are re-checked when you jump, not when the file loads or reloads.
- **Blank lines never move.** A mark on a blank line, such as an empty line in a code block, has no text to match and stays put.

If this looks right, approve and I'll write the Markdown plan to `.lavish/bookmarks.md`; otherwise tell me what to change.

## Simulated user turn 3

APPROVED
The design matches my answers on approach, `M` for mouse capture, a-z only per file, and fingerprint re-anchoring.

## Executor turn 4

I've written the final plan to `.lavish/bookmarks.md`, so a later session can implement it without the browser. The review page stays at `.lavish/bookmarks-implementation.html` and the approaches comparison at `.lavish/bookmarks-approaches.html`. I didn't write or change any source code.

The Markdown plan contains:
- the decisions from both review rounds
- each unit's file path and Rust signatures
- the data types and the `marks.toml` format
- the four call chains (set, jump, load, render), with their error paths
- the test plan and the 18 assumptions

It leaves out the page's diagrams, rationale and file-reference citations.

I used `.lavish/` instead of the usual `docs/plans/` because your instructions for this session asked for it there. As instructed, I didn't run `lavish-axi end`.
