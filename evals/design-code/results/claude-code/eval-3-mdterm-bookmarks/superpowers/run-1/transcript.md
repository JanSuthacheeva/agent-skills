## Eval Prompt

/superpowers:brainstorming i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

Context gathered. Here is what I found and what I understand so far.

**What you said**
- `m{a-z}` sets a mark at the current position, `'{a-z}` jumps to it.
- Marks are saved per file and survive restarts.

**What I'm assuming (please correct)**
- The goal is to find your place again in long docs you come back to (specs, notes, READMEs), so a mark has to land in the same place even after the file is edited or the terminal is resized.
- Only real files get marks. Stdin input gets none, or session-only ones.
- Marks are local to each file, like vim's lowercase marks. No marks that jump between files.

**Three things in the code that shape the design**
1. **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`, and it's listed in the help overlay at `:3637`). We need to settle that conflict first.
2. **Scroll position won't hold up as a mark.** `state.offset` counts wrapped lines, so it changes when the width changes, when line numbers are toggled (`l`), when images expand, and when the file is edited. A saved mark has to be tied to the source text instead, for example a source line plus some nearby text to re-locate it. The renderer can already see source byte ranges (`into_offset_iter` in `markdown.rs:1585`), but `Line`/`LineMeta` don't carry them through yet.
3. **Marks need their own storage, separate from `config.toml`.** That file holds settings the user edits by hand, while marks are app-written state. That points to a new module, something like `marks.rs`, saving to a separate state file keyed by canonical file path.

Because of point 2 and the new storage, I'm treating this as **architectural**: written spec first, then an implementation plan. Tell me if you'd rather go lighter.

**First question - what to do about `m` and mouse capture?**

- **A.** Make `m{letter}` the mark command and move mouse capture to another key, like `M`. This matches vim, but anyone used to `m` for mouse will find it changed.
- **B.** Make `m` a prefix key. `m` followed by a letter sets a mark, and `m` followed by something else (Esc, or a short timeout) still toggles mouse capture. Nothing moves, but the old toggle becomes awkward and a bit magical.
- **C.** Keep `m` for mouse and put marks on another key. This doesn't match what you asked for.

I recommend **A**. It's the simplest and clearest. Vim users will expect `m` to set marks, and the mouse toggle is used rarely enough to move to `M`.

## Simulated user turn 1

A, move mouse capture to `M`. Your other assumptions are fine too: marks are per file, local, and need to survive edits and resizes.

## Executor turn 2

Settled: `m{a-z}` sets a mark, `M` toggles mouse capture (nothing else uses `M`).

**Next question - how hard should a mark try to stay in place when the file is edited?**

Any approach stores where the mark sits in the source file. The difference is what happens when you edit text above it.

- **A. Source line number only.** Simplest, but the mark drifts: add 10 lines above it and it now points 10 lines too high. External edits happen all the time with auto-reload, so this breaks the "survives edits" goal.
- **B. Source line + text fingerprint.** Store the line number plus a short snippet of that line's text, trimmed and normalized. On load or reload, look for the snippet near the stored line. If it's found, the mark moves with it. If not (the line was rewritten or deleted), fall back to the stored line, clamped to the file length. Handles the common case (edits elsewhere in the file) and fails gracefully.
- **C. Heading-relative anchor.** Store the nearest heading text plus the distance in lines below it. Very robust when sections get moved around, but it depends on heading text being unique and adds a second resolution step. Docs without headings lose the benefit.

I recommend **B**. It's one small rule, it covers the edits that actually happen, and when it misses it lands somewhere reasonable instead of failing.

A related detail: the position is the **top line of the viewport**, so `'a` restores exactly the view you had. That matches how `offset` and `nav_history` already work. Objections to either?

## Simulated user turn 2

B, and top line of the viewport is fine. Marks should be a-z only, per file, no global A-Z for now.

## Executor turn 3

Recorded: lowercase `a-z` only, each file has its own set, no global marks.

**Next question - which extras are in scope?** Each is small on its own, but I want the scope decided before the design.

