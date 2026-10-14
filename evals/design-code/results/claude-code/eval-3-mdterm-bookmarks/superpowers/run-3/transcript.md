## Eval Prompt

/superpowers:brainstorming i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

Here's what I found and my understanding so far.

**What you asked for**
- `m` + letter saves the current position under that letter.
- `'` + letter jumps back to it.
- Marks are saved per file and come back in the next session.

**What the code tells me**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`), and the README and help overlay document it that way. Something has to give.
- **The scroll position can't be saved as-is.** `state.offset` counts lines after word-wrapping. That count changes with terminal width, the `l` line-numbers toggle, the `width` config, loaded image heights, and edits to the file. A saved `offset = 412` would land somewhere else next session. A saved mark needs an anchor tied to the source text instead. The renderer already reads source byte ranges (`markdown.rs:1585`, `into_offset_iter`), so attaching a source line to each rendered line is doable. That's the main design work here, beyond the keybindings.
- **Nothing gets written to disk today.** `config.rs` only reads `~/.config/mdterm/config.toml`, so persistence is a new piece. Saved marks are state, not config, so they belong in a data directory (e.g. `dirs::data_dir()/mdterm/marks.toml`), not next to the config file.
- **A "jump back" history already exists.** `nav_history` and Backspace go back to where you were.

**My assumptions (please correct)**
- This is for long documents you come back to, like specs, notes, and books, where you want to return to the same passage even after the file was edited a bit or the terminal size changed.
- Vim-style: lowercase letters only, saved per file. Uppercase global marks that jump across files are out of scope.
- It only applies to Markdown files. JSON view and slide mode come later, if ever.
- A jump also pushes onto `nav_history`, so Backspace takes you back to where you jumped from.
- No list or overlay of your marks for now.

**Success means:** set a mark, quit, change the terminal width or edit some text above the mark, reopen, press `'a`, and you land on the same passage.

The first decision is the `m` conflict. Which do you prefer?

- **A.** Move mouse capture to another key (e.g. `M`) and give `m` to marks, like vim. This changes a documented binding, so the README and help need updating. **(my recommendation)**
- **B.** Keep `m` for mouse and use a different prefix for marks (e.g. `b` + letter). `b` is already PageUp, so it would have to be some other key.
- **C.** Something else you have in mind.

## Simulated user turn 1

Option A, move mouse capture to `M` and give `m` to marks. Your other assumptions look right to me, including the lowercase-only, per-file marks and keeping them in the data directory instead of config.

## Executor turn 2

Got it: `M` for mouse capture, `m` for marks, and your assumptions stand. The next decision is **what a mark stores**, so it still points at the same passage after the width changes or the file is edited.

For any of these, the renderer first has to record which source line each rendered line came from. That would be a new `source_line` field on `Line` (`style.rs:56`). The markdown renderer fills it in from the byte ranges it already reads, and `wrap_lines` copies it to each wrapped piece. A mark is saved in terms of the file, and converted to a scroll position only at jump time.

**1. Source line plus a text fingerprint (recommended)**
- A mark stores the source line number plus that line's trimmed text.
- On jump, if the line still has that text, go there. If not, look for the nearest line with the same text. If none is found, fall back to the stored line number, clamped to the end of the file, and show a "mark moved" toast.
- Width changes and line-number toggles have no effect. Edits above the mark are absorbed by the text match. Only rewriting the marked line itself loses the exact spot, and even then you land close.
- Cost: a small resolver function to unit-test, and slightly bigger entries in the marks file.

**2. Source line only**
- Simplest option, and width changes don't matter.
- But adding or removing lines above the mark makes it drift by that many lines. That fails your "edit a bit, reopen, land on the same passage" goal.

**3. Nearest heading plus an offset within its section**
- Holds up against edits in other sections.
- Imprecise in long sections, breaks when a heading is renamed, and does poorly in files with few headings.

I recommend 1. It's the only option that meets the success criterion, and the extra logic is one pure function that's easy to test.

Should marks use approach 1?

## Simulated user turn 2

Yes, approach 1. It matches what I want: marks should survive resizes and small edits to the file.

## Executor turn 3

Approach 1 it is. I'll go through the design in sections. **Section 1 covers the components and how data moves between them.**

**New module `src/marks.rs`.** It holds the mark logic and file I/O, with no terminal or viewer code.
- `Mark { line: usize, text: String }`: a 1-based source line plus that line's trimmed text.
- `MarkStore`: the marks file, keyed by the file's canonical absolute path, then by letter. Stored at `dirs::data_dir()/mdterm/marks.toml`.
- `resolve(&Mark, source: &str) -> Resolved { line, exact }`: a pure function that implements approach 1.
- `set(path, letter, mark)` re-reads the marks file, updates only that one entry, and writes it back atomically (temp file plus rename). Each save happens right away, so marks survive a crash, and two mdterm windows open at once don't overwrite each other's marks.

