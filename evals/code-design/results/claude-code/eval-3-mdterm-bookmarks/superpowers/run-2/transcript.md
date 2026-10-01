## Eval Prompt

/superpowers:brainstorming i want bookmarks in mdterm - `m` + letter sets a mark at the current position, `'` + letter jumps back, and marks persist per file between sessions. how should we structure this?

## Executor turn 1

I've looked through the viewer. Here's how I understand the request, and one thing I found that we need to sort out first.

**What you asked for**
- `m` + letter sets a mark at the current position.
- `'` + letter jumps to that mark.
- Marks are saved per file and survive restarts.

**What I'm assuming (correct me if any of these are wrong)**
- The point is getting back to spots in long documents you return to, like specs, notes or runbooks.
- A "position" is a spot in the document. It isn't a row on screen. So a mark should still land in the right place after you resize the terminal, toggle line numbers, or after images load and push content down.
- Marks should behave sensibly when the file changes on disk (auto-reload). They shouldn't jump somewhere random.
- Nothing else in the app should get slower or less reliable. If the marks file is missing or corrupt, the viewer still works.

**Two things in the code that shape the design**
1. `m` is already taken. It toggles mouse capture (`src/viewer.rs:1647`).
2. The viewer only knows the scroll position as a row index into the wrapped output (`state.offset`). Wrapped lines don't keep any link back to the source line. That row index changes with width, line numbers and image sizes, so saving it directly would break. We need a more stable anchor, and that's the main design question I'll bring with the approaches.

**First question: what should happen to the mouse toggle on `m`?**

- **A)** Move mouse toggle to another key (for example `M`), and `m` becomes the mark prefix, as in vim/less. Existing users have to learn the new key.
- **B)** Keep `m` for mouse and use a different mark prefix (for example `b`). No breaking change, but it's not the key you asked for.
- **C)** Something else you have in mind.

I recommend **A**. `m` for marks is what vim and less users expect, and mouse toggle is rarely used, so it can move. The help overlay and README would be updated to match.

## Simulated user turn 1

A, move mouse toggle to `M`.

## Executor turn 2

Good, `M`, `'` and `` ` `` are all free, so `M` becomes the mouse toggle.

**Next question: when the file changes on disk, what should a mark stay attached to?**

- **A) The same source line number.** Simple and predictable. But if you add 20 lines above a mark, it ends up 20 lines too early, on whatever text is there now.
- **B) The text it was on.** We save the source line plus a small fingerprint of its content. That could be the nearest heading and the line's own text. On load we look for that content near the old line, and fall back to the line number if it's gone. The mark moves with its section when you edit around it.
- **C) Only the nearest heading.** Very stable, but coarse. In a long section you land at the heading, not where you were.

I recommend **B**. Your files get edited and auto-reloaded while you read them, and with A the marks would slowly point at the wrong places. B costs a bit more code, but it stays inside a small module of its own.

## Simulated user turn 2

B, go with the text-based anchor. Marks should survive resizes and small edits to the file, so that fits.

## Executor turn 3

That settles the anchor. I looked a bit further, and these are the facts that drive the structure:

- The renderer already reads `pulldown-cmark` with `into_offset_iter()` (`src/markdown.rs:1585`), so we know the source byte range of every event. That information is thrown away before it reaches `Line`.
- `rebuild()` keeps `offset` as a row index, and it drifts after resizes. Marks shouldn't rely on it.
- `viewer.rs` is already 4356 lines, so the new logic belongs in its own module.

## Approaches

**1) Source provenance on `Line`, plus a dedicated `marks.rs` (recommended)**
- `Line` gets `src: Option<usize>`, the byte offset of the source block that produced it. It's set in one place, the `render_with` event loop, which stamps lines pushed during each event. `wrap_lines` copies it to every wrapped row.
- `marks.rs` is pure logic with no terminal code. It turns a source position into an anchor (line number + line text), finds that anchor again in the current content, and loads/saves the store.
- The viewer only translates: top visible row → `src` → anchor, and anchor → byte offset → first row whose `src` is at or after it.
- Trade-off: every `Line { .. }` literal (about 50 of them) needs `src: None`. That's a mechanical change, and it gives us a source map other features can reuse later, like "open in editor at line".

**2) A separate source map returned next to the lines**
- `render` returns a `Vec<usize>` alongside `Vec<Line>`, and wrapping keeps it in sync.
- `Line` stays untouched, but two vectors have to stay aligned through wrapping and image-row expansion. That's an easy invariant to break without anyone noticing.

**3) Anchor on rendered text only**
- Save the plain text of the top rendered line and search the rendered output for it on jump.
- No changes to the renderer, but it's fragile. Wrapping, the line-number gutter, math rendering and tables all change the rendered text, so a resize can break a mark. That conflicts with your goal.

I recommend **1**. It's the only option where marks are tied to the source, so resizes, theme, line numbers and image loading can't affect them. The per-file logic is also unit-testable without a terminal.

Does approach 1 work for you? If yes, I'll go through the design section by section: keys and viewer state, anchor capture and lookup, storage, and edge cases (JSON, stdin, slide mode).

## Simulated user turn 3

Approach 1 works. Go ahead with the section-by-section design.

## Executor turn 4

## Section 1: Keys and viewer state

**Bindings (Normal mode)**
- `m` followed by a letter `a`-`z` sets that mark. `'` followed by a letter jumps to it.
- `M` takes over the mouse capture toggle from `m`. The help overlay (`src/viewer.rs:3637`) gets three entries in "Navigation": `m{a-z}` Set mark, `'{a-z}` Jump to mark, `M` Toggle mouse capture. The README is updated to match.
- Only lowercase letters. Uppercase marks that work across files (as in vim) are out of scope. Pressing a key outside `a`-`z` after the prefix cancels quietly. Esc also cancels.