1. **Jumps join back-navigation.** Before `'a` jumps, push the current position onto the existing `nav_history`, so `Backspace`/back takes you to where you were. Almost free, and consistent with how link jumps already work.
2. **Feedback.** A toast on set ("Mark a set") and on a miss ("Mark a not set"). Also a small indicator in the gutter or status bar on lines that have a mark.
3. **Mark list overlay.** `'` followed by `'`, or a dedicated key, opens a picker listing the file's marks with line previews, like the TOC/link picker.
4. **Delete marks.** For example `dm{letter}`, or a key inside the list overlay. Without it, the only way to "delete" a mark is to overwrite it.
5. **Slide mode and JSON files.** Either support marks there or disable them, with a toast explaining why.

My recommendation for v1: **1 yes, 2 toasts only (no gutter indicator), 3 no, 4 no, 5 disabled with a toast.**
- Item 1 costs nothing and uses an existing pattern.
- A gutter indicator affects every line render and the line-number layout, so it deserves its own design.
- Items 3 and 4 can come later without reworking anything.
- Slide mode and the JSON viewer don't use wrapped markdown lines, so there's no source-line anchor to store.

Agree, or change any of these?

## Simulated user turn 3

Agreed on all five: 1 yes, 2 toasts only, 3 no, 4 no, 5 disabled with a toast.

## Executor turn 4

Scope is locked. Now the main structural choice, which is how the viewer learns which **source line** sits at the top of the viewport.

**Approach 1 (recommended) - Carry source lines through the render pipeline.**
- Add `source_line: Option<usize>` to `Line`.
- `Renderer` sets it from the byte ranges `into_offset_iter` already provides. Each emitted line gets the source line of the block that produced it.
- `wrap_lines` copies it to every wrapped piece.
- Both directions then become simple lookups over `wrapped`:
  - position to mark: `wrapped[offset].source_line`
  - mark to position: the first wrapped line whose `source_line` is at or after the target
- It's exact and cheap. It works the same after resizes, line-number toggles, and image expansion, because all of those happen after the source line is attached.
- Cost: touches `style.rs` (field plus wrapping) and every place `markdown.rs` emits a `Line`.

**Approach 2 - Map rendered text back to the source after the fact.**
- Leave the renderer alone. On set, take the plain text of the top visible line and search the source for it.
- No pipeline changes, but it's fragile. Markdown syntax is stripped (`**`, links, list markers), wrapped pieces are partial, and repeated text is ambiguous. That's a lot of guessing that's hard to test.

**Approach 3 - Store the wrapped offset plus the render parameters.**
- Save `offset` with the width and line-number state, and re-render with those settings to translate.
- Handles resizes, but **fails the edit requirement**. Mentioned only to rule it out.

**Approach 1** is the right one. It's the only one that's exact, and the source-line field will be useful later (gutter indicators, the mark list, "open in editor at line").

How the pieces fit with Approach 1:
- **`src/marks.rs` (new)** - two independent parts:
  - **Pure anchor logic**, unit-tested without a terminal:
    - `Anchor { line, snippet }`
    - `Anchor::capture(source, line)`
    - `Anchor::resolve(source) -> line`, which searches outward from `line` within a fixed window for the snippet, otherwise clamps
  - **`MarkStore`**, which loads and saves `marks.json` in the platform state dir (`dirs::state_dir()`, falling back to `dirs::data_local_dir()`, since macOS has no state dir). Data is keyed by canonical file path, mapping each letter to an `Anchor`.
- **`viewer.rs`** - new `pending: Option<PendingKey>` field (`SetMark` or `JumpMark`), consumed at the top of `handle_normal`; `m` moves to `M`; the help overlay is updated.

Does Approach 1 work for you? If so, next I'll go through the design in sections, starting with anchoring and rendering.

## Simulated user turn 4

Approach 1 works. Platform state dir with the fallback is fine, and keeping it separate from config.toml is what I wanted. Go ahead with the design sections.

## Executor turn 5

## Section 1 of 4 - Source lines through rendering

