## Eval Prompt

/feature-dev:feature-dev i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've finished exploring. A few things in the codebase change how this should be built, so I need some decisions from you before I write the plan.

## How the relevant code works today

- **`m` is already taken.** In `src/viewer.rs:1647` it turns mouse capture on and off (so you can select text), and the help screen lists it (`src/viewer.rs:3637`). `'` is free.
- **There are no two-key commands yet.** Every key in `handle_normal` acts on its own. To support `m`+letter, the viewer needs a "waiting for the second key" state.
- **The scroll position isn't stable.** `state.offset` counts lines *after* word-wrapping. Resizing the terminal, changing `-w`, or toggling the theme or line numbers changes which text sits at a given offset. Saving that number to disk would send you to the wrong place next session.
- **Source positions are available but get thrown away.** `markdown.rs:1585` reads the source position of each element, but only task checkboxes keep it (`bracket_offset`). Each rendered `Line` could also keep its source line number, and wrapping already copies that data onto every wrapped piece.
- **There's no state storage yet.** `config.rs` only reads `config.toml`. `nav_history` plus Backspace already provide "go back to where I was".
- **Some views don't fit marks cleanly:** piped input from stdin (no file path), the JSON viewer (no markdown source lines) and slide mode (navigates by slide index).

## Questions

1. **The `m` conflict.** I recommend moving mouse capture to `M` so `m` works like vim. The alternative is a different key for marks, but that breaks the vim habit you're clearly building on.
2. **What a mark remembers.** I recommend saving the source line number of the top visible line. It survives resizes, width changes, and theme and line-number toggles, and edits only shift it by however many lines were added or removed above it. Alternatives:
   - Nearest heading plus an offset from it: handles edits better, but more complicated.
   - The wrapped line number: breaks as soon as you resize.
3. **Where marks are stored.** I recommend one file, `<data_dir>/mdterm/marks.toml`, keyed by each file's full absolute path, and saved right away whenever a mark is set (written safely so a crash can't corrupt it). Alternatively, saving only on quit loses marks if mdterm crashes. Is losing marks when a file is renamed or moved acceptable?
4. **Which letters.** Should `a-z` be per-file only? Should `A-Z` work like vim's global marks, which jump across files and open the file if needed? I recommend `a-z` per-file only for now.
5. **Jumping back.** I recommend recording the position before each jump in `nav_history`, so Backspace returns there. Do you also want vim's `''` (jump back to where you were before the last jump) and backtick as an alias for `'`?
6. **Feedback while typing a mark.** I recommend:
   - Show `m…` or `'…` in the status bar while waiting for the letter.
   - Esc or any non-letter cancels.
   - Toasts: "Mark a set" and "Mark x not set".

   Do you want a way to list marks (an overlay like the table of contents, or an entry in help), or leave that out of the first version?
7. **Special cases.** I recommend:
   - stdin: marks work but are lost when you quit.
   - Slide mode: jumping goes to the slide that contains the marked line.
   - JSON viewer: marks are turned off and a toast explains why.
   - A mark past the end of a shortened file goes to the end.

   Does that work for you?

Answer the ones you have opinions on and I'll take my recommendations for the rest. Then I'll design the approach and write the full plan to `.lavish/`.

## Simulated user turn 1

1. Yes, move mouse capture to `M` and use `m` for marks.
2. A source line number is fine for resizes, but marks need to survive small edits to the file too. Please pick something sturdier than a bare line number, such as the nearest heading plus an offset, or a line-content anchor. Your call on which.
3. Store marks in the platform state directory, not the data dir, and not in `config.toml`. Keying by absolute path and saving right away is fine, and losing marks on a rename or move is acceptable.
4. `a-z` per-file only, no global `A-Z` for now.
5. Go with your recommendation: record the position in `nav_history` before each jump. Skip `''` and the backtick alias.
6. Go with your recommendation, and leave the marks list out of the first version.
7. That works for me.

## Executor turn 2

I've written the plan to `.lavish/bookmarks.html`, with the same content in `.lavish/bookmarks.md`. I haven't written any code. The page uses mdterm's own dark and light colors from `src/theme.rs`, so the mockups look like the real viewer.

## Approach

- **How a mark stays on target:** each mark stores the source line number and that line's text. When you jump, mdterm finds the matching line in the file as it is now:
  - If the text is still on the same line, it jumps there.
  - If the line moved, it jumps to the nearest line with the same text.
  - If the marked line was edited, it falls back to the old line number, or the end of the file if the file got shorter.

  This handles edits anywhere except on the marked line itself, and works in files without headings, so I picked it over heading + offset.
- **Source line numbers on screen lines:** to know which source line is at the top of the screen, each rendered line gets a `source_line` field (in `style.rs`). Wrapping keeps it, and the renderer fills it in at one spot (`markdown.rs`). Rows inside code blocks are numbered individually, so marks there land on the exact line.
- **New `src/marks.rs`:** contains the matching logic (`Mark::capture` / `Mark::resolve`) and the storage (`FileMarks`). Marks are saved to `marks.toml` in the state directory. Each save re-reads the file and writes it atomically, so two sessions on different files don't overwrite each other's marks. If `marks.toml` is corrupt, it is never overwritten; marks still work for the session and the toast says they weren't saved.
- **Viewer changes:**
  - A "waiting for a letter" state is checked before the help key, so `m` then `h` sets mark `h` instead of opening help. One check covers both normal and slide mode.
  - While waiting, the status bar shows a `m_` prompt in the search prompt's style.
  - Jumping records your position in `nav_history`, so Backspace returns.
  - Mouse capture moves to `M`, and the help overlay, README and CLAUDE.md are updated. The README never listed the mouse capture key, so I'm adding it.
- **Four commits:** source line numbers, the marks module, moving mouse capture to `M`, then the bookmarks feature itself. Tests are in each step, plus a check in tmux that marks survive a restart after editing the file.

## Decisions needed

1. **State directory on macOS and Windows.** `dirs::state_dir()` only returns a path on Linux. I recommend falling back to `~/.local/state/mdterm/marks.toml`, which is where most command-line tools keep this on macOS. The only built-in alternative is `~/Library/Application Support`, which is the data directory you ruled out. One catch: `config.toml` on macOS already lives under `~/Library/Application Support/mdterm/`, so config and marks would end up in different places. OK?
2. **Go ahead with the build?** If the plan looks right, say so and I'll start in the commit order above.

## Simulated user turn 2

The `~/.local/state/mdterm/marks.toml` fallback on macOS and Windows is fine. I only wanted the plan in this conversation, so I'm not asking you to start the build.

APPROVED

## Executor turn 3

The plan is final, and I've stopped here without writing any code.

I updated both `.lavish/bookmarks.html` and `.lavish/bookmarks.md`:
- The state directory question is now marked decided: on macOS and Windows, marks go to `~/.local/state/mdterm/marks.toml`.
- They note that on macOS, `config.toml` and `marks.toml` will end up in different folders.
- They mark the plan as approved.

When you want it built, the plan has the full order: four commits, then the tests and a check in tmux.

## Simulated user turn 3

APPROVED

## Executor turn 4

Both plan files are written, and the only changes in the repo are those plan files plus the lavish skill folder in `.claude/` - no source files were touched.

- `.lavish/bookmarks.html`
- `.lavish/bookmarks.md`

Neither has any unresolved questions left. Both note that the state directory on macOS and Windows falls back to `~/.local/state`, and both mark the plan as approved.