**State**
- `ViewerState` gets `pending_mark: Option<MarkOp>`, with `enum MarkOp { Set, Jump }`.
- `m` and `'` in `handle_normal` only set `pending_mark`.
- `handle_event` checks `pending_mark` first. That's before the help-toggle check, so `m` then `h` sets mark `h` instead of opening help. The next key press is consumed whatever it is: a letter runs the operation, anything else cancels. Ctrl+C still quits.

**Feedback**
- While a prefix is waiting, the status bar shows `m-` or `'-`, so the waiting state is visible.
- Toasts: `Mark a set`, `Jumped to mark a`, `Mark a not set`.
- A jump pushes the current `(file_idx, offset)` onto `nav_history`, so Backspace returns you to where you were, the same as after following a link. I'm leaving out vim's `''` because Backspace already does that job.

**What the viewer does on each operation (details in the next section)**
- Set: take the top visible row, read its `src`, and pass it to `marks::Anchor::capture(&content, byte)`. Then store and save.
- Jump: `Anchor::resolve(&content)` returns a byte offset. Scroll to the first wrapped row whose `src` is at or after it, clamped to `max_offset`.

Does this section look right? In particular: is the top visible row the right "current position", and is Backspace-to-return enough without `''`?

## Simulated user turn 4

Yes, the top visible row is the right "current position", and Backspace is enough without `''`. Section 1 looks good, go on to the next one.

## Executor turn 5

## Section 2: Provenance and anchors

**Provenance on `Line` (`style.rs`, `markdown.rs`)**
- `Line` gets `pub src: Option<usize>`, a byte offset into the source. Every existing `Line { .. }` literal gets `src: None`.
- Stamping happens once, in the `render_with` loop. After each `renderer.process(event, range)`, any line pushed during that call that has no `src` yet gets `range.start`. Paragraphs are flushed on their `End` event, and that event's range starts at the start of the block. So every row of a block points at the block's first source line.
- Code blocks are the one exception. Each code line gets its own offset (the start of the text range plus the bytes before that line), so a mark inside a long code block lands on that exact line instead of the fence.
- `wrap_lines` copies `src` to every wrapped row, including blockquote and continuation rows. Image rows added by `finalize_layout` copy `src` from their placeholder line.
- JSON lines keep `src: None` (see Section 4).