**Data type (`style.rs`).** `Line` gets a new field, `source_line: Option<usize>` (0-based, `None` for synthetic lines). Rust needs every `Line { .. }` literal to list the new field, and there are about 51 of them in `markdown.rs`, `style.rs`, `json.rs` and `viewer.rs`. I'll add `Line::new(spans, meta)` and switch the call sites to it, so the field is set in one place instead of being repeated everywhere.

**Stamping (`markdown.rs`).** One rule, applied in one place: the code that feeds parser events to the `Renderer` notes `lines.len()` before each `process(event, range)` call. Afterwards, any new line whose `source_line` is still `None` gets the line number of `range.start`. A line index is built once per render and looked up with binary search to turn byte offsets into line numbers. Most event handlers need no changes.
- **Code blocks** are the exception. `emit_code_block` runs on `End(CodeBlock)`, and its range starts at the opening fence, so the rule above would pin every code line to the fence. Instead `emit_code_block` sets `fence_line + 1 + i` for each line. That matters because long code blocks are exactly where people leave marks.
- Paragraphs and table rows stay at block level. A mark inside a long paragraph lands on the paragraph's first line, which is at most a few rows off. That's fine for v1.

**Wrapping (`style.rs`).** `wrap_lines` copies `source_line` to every wrapped piece, including blockquote pieces. That differs from `meta`, which is only copied to some pieces on purpose. Here every visual row should know where it came from.

**Image rows (`viewer.rs` `finalize_layout`).** The expanded image rows get the placeholder's `source_line`.

**JSON (`json.rs`).** Always `None`, because marks are disabled there.

**Two lookups on `ViewerState`:**
- `source_line_at(offset)` returns `wrapped[offset].source_line`. If that's `None`, it walks forward to the next line that has one.
- `offset_for_source_line(n)` returns the first wrapped index whose `source_line >= n`, clamped to `max_offset()`.

Does this section look right?

## Simulated user turn 5

Looks right. Go on to the next section.

## Executor turn 6

## Section 2 of 4 - `src/marks.rs`

This module never touches the terminal. It has two parts.

**`Anchor { line: usize, snippet: String }`** (serde-serializable)
- `Anchor::capture(source, line)` stores the line number and that source line trimmed, cut to 80 characters (on a character boundary).
- `Anchor::resolve(&self, source) -> usize`:
  1. If `line` is in range and the trimmed text at `line` matches `snippet`, return `line` (fast path).
  2. Otherwise search **outward from `line` over the whole file**, alternating `line-1`, `line+1`, `line-2`, ... and return the nearest exact match. If two matches are equally close, the earlier one wins. Searching the whole file rather than a fixed window means a big insertion above the mark still resolves. Nearest-first means repeated lines like `---` or a closing fence pick the copy closest to the original.
  3. If there's no match, or the snippet is empty, return `line.min(last_line)`.
- **Healing:** when a jump resolves to a different line, the viewer saves the updated anchor. A mark keeps following its text as the file changes over time instead of relying on an old line number.

**`MarkStore`**
- Data: `BTreeMap<String, BTreeMap<char, Anchor>>`, keyed by canonical path (the `BTreeMap`s keep the file order stable, which makes it easy to diff).
- Location: `dirs::state_dir()` or else `dirs::data_local_dir()`, then `/mdterm/marks.json`. On macOS that's `~/Library/Application Support/mdterm/marks.json`.
- Format is pretty-printed JSON with a version field, using `serde_json`, which is already a dependency:
  ```json
  { "version": 1, "files": { "/abs/notes.md": { "a": { "line": 41, "snippet": "## Rollout" } } } }
  ```
- API:
  - `load() -> Self` for normal use
  - `at(path) -> Self` so tests can use a temp dir
  - `get(file, letter) -> Option<&Anchor>`
  - `set(file, letter, anchor) -> io::Result<()>`
- **`set` writes through immediately.** It re-reads the file from disk, merges in only this one entry, writes to `marks.json.tmp` and renames it into place. With two mdterm instances open, neither erases the other's marks; for the same file and letter, the last write wins. The rename means a crash can't leave a half-written file.
- No pruning of deleted files in v1. Each entry is tiny, and pruning would wipe marks for files on drives that are temporarily unmounted.

