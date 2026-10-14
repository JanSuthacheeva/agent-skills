## Eval Prompt

/feature-dev:feature-dev i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've explored the codebase and have some findings to share before designing anything. A few of them affect the design directly.

## What I found

- **`m` is already used.** It turns mouse capture on and off (`src/viewer.rs:1647`, help entry at `src/viewer.rs:3637`). It's also missing from the README controls table, which is a separate small doc gap.
- **There's no support for two-key sequences.** `handle_normal` (`src/viewer.rs:1606`) handles one key at a time. Sequences like `m`+letter need a small "pending key" state. That state has to be cleared by `Esc` or any key that isn't a letter, and the status bar should show it (e.g. `m-`).
- **The scroll position is fragile.** `state.offset` counts lines after word-wrapping. It shifts when:
  - the terminal is resized or the width changes (`rebuild`)
  - images load and expand their placeholder rows (`finalize_layout`, `src/viewer.rs:605`)
  - the file is edited and auto-reloaded

  Saving that number as-is would make marks land in the wrong place, especially across sessions with a different terminal width. The renderer already receives each element's position in the source file (`into_offset_iter` in `src/markdown.rs:1585`) but throws it away. Recording a source line number on each rendered line would let marks point at the source text instead.
- **Persistence:** today mdterm only reads `config.toml`, using `dirs::config_dir`, and never writes anything to disk. Marks are state rather than config, so they belong in a data/state directory (`serde_json` is already a dependency).
- **Some existing pieces are relevant:**
  - `nav_history` with `Backspace` for going back after a jump (`src/viewer.rs:1765`)
  - multi-file switching
  - slide mode, which has its own key handler
  - the JSON viewer, which intercepts keys first
  - stdin input, which has no path to save marks under
  - help overlay tests that fail on duplicate keys

## Questions (my recommendation in brackets)

1. **The `m` conflict:** should I move mouse capture to `M` so `m` can set marks? [Yes. Move it to `M` and update the help and README.]
2. **What a mark points at:** should a mark point at a line in the source file, or just save the current scroll number? [Point at the source line. It survives resizes, image loading and different widths between sessions, and edits only nudge it. This means adding a source line number to rendered lines in `markdown.rs`.]
3. **What "position" means:** should jumping restore the same top line on screen? [Yes, the top line of the screen.]
4. **Letter scope:** should both lowercase and uppercase marks be per file, or should uppercase marks work across files like in vim? [Make all letters per file, as you described. Cross-file marks can come later.]
5. **How jumps fit with going back:** should `'`+letter be undoable with `Backspace`, and do you want vim's `''` to return to where you were before the last jump? [Yes to both. Both would use the existing `nav_history`.]
6. **Visibility:** should there be:
   - (a) a short message like "Mark a set" when you set or jump?
   - (b) the mark letter shown in the left margin?
   - (c) a list of all marks?

   [(a) and (b) now, with the list left for later. The margin is already 2 columns wide.]