**Granularity, stated plainly:** in prose, a mark points at a block, such as a paragraph, list item, heading or table. A code block points at a single line. If you set a mark partway through a long wrapped paragraph, the jump goes to the paragraph's first row. I think that's right, because wrapped rows don't exist in the source and change with every resize.

**`marks.rs`: the anchor (pure functions, no I/O)**
```rust
pub struct Anchor { pub line: usize, pub text: String }   // 0-based line, trimmed text

impl Anchor {
    pub fn capture(content: &str, byte: usize) -> Anchor;
    pub fn resolve(&self, content: &str) -> Resolved;
}
pub struct Resolved { pub byte: usize, pub line: usize, pub exact: bool }
```
- `capture` finds the source line containing `byte` and stores its trimmed text, cut to 256 characters.
- `resolve`:
  1. If `line` still has `text` on it, use it.
  2. Otherwise use the nearest line with the same trimmed text, measured by `|i - line|`, with the earlier line winning a tie.
  3. Otherwise fall back to `line`, clamped to the end of the file, with `exact: false`.
  4. An empty `text` means "match by line number only".

**Viewer mapping**
- Set: start at the top visible row and scan forward to the first row with a `src`. If there is none, scan backward. Then call `capture`.
- Jump: find the largest `src` that is at or before `resolved.byte`, then scroll to the first row with that `src`. That handles a mark line that sits in the middle of a block.
- If the mark was found by its text on a different line, the stored anchor moves to the new line and is saved, so drift doesn't add up over many edits.
- If it fell back to the line number, the toast says `Jumped to mark a (text not found)`, and the stored anchor is left alone so it can match again if the text comes back.

**Tests**
- `marks.rs` unit tests: unchanged file, lines inserted or deleted above the mark, mark line edited (fallback), duplicate lines (nearest wins), file truncated, empty file.
- `markdown.rs` / `style.rs` tests: `src` on headings, paragraphs and code-block lines, and `src` surviving wrapping.

Does this section look right, especially block-level granularity for prose and per-line for code?

## Simulated user turn 5

Yes, block-level for prose and per-line for code is fine. Section 2 looks good, go on to the next one.

## Executor turn 6

## Section 3: Storage

**Location**
- `dirs::state_dir()`, falling back to `dirs::data_dir()`, then `mdterm/marks.json`.
- That gives `~/.local/state/mdterm/marks.json` on Linux and `~/Library/Application Support/mdterm/marks.json` on macOS.
- Marks are state, not configuration, so they stay out of `config.toml`.
- No new runtime dependency: `serde_json` and `dirs` are already in the project.

**Format**
```json
{
  "version": 1,
  "files": {
    "/Users/jan/notes/spec.md": {
      "a": { "line": 41, "text": "## Rollout plan" }
    }
  }
}
```
Files are keyed by `fs::canonicalize(path)`, so `./spec.md`, `../x/spec.md` and symlinks all share one set of marks.

**`MarkStore` (in `marks.rs`, next to `Anchor`)**
```rust
pub struct MarkStore { path: Option<PathBuf>, files: HashMap<PathBuf, BTreeMap<char, Anchor>>, writable: bool }

impl MarkStore {
    pub fn load() -> Self;                       // default location
    pub fn load_from(path: PathBuf) -> Self;     // tests
    pub fn get(&self, file: &Path, letter: char) -> Option<&Anchor>;
    pub fn set(&mut self, file: &Path, letter: char, anchor: Anchor) -> io::Result<()>;
}
```
- `ViewerState` owns a `MarkStore`, loaded once in `ViewerState::new`. Piped output and HTML export never touch it.
- `set` updates memory, then saves straight away. Re-anchoring after a text match also goes through `set`.

**Writing safely**
- On each save, re-read the file from disk, merge in only the entry that changed, write `marks.json.tmp` in the same directory, then `rename` it into place. The rename is atomic, so a crash can't leave a half-written file.
- Re-reading before each save means two mdterm instances only conflict if they write the same file and letter at the same moment. In that case the last write wins. File locking would cost more than that edge case is worth.
- The directory is created on the first write.