The module has no dependency on `viewer.rs`. The viewer only calls `capture`, `resolve`, `get` and `set`.

Does this look right?

## Simulated user turn 6

Looks right. Go on to the next section.

## Executor turn 7

## Section 3 of 4 - Viewer integration

**New `ViewerState` fields:**
- `marks: MarkStore`, loaded once in `ViewerState::new`
- `pending: Option<PendingKey>`, where `enum PendingKey { SetMark, JumpMark }`
- `mark_file: Option<String>`, the canonical path of the current file. It's computed in `new()` and in `switch_file()`, and is `None` for stdin.

**The pending key has to be checked before the help toggle.** `handle_event` runs `is_help_toggle` *before* `handle_normal` (`viewer.rs:999`), so if the pending key were handled inside `handle_normal`, `mh` or `'h` would open the help overlay instead of setting or jumping. So in `handle_event`, right after the Ctrl-C check:
- If `pending` is set, call `handle_pending_mark(state, key)` and return. Every key is swallowed here:
  - `a-z` (without Ctrl) performs the action.
  - Anything else, including Esc, silently cancels. This matches vim.
  - Ctrl-C still quits, because its check runs first.

**Entering the pending state** happens in `handle_normal`, *before* the slide-mode and JSON early returns:
- `m` or `'` (without Ctrl) checks `marks_unavailable()`, which returns a reason:
  - "Marks unavailable in slide mode"
  - "Marks unavailable for JSON"
  - "Marks unavailable for stdin"
- If there's a reason, show it as a toast. Otherwise set `pending`.
- The old `m` arm becomes `M`. The help overlay entry changes to `("M", "Toggle mouse capture ...")` and gains two lines: `("m a-z", "Set mark")` and `("' a-z", "Jump to mark")`.

**Set** (`m{c}`):
1. `line = source_line_at(offset)`, then `anchor = Anchor::capture(&content, line)`.
2. Call `marks.set(file, c, anchor)`.
3. Toast "Mark c set". If saving fails, toast "Mark c set (not saved: {err})". The mark is still kept in memory for the session.

**Jump** (`'{c}`):
1. If there's no anchor, toast "Mark c not set".
2. Otherwise compute `resolved = anchor.resolve(&content)`, then `target = offset_for_source_line(resolved)`.
3. If `target != offset`, push `(current_file_idx, offset)` onto `nav_history`, so `Backspace` goes back as it already does for links. Then set `offset = target`.
4. If `resolved != anchor.line`, save the healed anchor (write errors are ignored here).
5. There's no toast on a successful jump, since the view moving is the feedback.

**Auto-reload, resize, line-number toggle:** nothing to do. Anchors are always resolved against the current `content` at the moment you jump, and `source_line` survives every rebuild.

Does this look right?

## Simulated user turn 7

Looks right. Go on to the next section.

## Executor turn 8

## Section 4 of 4 - Error handling and testing

**Error handling.** The rule: marks must never crash the viewer or quietly destroy data.

| Situation | Behavior |
|---|---|
| No state or data dir can be found | Marks work for the session only. The first `m` shows the toast "Mark a set (not saved: no state directory)" |
| `marks.json` is missing | Start with no marks. `set` creates the directory with `create_dir_all` |
| `marks.json` won't parse | Rename it to `marks.json.corrupt` and start fresh. The next toast says so. Nothing gets overwritten blindly |
| `version` is newer than this build understands | The store is **read-only**: marks work for the session but are never written, so older binaries can't damage data written by newer ones |
| Write or rename fails | The mark stays in memory. The toast includes the error |
| `canonicalize` fails (file was deleted after opening) | Use the path as given |

**One small change to Section 3:** `main.rs` creates the `MarkStore` and passes it in through `ViewerOptions`, instead of `ViewerState::new` loading it itself. Then tests can pass `MarkStore::at(tempdir)` and never touch your real marks. I'll add `tempfile` as the repo's first dev-dependency.