**`style.rs`:** `Line` gets `source_line: Option<usize>`, and `wrap_lines` copies it to every wrapped piece.

**`markdown.rs`:** the renderer builds a lookup table of where each source line starts once per render. When it starts a new output line, it stores the source line of the event that began it.

**`viewer.rs`, kept as thin glue:**
- `pending_mark: Option<MarkOp>` (`Set` or `Jump`). It's a single-key prefix, so it doesn't need a new `ViewMode`. The next key is always consumed. `a-z` runs the action, and any other key cancels quietly.
- **The marked position is the top of the screen,** since mdterm has no cursor. On set, it takes the `source_line` of the first visible line that has one.
- **Jump:** calls `resolve` on the current file, scrolls to the first wrapped line at or after the resolved source line, pushes the old position onto `nav_history`, and shows a "mark moved" toast if the match wasn't exact.
- `M` takes over mouse capture, and the help table is updated.

**Data flow:**
- Set: `m a` -> top visible line -> `source_line` -> `Mark` -> `MarkStore::set` -> disk.
- Jump: `' a` -> `MarkStore` -> `resolve` -> wrapped line index -> `offset`.

**When marks are off:** for stdin, JSON view and slide mode, `m`/`'` show a toast like "Marks unavailable for stdin" and do nothing else.

Does this structure look right before I move on to error handling and testing?

## Simulated user turn 3

Yes, the structure looks right. Go ahead with error handling and testing.

## Executor turn 4

**Section 2 covers error handling and testing.**

**Error handling.** Marks are a convenience, so no failure here should crash or block the viewer. Every failure shows a toast and the viewer keeps running.

| Situation | Behavior |
|---|---|
| Marks file missing | Treated as empty. The file and its directory are created on the first save. |
| Marks file can't be parsed | **Never overwritten.** Marks still work for the current session but aren't saved, and a toast says `marks.toml unreadable - marks not saved`. |
| No data dir, or the write fails | The mark is kept for this session. Toast: `Could not save mark: <reason>`. |
| `canonicalize` fails | Falls back to the path exactly as given. |
| `'x` when `x` isn't set | Toast: `Mark 'x' not set`. |
| Stored line is past the end of the file | Clamped to the last line, counts as not exact, and shows the "mark moved" toast. |
| Marked line is blank | Matched by line number only, because blank text would match any empty line. |
| Several lines have the same text | Uses the one closest to the stored line. On a tie, the earlier line wins. |
| File auto-reloads | Nothing to do, because marks are resolved only when you jump. |

Successful actions also get feedback: `Mark 'a' set` and `Jumped to 'a'`. Entries for files that no longer exist stay in the marks file. Cleaning them up is out of scope for now.

**Testing**
- **Unit tests in `marks.rs`:**
  - `resolve`: exact match, line moved down, line moved up, duplicate text resolving to the closest copy, missing text falling back and clamping, and blank lines.
  - `MarkStore`: takes its path as a parameter so tests can use a temporary directory (`tempfile` as a dev-dependency). Tests cover save then load, merging changes from two store instances, and a corrupt file left untouched.
- **`markdown.rs` and `style.rs`:** `source_line` is set correctly for headings, paragraphs, list items, code block lines and tables, and is still there after wrapping at narrow widths.
- **Viewer:** key-handling tests for set, jump, cancel on Esc or a non-letter key, `nav_history` being pushed, and the toasts for the "off" cases. The existing `help_sections_no_duplicate_keys` test will catch the `m`/`M` binding change.
- **End-to-end check** of the success criterion: drive the real binary in tmux with `HOME` pointed at a temporary directory, so your real marks file isn't touched.
  - Open `test.md`, press `m a`, quit.
  - Resize the pane and insert lines above the mark.
  - Reopen, press `' a`, and check that the same passage is at the top of the screen.

Does this look right? If so, I'll write the spec as a lavish page plus a Markdown copy under `.lavish/` and ask you to review it.

## Simulated user turn 4

Looks right, go ahead and write the spec.

## Executor turn 5

I've written the spec in two forms and committed both (`87dafbe`):

- **Review page:** `.lavish/mdterm-bookmarks.html`. It uses mdterm's own dark theme colors from `Theme::dark()` in `src/theme.rs`, so the mock terminal screens look like the real viewer.
- **Markdown:** `.lavish/mdterm-bookmarks.md`, with the same content.