**Failure behaviour (the viewer must keep working)**
- Missing file: start empty.
- Unreadable, corrupt, or an unknown `version`: start empty with `writable = false`, so we never overwrite a file we couldn't read. Marks still work for the session. The first `set` shows the toast `Marks file unreadable - not saving`, once.
- A write fails, for example on a read-only disk: the toast says `Could not save marks`, and the mark stays in memory.
- No state directory: in-memory only.

**Deliberately left out:** deleting marks (setting a mark again overwrites it), a marks list overlay, and removing entries for files that no longer exist. That last one could wipe marks for a file on an unmounted drive, and the store stays tiny anyway.

**Tests:** round-trip, merging with a file another instance changed, a corrupt file not being overwritten, and a missing directory being created. I'd add `tempfile` as a dev-dependency for clean temp directories, since the repo has no test temp helper today.

Does this section look right?

## Simulated user turn 6

Yes, Section 3 looks right. State dir with the data dir fallback, a separate marks.json outside config.toml, and the atomic write all work for me. Go on to the next section.

## Executor turn 7

## Section 4: Edge cases and integration

**Where marks work**

| Context | Behaviour |
|---|---|
| Normal markdown view, one file or several | Works. Marks belong to the file currently shown, keyed by its canonical path. A jump never switches files. |
| Several files with Tab / Shift+Tab | Each file has its own `a`-`z`. Mark `a` in `spec.md` and mark `a` in `notes.md` are separate. |
| stdin (`<stdin>`, `files` is empty) | `m`/`'` show the toast `Marks need a file`. This guard also prevents the `files[current_file_idx]` index panic. |
| JSON view (`json_view.is_some()`) | Toast `Marks not available in JSON view`. JSON rows have no `src`, and the JSON view has its own cursor model. Invalid JSON already falls back to markdown rendering, so it gets `src` and marks work there. |
| Slide mode | Not bound. `handle_slide_keys` returns before `handle_normal`, so `m`/`'` do nothing, and the help entries are listed under Navigation for the normal view. Adding slide support later only needs "jump sets `current_slide` to the slide containing the target row". |
| Search, TOC, link picker, fuzzy, help | Not bound. Those modes have their own keys, and Search/Fuzzy take `m` and `'` as typed text. |

**Content changes during a session**
- Auto-reload and task-checkbox toggles both replace `content`. Nothing needs to happen at that moment, because anchors are resolved against the current content each time you jump. That's why Section 2 tolerates edits.
- Resize, theme toggle, line numbers and image loading change only the wrapped rows, never `src`, so marks aren't affected.

**Pending prefix lifecycle**
- Only key presses use up `pending_mark`. Mouse events and resizes leave it alone.
- A file switch, reload or rebuild doesn't clear it either, because the next key resolves against whatever is current.
- Ctrl+C still quits while a prefix is pending.

**Files touched**
- `src/marks.rs` (new): `Anchor`, `Resolved`, `MarkStore`, and their tests.
- `src/style.rs`: `Line.src`, and `wrap_lines` propagating it.
- `src/markdown.rs`: stamping in `render_with`, per-line offsets in code blocks, and `src: None` on literals.
- `src/json.rs`, `src/export.rs`, `src/viewer.rs`: `src: None` on literals where needed.
- `src/viewer.rs`: `MarkOp`, `pending_mark`, the `marks` field, intercepting the key after `m`/`'` in `handle_event`, the `m`/`'`/`M` bindings, the status-bar hint, help entries, and image rows copying `src` in `finalize_layout`.
- `src/main.rs`: `mod marks;`
- `README.md` and `CLAUDE.md`: the keys, and the architecture list going from 10 to 11 files.
- `Cargo.toml`: `tempfile` as a dev-dependency.

**End-to-end check before calling it done**
1. Run the real binary in a terminal.
2. Set marks, resize, toggle line numbers, jump.
3. Insert lines above a mark in an editor while the file is open, let it auto-reload, and jump.
4. Quit, restart and jump.
5. Corrupt `marks.json` and confirm it isn't overwritten.

Does this section look right? Once you approve it, I'll write the spec. One question about where it goes: the brainstorming default is `docs/superpowers/specs/2026-10-01-bookmarks-design.md`, committed. My instructions for this session are to put the plan in `.lavish/` (Markdown + HTML). I suggest the spec in `docs/superpowers/specs/`, and the implementation plan from writing-plans in `.lavish/`. Does that work, or do you want both in `.lavish/`?

