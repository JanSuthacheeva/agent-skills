## Eval Prompt

/feature-dev:feature-dev i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I surveyed the codebase myself rather than sending explorer agents, since the relevant parts fit in `viewer.rs` and `config.rs`. Before I design the architecture, a few things need your decision.

## What matters in the code

- **`m` is already taken.** It toggles mouse capture (`src/viewer.rs:1647`) and is listed in the help screen (`src/viewer.rs:3637`) and the README. `'` is free.
- **Scroll position won't survive between sessions.** `state.offset` counts lines *after* word wrapping. It changes on resize, with the `l` line-number toggle, with `width`, as images load (`finalize_layout` resizes image rows) and when the file changes on disk. A saved offset would point to the wrong place the next time you open the file.
- **The renderer already knows where each line came from, but throws it away.** It reads `into_offset_iter()` source positions (`src/markdown.rs:1585`), but `Line` keeps only `spans` and `meta`. To save marks in a form that survives width changes, each `Line` needs to carry its source line number through wrapping and image expansion.
- **There is a back-navigation stack.** `nav_history` is a list of (file, offset) pairs that Backspace pops (`src/viewer.rs:1765`). Mark jumps can reuse it.
- **Nothing is saved between sessions today.** `config.rs` only reads `config.toml`.
- **Keys are handled per mode.** Slide mode (`handle_slide_keys`) and the JSON explorer (`handle_json_keys`) each catch keys before Normal mode. A two-key sequence needs a small "waiting for a letter" state, plus a hint in the status bar while it waits.

## Planned structure

- **New `src/marks.rs`:** a store that holds marks for every file, keyed by the file's full path. It's saved as one file under `dirs::state_dir()`, falling back to `dirs::data_dir()`, at `mdterm/marks.json`. Each new mark re-reads that file, updates it and writes it back atomically, so two mdterm windows don't overwrite each other's marks.
- **`Line` gets a source line number**, which wrapping and image expansion copy along.
- **A mark stores the source line at the top of the viewport.** There's no cursor, so the top visible line is the position.
- **Jumping goes to the first rendered line from that source line or later**, and adds an entry to `nav_history`.

## Questions (my recommendation in brackets)

1. **The `m` conflict.** Move mouse capture to `M` and give `m` to marks? Or keep `m` for mouse and use another key for marks? [Move mouse capture to `M`: `m`/`'` is the vim convention you asked for.]
2. **External edits.** If the file changes above a mark, a plain line number now points to the wrong text. Should a mark also save that line's text, so it can find the nearest matching line if the text has moved? [Yes. It costs little and makes marks hold up when you edit with mdterm's auto-reload open.]
3. **Uppercase letters.** In vim, `A-Z` marks work across files and jump to their file. Do you want that, or only `a-z` per file (with `A-Z` treated as more per-file letters)? [Cross-file `A-Z`: you already open several files at once. It's cheap if I build it now, but I can leave it out.]
4. **Previous position.** Should `''` jump back to where you were before the last jump, like vim? [Yes, using the existing `nav_history`. Backspace keeps working.]
5. **Seeing your marks.** Do you want a mark list overlay (like vim's `:marks`) and/or a gutter indicator next to marked lines? Or just keys and toasts for now? [Toasts only for now, overlay as a follow-up. A gutter indicator affects wrap width and the HTML export.]
6. **Where marks are disabled.** stdin input has no file path, JSON files have collapsible views with no stable line mapping, and slide mode has its own key handler. My proposal:
   - stdin: marks work for the session only, with a toast saying they won't be saved.
   - JSON: marks off, with a toast.
   - Slide mode: marks work and jump to the slide containing the mark.

   OK?
7. **Missing marks and overwriting.** `'x` with no mark set shows a toast "Mark x not set". Setting a mark on a letter already in use overwrites it silently and shows a "Mark x set" toast. Agreed?
8. **Cleanup.** Should marks for files that no longer exist be pruned? [Yes, on load, since it costs only a stat per file.]

Once you answer, I'll have the architect agents work out the options and deliver the final plan as the lavish page and the markdown file under `.lavish/`.

## Simulated user turn 1

1. Yes, move mouse capture to `M` and give `m` to marks.
2. Yes, save the line text too.
3. Only `a-z`, per file. No `A-Z` for now, and uppercase letters shouldn't set marks.
4. Yes, `''` using `nav_history`.
5. Toasts only for now.
6. OK as proposed.
7. Agreed.
8. Yes, prune on load.

## Executor turn 2

I've written the plan as a page and a markdown file. No code has been written yet.

- `.lavish/bookmarks-plan.html` uses mdterm's own dark-theme colors from `src/theme.rs`, so the mockups look like the real viewer.
- `.lavish/bookmarks-plan.md` has the same content.

I skipped the separate architect agents. Your answers left only one real design choice, and the plan compares the options for it in its alternatives section.

**The core problem:** the scroll position mdterm tracks counts lines after word wrapping. It shifts with a resize, the `l` line-number toggle, images loading and any edit to the file, so it can't be saved. The renderer already gets each line's position in the source from the parser (`src/markdown.rs:1585`) and then throws it away. The plan keeps it.

**How it's structured:**

1. **Source line on each line.** Each rendered line gets a new `source` field holding its source line number. Wrapping and image expansion copy it to every piece. It's set in one place in `render_with`. Code block lines get exact numbers; tables and paragraphs that span several source lines map to their first line.
2. **New `src/marks.rs`.** A mark stores the source line, how far down within that line's wrapped rows you were, and the line's text.
   - **Jumping back:** the mark is exact at the same width and lands on the same source line after a resize. After an edit it finds its line again by matching the saved text.
   - **The store** is one `marks.json` under the state directory (`~/.local/state` on Linux, `~/Library/Application Support` on macOS). Each new mark re-reads the file before writing, so two mdterm windows don't overwrite each other. Files that no longer exist are pruned on load. A corrupt file is moved to `marks.json.bak`.
3. **Key handling.** After `m` or `'`, mdterm waits for the next key. That check has to run before the help toggle, otherwise `m` then `h` would open help instead of setting mark `h`. Backspace and `''` share one go-back helper; `''` also records where you were, so pressing it again toggles back. Slide mode jumps to the slide containing the mark.
4. **Testing.** The mark store is passed in when the viewer starts, so tests use a temporary directory and never touch your real marks file. The plan also lists the unit tests and a tmux end-to-end run covering relaunch, resize, external edits, slide mode and stdin.

**Main trade-off:** adding the field means updating about 50 places that build a line by hand. The compiler catches every one, and the field then follows each line through every later step automatically. The alternative is a separate list of source numbers that wrapping and image expansion would each have to keep in step, which breaks easily later.

The work is split into five commits: the `M` rebind, source tracking, the mark store, viewer integration, then docs.

Should I go ahead and implement it as planned, or do you want to annotate or change anything first?

## Simulated user turn 2

APPROVED
The plan matches all my answers, and I only wanted the plan, so no implementation yet.

## Executor turn 3

Both plan files are written and unchanged since you reviewed them:

- `.lavish/bookmarks-plan.html`
- `.lavish/bookmarks-plan.md`

I've stopped there and implemented nothing. When you want to build it, the plan's five commits can be done in order, starting with moving mouse capture to `M`.