7. **Storage:** one JSON file keyed by the file's full resolved path, written as soon as a mark is set. It would live in `dirs::state_dir()` (`~/.local/state/mdterm/marks.json` on Linux) and fall back to `dirs::data_dir()` on macOS. Should entries for files that no longer exist be cleaned up? [Yes, remove them when the file loads.]
8. **Edge cases:**
   - stdin: [marks work for the session only and aren't saved]
   - slide mode: [turn marks off for now]
   - JSON viewer: [turn marks off, because expanding and collapsing nodes moves lines around]
   - jumping to a mark that isn't set: [show "Mark 'x' not set"]
   - a mark whose line was deleted by an edit: [move it to the nearest valid line]

Once you answer, or confirm the bracketed defaults, I'll draft two or three ways to build it, recommend one, and write the plan as a lavish page plus Markdown under `.lavish/`.

## Simulated user turn 1

1. Yes, move mouse capture to `M`.
2. Source line, as you recommend.
3. Yes, top line of the screen.
4. Lowercase a-z only, per file. Uppercase isn't a mark for now, so no A-Z at all.
5. Yes to both.
6. (a) and (b) now, list later.
7. Yes to the JSON file in the state dir, with the data dir as the macOS fallback. Clean up entries for missing files. Keep it out of `config.toml`.
8. All your bracketed defaults are fine.

Go ahead with the approaches and the plan.

## Executor turn 2

I've written the plan: `.lavish/mdterm-bookmarks.html`, with a Markdown copy at `.lavish/mdterm-bookmarks.md`. Two architecture agents each drafted a design, and I checked their code references against the source.

**The decision is how to track source lines.**

- **A. Minimal (about 200 lines, 5 files).** Source line numbers are kept in separate lists alongside the rendered and wrapped lines, and must be kept aligned by hand whenever the layout changes. The weaknesses:
  - If they fall out of step, marks point at the wrong text with no error.
  - It adds to the 4356-line `viewer.rs`.
  - Marks don't move with the text when the file is edited and reloaded.
- **B. Clean, trimmed (recommended).** Each rendered `Line` carries its own `src` source line, so the row always knows where it came from. It stays correct through wrapping and image loading. `Line` already derives `Default`, so adding the field is a mechanical change at about 50 places. The code is split into layers:
  - `source_map.rs` and `marks.rs`: pure logic, easy to unit test.
  - `marks_store.rs`: reading and writing the JSON file.
  - `viewer/marks_ctl.rs`: a child module holding the viewer side, so `viewer.rs` grows by only about 30 lines.

  It also makes two fixes beyond the marks themselves. When the file is edited and reloaded, marks shift to follow the text. `Backspace` history uses source lines too, which fixes how it lands in the wrong place after a resize today.

**Trims to the full clean design:**
- No file lock. It would need `unsafe` system calls. Re-reading the file before each write and replacing it in one step already stops two running copies of mdterm from wiping out each other's marks.
- No preserving of unknown JSON fields. A `version` field is enough.
- The position `''` returns to lasts only for the session and isn't saved.

**Things that affect the design:**
- The pending `m` or `'` must be caught before the help-key check in `src/viewer.rs:999`. Otherwise `mh` opens help and `m` then Esc quits mdterm.
- A mark set in the middle of a paragraph jumps to the start of that paragraph. Code blocks are exact to the line.

**Design source:** the page uses mdterm's own dark and light theme colours from `src/theme.rs`, including the terminal mockups of the margin letters and the `m-` status bar. As instructed, I didn't open it in a browser, so it hasn't been checked visually.

**Decisions for you:**
1. Approach A or B trimmed? I recommend B.
2. Should this feature include moving marks with the text on reload (step 13) and keeping the same top line on resize (step 15), or should those be a follow-up? I recommend including both.
3. Skip the file lock as proposed? I recommend skipping it.

## Simulated user turn 2

APPROVED
Go with B trimmed, include steps 13 and 15 in this feature, and skip the file lock.

## Executor turn 3

I've updated both plan files with your three decisions. No code has been written, and I didn't open the page in a browser.

- `.lavish/mdterm-bookmarks.html` (the visual plan)
- `.lavish/mdterm-bookmarks.md` (the same plan as Markdown)

**What changed in them:**
- **Status:** marked as approved: option B trimmed, steps 13 and 15 included, no file lock.
- **Decisions table:** now lists the approach, the scope and the locking choice. Option A is marked rejected and B chosen.
- **Steps 13 and 15:** moving marks with the text on reload, and keeping the same top line on resize, are now regular build steps. They're no longer flagged as open.
- **Open questions:** the section is removed, since all three are answered.
- **Risks:** without a lock, two copies of mdterm saving marks at the same moment can lose one update. The file can't be corrupted, because each save replaces it in one step.

The plan has 15 steps, each meant to be one commit, and starts with moving mouse capture from `m` to `M`.