## Simulated user turn 7

Section 4 looks right. For the location, your suggestion works: spec in `docs/superpowers/specs/`, implementation plan in `.lavish/`. Go ahead and write the spec.

## Executor turn 8

I've written the spec and committed it to `docs/superpowers/specs/2026-10-01-bookmarks-design.md` (commit `ef942dd`). There's no `/commit` skill in this session, so I made the commit with plain git, following the repo's `docs:` message style.

It covers everything we agreed in the four sections, plus a few rules I had to settle while writing it. Please check these:

- **Help overlay:** in Section 4 I said all three entries go under "Navigation". I changed that while reviewing: `m{a-z}` and `'{a-z}` go under Navigation, and the mouse entry stays in "Actions" with its key changed from `m` to `M`.
- **Code-block offsets:** each code line gets its own offset before the main loop does its block-level stamping, and the loop only fills lines that have no offset yet. That way the per-line values are never overwritten.
- **Failed re-read before a write:** when saving, the store re-reads `marks.json` first. If that read fails to parse, the write is cancelled and the store stops saving for the session, the same as a corrupt file at startup.
- **No path for the file:** if mdterm can't resolve the file's full path, the mark works for the session but isn't saved.

Please review the spec and let me know if you want any changes. Once you approve it, I'll invoke writing-plans to create the implementation plan in `.lavish/` (Markdown + HTML).

## Simulated user turn 8

APPROVED
The spec matches what we agreed, so go ahead with writing-plans in `.lavish/`.

## Executor turn 9

The implementation plan is finished. I followed the writing-plans skill and haven't implemented anything.

- **Markdown:** `.lavish/mdterm-marks.md` has the full step-by-step plan, with every test and code block written out.
- **HTML:** `.lavish/mdterm-marks.html` covers today vs after, a mock of the status-bar hint, a data-flow diagram, task cards, the key code excerpts, the review focus list, risks, and the execution choice. Its styling copies mdterm's own dark theme from `src/theme.rs` (the Catppuccin Mocha colors), because the artifact is about this app. I haven't opened it in a browser and haven't checked how it renders.

I wrote both files but didn't commit them. Before planning, I checked the starting state: 149 tests pass and 6 are ignored, and clippy and fmt are clean.

**Tasks:**
1. Add `Line.src` (the source byte offset of each rendered line) and carry it through wrapping and image rows.
2. Give each code-block row the offset of its own source line.
3. Add `src/marks.rs` with anchors and the row-to-source mapping.
4. Add `MarkStore` persistence with atomic writes, plus `tempfile` as a dev-dependency.
5. Wire up the viewer: `m` / `'` / `M`, the stdin and JSON guards, the status hint, help entries, and README and CLAUDE.md updates.
6. Run it end to end in a real terminal through tmux.

**Four places the plan refines the spec** (each stays within what you approved):
- Text lines take `src` from their first piece of text, not only from the main render loop. Otherwise the line before a nested list would get the nested list's offset.
- Blank separator rows have no `src`, so a mark set on a blank top row attaches to the next block instead of the previous one.
- `MarkStore` is passed in through `ViewerOptions` from `main.rs` rather than loaded inside the viewer. Tests can then use an in-memory store and never touch your real marks file.
- An empty document shows the toast `Nothing to mark`.

**One thing for you:** the mouse toggle moves to `M` with its existing toasts unchanged, and those contain em dashes (`Mouse capture OFF — select text freely`). Changing them is outside this plan. I can switch them to `-` as part of Task 5 if you want.

Please review the plan. Does it capture what you want, and which execution approach should we use?
- **Subagent-driven (my recommendation):** a fresh implementer and reviewer for each task. Tasks 3-5 rely on exact signatures from earlier tasks, and a mistake in Task 1 would quietly send every mark to the wrong place, so checking each task before the next one starts is worth it.
- **Native:** I implement all six tasks in this session, then one reviewer checks the whole branch. It's cheaper, but nothing is reviewed until the end.