**Tests**
- **`marks.rs` unit tests:**
  - `capture`: trimming, and cutting at 80 characters without splitting multi-byte text
  - `resolve`: exact match; text shifted down or up; a large insertion above; nearest of several duplicates, with the earlier one winning ties; line deleted (clamped); empty snippet; empty file
  - Store: save and reload; two `MarkStore`s on the same path keep each other's marks; no `.tmp` file left behind; corrupt file moved aside; future version is read-only
- **`markdown.rs` / `style.rs` tests:** `source_line` is set correctly for headings, paragraphs, list items, table rows, and each line of a code block; wrapping copies it to every piece, including blockquotes.
- **`viewer.rs` tests**, using the existing `make_state_with_lines` helper:
  - `ma` then `'a` round-trips the position
  - `mh` and `'?` set and jump instead of opening help
  - Esc cancels a pending `m`
  - jumping pushes onto `nav_history`, and `Backspace` returns
  - `M` toggles mouse capture
  - `m` shows the "unavailable" toast in slide mode, for JSON, and for stdin
  - the position holds after changing the width and after toggling line numbers
- **End-to-end check in `tmux`, run as a real user would.** `HOME` points at a temp dir so your real marks aren't touched:
  1. Open a fixture, scroll to a heading, press `ma`, quit.
  2. Insert 30 lines at the top of the file and reopen it at a different width.
  3. Press `'a` and confirm with `capture-pane` that the heading is the top line.
  4. Edit the file while it's open (auto-reload), then `'a` again.

Does this section look right? If it does, I'll write the full spec, which per your setup goes in `.lavish/` as both Markdown and an HTML page, and then send it to you for review.

## Simulated user turn 8

Looks right. Go ahead and write the full spec.

## Executor turn 9

I've written the spec as Markdown and as an HTML page. I haven't opened the page, and nothing is committed yet. Your instructions say to commit with the `/commit` skill, but it isn't available in this session. Should I commit with plain `git` instead, or leave it?

- **Markdown:** `.lavish/mdterm-bookmarks.md`
- **HTML:** `.lavish/mdterm-bookmarks.html`. It uses mdterm's own dark and light colors from `src/theme.rs`, since that's the closest thing the project has to a design system. It includes diagrams of the render pipeline, the outward search on jump, and the key-handling order, plus terminal mockups of the new toasts and help entries.

**Three changes since the sections you approved**, all found while checking the code:

1. **List items would have been stamped with the wrong line.** They are only flushed when the next item starts (`src/markdown.rs:1101`), so the simple per-event rule from Section 1 would give each item the next item's line. The spec adds a rule ahead of it: a line built up from text pieces takes the source line of its first piece. Code rows still get one line each, and everything else keeps the per-event rule.
2. **Tables now resolve to their first row**, like paragraphs. The whole table is emitted at once at its end, so per-row lines would need extra work in `emit_table`. I left that for later.
3. **Warning toasts (new scope, please confirm).** The toast renderer puts `✓` in front of every message (`src/viewer.rs:3023`), so "Mark q not set" would show with a check mark. The spec adds `set_warning`, which shows a `!` in a new `toast_warning` theme color. It also moves the existing "Invalid JSON" toast over to it.

Two smaller additions:
- The README key table gets the new keys. It never listed the mouse-capture key in the first place.
- Unreadable or newer-version `marks.json` files are now handled explicitly: an unreadable file is moved to `marks.json.corrupt`, and a file from a newer version is treated as read-only.

Please review the spec and let me know what you'd like changed, including whether to keep the warning toasts. Once you approve it, I'll write the implementation plan.

## Simulated user turn 9

APPROVED. Keep the warning toasts, and leave the spec uncommitted for now.

## Executor turn 10

The bookmarks plan is finished. Both files are written and marked approved, with the warning toasts kept:

- `.lavish/mdterm-bookmarks.md`
- `.lavish/mdterm-bookmarks.html`

As you asked, they're uncommitted (`.lavish/` shows as untracked in git), and I haven't changed any code. I'm stopping here.