**Added while writing it** (things we hadn't covered in chat):
- **Tables and code blocks:** they're output all at once at the end of the block, so by default every line would point back to the block's first line. Code lines will instead get `fence_line + 1 + i`. Table rows will record their own source line when the row starts.
- **Most source lines are set in one place:** in the `into_offset_iter` loop, any new line without a source line gets the line where its event started. That avoids changing each of the ~47 places that create a `Line`, which only need `source_line: None`.
- **Precision:** a mark set in the middle of a long paragraph jumps to the paragraph's first line. The spec lists this as an accepted limitation.
- **Docs:** the README key table and the CLAUDE.md file list (`marks.rs`, now eleven files) need updating.

**Notes:**
- Your CLAUDE.md asks for the `/commit` skill, but it isn't available in this session, so I committed with plain `git`.
- The `.claude/` folder in the repo is untracked and I left it alone.

Please review the spec and tell me if you want changes. Once you approve it, I'll write the implementation plan.

## Simulated user turn 5

One inconsistency in the plan as written: the mock screen in the review page shows the toast `Jumped to 'a'  (line 120 -> 125, matched by text)`. The spec text and the `.md` define it as just `Jumped to 'a'` when the match is exact, and `Mark 'a' moved - nearest position` otherwise. Please make the mock match the spec, or add the line-number detail to the spec if you want it.

Everything else looks fine. Once that's fixed, I'll approve.

## Executor turn 6

I fixed the mock to match the spec rather than adding line numbers to it. The jump example screen now shows only `Jumped to 'a'`, which is the toast for an exact text match. I searched both files and that line-number text no longer appears anywhere. The `.md` was already correct, so only the HTML changed, committed as `6ae84ed`.

I left the line numbers out on purpose. "Jumped" already tells you the passage was found, and "moved" tells you it wasn't. Showing line numbers would only matter if you were debugging the matching.

Once you approve, I'll move on to the implementation plan.

## Simulated user turn 6

APPROVED. The mock now matches the spec, so go ahead with the implementation plan.

## Executor turn 7

I've written the implementation plan in two forms and committed both (`fa0fb79`, plus `f3b7548`, which only replaces an em dash). No code has been changed.

- **Plan:** `.lavish/mdterm-bookmarks-plan.md` has the full TDD steps with exact code, test code, commands and commit messages.
- **Review page:** `.lavish/mdterm-bookmarks-plan.html` shows the task order, review focus, task cards and execution choice. It uses the same mdterm theme colors as the spec page.

**The six tasks, one commit each:**
1. **`source_line` on `Line`:** add the field, copy it through wrapping, and update the ~47 places that create a `Line`.
2. **Renderer fills it in:** each line gets the source line where its content starts, with one line per code line and per table row.
3. **`resolve`:** 11 unit tests.
4. **`MarkStore`:** saves by re-reading, updating one entry, and writing atomically. An unreadable file is never overwritten. 7 tests, with `tempfile` added as a test-only dependency.
5. **Viewer:** the `m`/`'` prefix, set and jump, `M` for mouse capture, and help entries. 13 tests.
6. **Docs and end-to-end check:** README and CLAUDE.md updates, then the real binary in tmux with `HOME` pointed at a temp directory.

**Five cases the spec implies but doesn't test.** Each now has its own test:
- `Ctrl+c` while a mark prefix is pending still quits.
- `q` or `Esc` while a prefix is pending only cancels it.
- A mark set in one file doesn't exist in another file opened alongside it.
- CRLF line endings don't break the text match.
- An empty document shows `Nothing to mark here` instead of panicking.

**Where the plan differs from the spec:**
- **New toast:** `Nothing to mark here`, for the empty-document case above.
- **File layout:** `toml` may write `marks.toml` with `["path".a]` table headers rather than the spec's inline tables. The data is the same; tests only check that marks survive a save and reload.
- **Merge after save:** after a successful save, marks other mdterm windows wrote to disk are also loaded into memory.

**Unverified risk:** I haven't run anything, so the plan relies on two library behaviors I haven't confirmed. The plan's tests will catch either one if it's wrong:
- `pulldown-cmark` reports a code block's start position on the fence line.
- `toml` can write the nested map without errors.

Please review the plan and pick how to run it:
- **Subagent-driven (my recommendation):** a fresh implementer and reviewer for each task, then a review of the whole branch. Task 5 depends on the interfaces from Tasks 1-4, and Task 1 touches many files, so a review after each task catches mismatches early.
- **Native:** I implement all six tasks in this session, then one fresh reviewer checks the whole branch. Cheaper and faster, but nothing is reviewed independently until the end.
