## Eval Prompt

i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've written the plan to `.lavish/mdterm-bookmarks.html` and `.lavish/mdterm-bookmarks.md`. No code has been written yet.

**Two problems to solve first:**
- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`). `'` and `M` are both free.
- **The current scroll position can't be saved as a mark.** `state.offset` counts lines after wrapping, so it changes when the terminal is resized, an image loads, line numbers are toggled, or the file is edited. Next session's terminal width will usually differ too. Rendered lines don't record where they came from in the source, even though the parser hands the renderer that information (`src/markdown.rs:1585`).

**Proposed structure:**
1. **Record source positions on lines.** Add a source offset to each rendered line (`src: Option<usize>` on `Line`). Wrapped rows inherit it automatically. Code blocks get an exact position per line.
2. **New `src/marks.rs` with no UI code:**
   - A mark is stored as a source line number plus that line's text.
   - `anchor_at` turns the line at the top of the screen into a mark.
   - `resolve` runs at jump time. It uses the stored line if its text still matches. Otherwise it picks the nearest line with the same text, and as a last resort the same line number. Resizes, image loads and edits all go through this one path.
3. **Saving to disk (`MarkStore`):**
   - One JSON file at `~/.local/state/mdterm/marks.json` on Linux, or `~/Library/Application Support/mdterm/marks.json` on macOS, keyed by the file's full path.
   - It's written on every mark set, and only that file's entry changes, so two open mdterm windows don't overwrite each other.
   - Writes are atomic, so a crash can't corrupt it. A corrupt or unreadable file just means no marks, never a crash.
4. **Keys in the viewer:**
   - `m` or `'` waits for the next key. This check has to run before the help and JSON key handlers, otherwise `m h` would open help.
   - A letter sets or jumps; any other key cancels.
   - A jump is added to the existing back history, so Backspace returns you to where you were.
   - Works in slide mode. The status bar shows that it's waiting for a letter.

The plan also covers the test list (including a resize / relaunch / edit check run in tmux), a four-commit order, and risks. The HTML uses mdterm's own dark-theme colours from `src/theme.rs`.

**Decisions for you:**
1. Can mouse capture move from `m` to `M`? I recommend yes, since `m` for marks is the vim convention, but it will break muscle memory for existing users.
2. Allow only lowercase letters (`a-z`) and keep uppercase free for possible cross-file marks later, as in vim? Or allow `a-zA-Z`, all per file? I recommend lowercase only.
3. Leave JSON files out of v1? I recommend yes: JSON lines have no source positions, and expanding or collapsing nodes moves everything.

## Simulated user turn 1

1. Yes, move mouse capture to `M`.
2. `a-z` only.
3. Yes, leave JSON out of v1.

## Executor turn 2

I've updated both plan files (`.lavish/mdterm-bookmarks.html` and `.lavish/mdterm-bookmarks.md`) with your three answers. The open-questions section is now a "Decisions" section:

1. Mouse capture moves from `m` to `M`, and `m` becomes the mark key.
2. Only lowercase letters (`a-z`) work as marks. Uppercase stays free for possible cross-file marks later. Pressing an uppercase letter after `m` or `'` cancels, the same as any other key that isn't a mark letter.
3. JSON files are left out of v1. Pressing `m` or `'` there shows a short "Marks are not supported for JSON" message.

The rest of the plan is unchanged. The work is split into four commits:
1. Record each rendered line's position in the source file.
2. Turn a screen position into a mark, and a mark back into a position.
3. Save and load marks on disk.
4. Wire up the keys: the `M` rebind, the status-bar hint, and the help/README updates.

No code has been written yet. Tell me when you'd like me to start on the first commit.

## Simulated user turn 2

APPROVED
The plan matches my three answers and I have no further points.

## Executor turn 3

The final plan is in `.lavish/mdterm-bookmarks.html` and `.lavish/mdterm-bookmarks.md`, with your three decisions included. No code has been changed, and I'm stopping here.
