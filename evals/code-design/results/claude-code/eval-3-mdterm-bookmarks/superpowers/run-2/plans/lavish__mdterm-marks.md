# mdterm Marks (Bookmarks) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vim-style marks in the mdterm viewer. `m{a-z}` sets a mark, `'{a-z}` jumps to it, and marks persist per file across sessions. A mark keeps pointing at the same content through resizes and small edits.

**Architecture:**
- Every rendered `Line` carries `src: Option<usize>`, the source byte offset it came from. This survives wrapping and image-row expansion.
- A new pure module, `src/marks.rs`, turns a byte offset into a content anchor (line number + trimmed text), resolves anchors against changed content, maps between rows and source offsets, and persists anchors to `marks.json` with atomic writes.
- `viewer.rs` only wires keys, guards, toasts and the status hint to that module.

**Tech Stack:** Rust 2024, pulldown-cmark 0.11 (`into_offset_iter`), crossterm 0.28, serde + serde_json, dirs 5. New dev-dependency: `tempfile`.

**Spec:** `docs/superpowers/specs/2026-10-01-bookmarks-design.md` (commit `ef942dd`). Read it before starting.

**Deliberate refinements of the spec (all within its intent):**
1. **How `src` is assigned.** Text lines take their `src` from the event that produced their *first span* (set in `push_span`). The `render_with` loop stamps all other lines (borders, tables, images, rules) with the event's `range.start`. Stamping only in the loop would give the paragraph before a nested list the nested list's offset, because `Start(List)` flushes the parent item's text.
2. **Blank lines get no `src`.** `Line::empty()` rows (no spans, `LineMeta::None`) keep `src: None`, so a mark set while a blank separator is the top row attaches to the next block, not the previous one.
3. **Where the store is created.** `MarkStore` is passed in through `ViewerOptions.marks`, created in `main.rs` only on the interactive (TTY) path, instead of being loaded inside `ViewerState::new`. Tests can then inject `MarkStore::in_memory()` and never touch the user's real marks file. Piped output and export still never create one.
4. **Empty documents.** Setting a mark in a document with no content rows shows the toast `Nothing to mark`.

## Global Constraints

- Rust edition 2024 (rustc 1.85+). No new runtime dependencies. `tempfile = "3"` as a dev-dependency only.
- Marks file: `dirs::state_dir()`, falling back to `dirs::data_dir()`, then `mdterm/marks.json`. JSON `{"version": 1, "files": {<canonical path>: {<letter>: {"line": <0-based>, "text": <trimmed, max 256 chars>}}}}`.
- Writes: re-read from disk, merge the single changed entry, write a temp file in the same directory, then `rename` it into place. Never overwrite a file that failed to parse or has `version != 1`.
- Only `a`-`z` are marks. Any other key after the prefix cancels silently. `Ctrl+c` still quits while a prefix is pending.
- `M` toggles mouse capture (moved from `m`).
- Toast strings, verbatim:
  - `Mark a set`
  - `Jumped to mark a`
  - `Jumped to mark a (text not found)`
  - `Mark a not set`
  - `Marks need a file`
  - `Marks not available in JSON view`
  - `Marks file unreadable - not saving`
  - `Could not save marks`
  - `Nothing to mark`

  (`a` stands for the actual letter.)
- Status hint while a prefix is pending: `m-` or `'-`.
- No em dash characters in any new code, strings or docs. Use `-`.
- Every task ends with `cargo test`, `cargo clippy --all-targets` (zero warnings) and `cargo fmt --check` all clean. The baseline is clean today: 149 passed, 6 ignored.

## Review Focus

These are the five failure modes most likely to hit a real user that the spec implies but doesn't spell out as tests. Each has a pinned test in the task that owns the code:

1. **Resize between set and jump.** A mark set at width 80 must land on the same block after the terminal shrinks to 40 columns and rows shift. Pinned in Task 5: `mark_survives_resize`.
2. **Mark inside a nested list or blockquote.** After setting it and resizing, the jump must return to the same item's first row, not the parent item or the quote's first line. Pinned in Task 1 (`nested_list_item_gets_its_own_src`) and Task 5 (`mark_on_nested_list_item_round_trips`).
3. **Document shrinks under a mark during auto-reload.** If the file is truncated to fewer lines than the mark's line, the jump clamps to the end, doesn't panic, and shows the fallback toast. Pinned in Task 5: `jump_after_truncation_clamps_and_reports_fallback`.
4. **Non-ASCII and CRLF content.** Byte offsets next to multibyte characters and `\r\n` line endings must not panic or shift the anchor line, and lines longer than 256 characters must still match after the text is cut off. Pinned in Task 3: `capture_handles_multibyte_and_crlf` and `long_line_fingerprint_still_matches`.
5. **Prefix followed by an unexpected key.** `m` then `A`, a digit, `Esc` or `Ctrl+x` must set nothing, clear the prefix, and not trigger the key's normal action (`m` then `q` must not quit). Marks must also stay per file across Tab switching. Pinned in Task 5: `prefix_then_non_letter_cancels_without_side_effects` and `marks_are_per_file`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `src/style.rs` | `Line` gains `src`; `wrap_lines` copies it to every wrapped row | Modify |
| `src/markdown.rs` | Assigns `src` while rendering: span-level for text, event-level for everything else, per line in code blocks | Modify |
| `src/json.rs` | `src: None` on all `Line` literals | Modify (mechanical) |
| `src/marks.rs` | `Anchor`, `Resolved`, `source_at_row`, `row_for_source`, `MarkStore`, `SaveStatus` | Create |
| `src/viewer.rs` | `MarkOp`, `pending_mark`, `marks`; key interception; `m` / `'` / `M`; guards; set/jump; status hint; help entries; `finalize_layout` copies `src` | Modify |
| `src/main.rs` | `mod marks;` and passes `MarkStore::load()` to the viewer | Modify |
| `Cargo.toml` | `[dev-dependencies] tempfile = "3"` | Modify |
| `README.md`, `CLAUDE.md` | Key docs, marks file location, architecture list now 11 files | Modify |

---

### Task 1: Source provenance on `Line`

**Files:**
- Modify: `src/style.rs:55-59` (struct), `src/style.rs:89-145` (`wrap_lines`), every `Line { .. }` literal in `src/style.rs`
- Modify: `src/markdown.rs` (`Renderer` struct ~line 17-70, `Renderer::new` ~line 80-130, `push_span` ~line 178, `flush_line_with_meta` ~line 189, `render_with` ~line 1583-1588, all `Line { .. }` literals)
- Modify: `src/json.rs` (all `Line { .. }` literals), `src/viewer.rs:639` (`finalize_layout`) and `src/viewer.rs:4274` (test helper)
- Test: `src/style.rs` tests module, `src/markdown.rs` tests module, `src/viewer.rs` tests module

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `pub struct Line { pub spans: Vec<StyledSpan>, pub meta: LineMeta, pub src: Option<usize> }`
  - every wrapped row has the `src` of its pre-wrap line
  - markdown text rows have the byte offset of their first span's event
  - other non-blank rows have their event's `range.start`
  - `Line::empty()` and JSON rows have `None`

- [ ] **Step 1: Add the field and make everything compile**

In `src/style.rs`:

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// Byte offset into the source markdown of the block or span that produced this line.
    pub src: Option<usize>,
}

impl Line {
    pub fn empty() -> Self {
        Line {
            spans: vec![],
            meta: LineMeta::None,
            src: None,
        }
    }
```

Then run `cargo build` and add `src: None,` to every `Line { .. }` literal the compiler reports, in `style.rs`, `markdown.rs`, `json.rs` and `viewer.rs`. Don't use `..Default::default()`; the explicit field keeps provenance visible at each construction site. Run `cargo test` and expect 149 passed.

- [ ] **Step 2: Write the failing tests**

Add to `src/style.rs` tests:

```rust
    #[test]
    fn wrap_propagates_src_to_every_row() {
        let mut line = plain_line("alpha beta gamma delta epsilon zeta eta theta");
        line.src = Some(42);
        let wrapped = wrap_lines(&[line], 12);
        assert!(wrapped.len() > 1);
        assert!(wrapped.iter().all(|l| l.src == Some(42)));
    }

    #[test]
    fn wrap_propagates_src_through_blockquote_rows() {
        let line = Line {
            spans: vec![
                StyledSpan {
                    text: BLOCKQUOTE_PREFIX.to_string(),
                    style: Style::default(),
                },
                StyledSpan {
                    text: "alpha beta gamma delta epsilon zeta eta theta".to_string(),
                    style: Style::default(),
                },
            ],
            meta: LineMeta::None,
            src: Some(7),
        };
        let wrapped = wrap_lines(&[line], 16);
        assert!(wrapped.len() > 1);
        assert!(wrapped.iter().all(|l| l.src == Some(7)));
    }
```

Add to `src/markdown.rs` tests:

```rust
    // ── Source provenance ───────────────────────────────────────────────────

    /// 0-based source line that the rendered line containing `needle` points at.
    /// Marks only care about the source line, not the exact byte inside it.
    fn src_line(input: &str, lines: &[Line], needle: &str) -> Option<usize> {
        let src = lines
            .iter()
            .find(|l| line_text(l).contains(needle))
            .and_then(|l| l.src)?;
        Some(input[..src].matches('\n').count())
    }

    #[test]
    fn heading_and_paragraph_get_src() {
        let input = "# Title\n\nFirst para.\n\nSecond para.\n";
        let (lines, _) = render_test(input);
        assert_eq!(src_line(input, &lines, "Title"), Some(0));
        assert_eq!(src_line(input, &lines, "First para."), Some(2));
        assert_eq!(src_line(input, &lines, "Second para."), Some(4));
    }

    #[test]
    fn nested_list_item_gets_its_own_src() {
        let input = "- parent item\n  - child item\n- sibling\n";
        let (lines, _) = render_test(input);
        assert_eq!(src_line(input, &lines, "parent item"), Some(0));
        assert_eq!(src_line(input, &lines, "child item"), Some(1));
        assert_eq!(src_line(input, &lines, "sibling"), Some(2));
    }

    #[test]
    fn blockquote_paragraphs_get_their_own_src() {
        let input = "> first quote para\n>\n> second quote para\n";
        let (lines, _) = render_test(input);
        assert_eq!(src_line(input, &lines, "first quote"), Some(0));
        assert_eq!(src_line(input, &lines, "second quote"), Some(2));
    }

    #[test]
    fn table_rows_get_src() {
        let input = "Intro.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n";
        let (lines, _) = render_test(input);
        let row = lines.iter().find(|l| line_text(l).contains('1')).unwrap();
        let src = row.src.expect("table row has src");
        assert!(input[..src].matches('\n').count() >= 2, "table rows point into the table");
    }

    #[test]
    fn blank_separator_lines_have_no_src() {
        let (lines, _) = render_test("One.\n\nTwo.\n");
        assert!(
            lines
                .iter()
                .filter(|l| l.spans.is_empty() && matches!(l.meta, LineMeta::None))
                .all(|l| l.src.is_none())
        );
    }
```

Add to `src/viewer.rs` tests:

```rust
    #[test]
    fn finalize_layout_copies_src_to_image_rows() {
        let image = Line {
            spans: vec![],
            meta: LineMeta::Image {
                url: "https://example.com/x.png".to_string(),
                alt: "x".to_string(),
                row: 0,
                total_rows: 1,
            },
            src: Some(9),
        };
        let mut state = make_state_with_lines(vec![image]);
        state.finalize_layout();
        let rows: Vec<_> = state
            .wrapped
            .iter()
            .filter(|l| matches!(l.meta, LineMeta::Image { .. }))
            .collect();
        assert_eq!(rows.len(), 3);
        assert!(rows.iter().all(|l| l.src == Some(9)));
    }
```

- [ ] **Step 3: Run the tests and check they fail**

Run: `cargo test`
Expected: the new tests FAIL, because `src` is `None` everywhere and the `Some(..)` assertions fail. `blank_separator_lines_have_no_src` already passes, which is fine. It pins the blank-line rule against the stamping added in Step 5. The 149 existing tests still pass.

- [ ] **Step 4: Implement wrap propagation**

In `wrap_lines` (`src/style.rs`), give every row produced from `line` its `src`. In the blockquote branch, inside the existing `for mut w in wrapped` loop:

```rust
            for mut w in wrapped {
                w.spans.insert(0, prefix_span.clone());
                w.meta = line.meta.clone();
                w.src = line.src;
                result.push(w);
            }
```

In the plain branch, before the existing `propagate_all` logic:

```rust
            let mut wrapped = word_wrap(line, width);
            for w in &mut wrapped {
                w.src = line.src;
            }
```

The early `result.push(line.clone())` paths already keep `src`, because `clone` copies it.

- [ ] **Step 5: Implement span-level and event-level stamping in the renderer**

Add to the `Renderer` struct (after `current_spans`):

```rust
    // Source provenance
    event_start: usize,
    span_src: Option<usize>,
```

Initialize both in `Renderer::new`: `event_start: 0, span_src: None,`.

`push_span`, recording where the first span of the pending line came from:

```rust
    fn push_span(&mut self, text: &str, style: Style) {
        if self.current_spans.is_empty() {
            self.span_src = Some(self.event_start);
        }
        self.current_spans.push(StyledSpan {
            text: text.to_string(),
            style,
        });
    }
```

`flush_line_with_meta`, which takes it:

```rust
            spans.append(&mut self.current_spans);
            let src = self.span_src.take();
            self.lines.push(Line { spans, meta, src });
```

At the very top of `fn process(&mut self, event: Event, source_range: std::ops::Range<usize>)`:

```rust
        self.event_start = source_range.start;
```

In `render_with`, replace the loop:

```rust
    for (event, range) in parser.into_offset_iter() {
        let before = renderer.lines.len();
        let start = range.start;
        renderer.process(event, range);
        // The blockquote `is_bar_only` path pops lines, so the vec can shrink.
        let before = before.min(renderer.lines.len());
        for line in &mut renderer.lines[before..] {
            let blank = line.spans.is_empty() && matches!(line.meta, LineMeta::None);
            if line.src.is_none() && !blank {
                line.src = Some(start);
            }
        }
    }
```

The final `renderer.flush_line()` after the loop already gets its `src` from `span_src`, so it needs no stamping. `LineMeta` is already imported in `markdown.rs`.

- [ ] **Step 6: Copy `src` onto expanded image rows**

In `finalize_layout` (`src/viewer.rs` ~line 615), read the placeholder's `src` before the row loop and set it on every generated row:

```rust
                let url = url.clone();
                let alt = alt.clone();
                let src = self.wrapped[i].src;
                // ...
                for r in 0..actual_rows {
                    new_wrapped.push(Line {
                        spans: vec![],
                        meta: LineMeta::Image {
                            url: url.clone(),
                            alt: alt.clone(),
                            row: r,
                            total_rows: actual_rows,
                        },
                        src,
                    });
                }
```

- [ ] **Step 7: Run all checks**

Run: `cargo test && cargo clippy --all-targets && cargo fmt --check`
Expected: all pass, zero clippy warnings.

- [ ] **Step 8: Commit**

```bash
git add src/style.rs src/markdown.rs src/json.rs src/viewer.rs
git commit -m "feat(render): track source byte offset on rendered lines"
```

---

### Task 2: Per-line source offsets in code blocks

**Files:**
- Modify: `src/markdown.rs` (`Renderer` struct, `Renderer::new`, `Event::Start(Tag::CodeBlock)` ~line 837, the `in_code_block` branch of `Event::Text` ~line 1022, `emit_code_block` ~line 230-420)
- Test: `src/markdown.rs` tests module

**Interfaces:**
- Consumes: `Line.src` and the stamping loop from Task 1 (the loop only fills `None`, so values set here win).
- Produces: every `LineMeta::CodeContent` row that holds code text has `src` = the byte offset of the start of the matching source line. Border rows keep the block's event offset.

- [ ] **Step 1: Write the failing tests**

```rust
    fn code_rows(lines: &[Line]) -> Vec<&Line> {
        lines
            .iter()
            .filter(|l| matches!(l.meta, LineMeta::CodeContent { .. }))
            .collect()
    }

    #[test]
    fn code_block_lines_get_per_line_src() {
        let input = "Intro.\n\n```rust\nlet a = 1;\nlet b = 2;\nlet c = 3;\n```\n";
        let (lines, _) = render_test(input);
        let rows = code_rows(&lines);
        // top border, 3 code lines, bottom border
        let a = rows.iter().find(|l| line_text(l).contains("let a")).unwrap();
        let b = rows.iter().find(|l| line_text(l).contains("let b")).unwrap();
        let c = rows.iter().find(|l| line_text(l).contains("let c")).unwrap();
        assert_eq!(a.src, Some(input.find("let a").unwrap()));
        assert_eq!(b.src, Some(input.find("let b").unwrap()));
        assert_eq!(c.src, Some(input.find("let c").unwrap()));
    }

    #[test]
    fn code_block_in_blockquote_maps_to_source_line_starts() {
        let input = "> ```\n> one\n> two\n> ```\n";
        let (lines, _) = render_test(input);
        let rows = code_rows(&lines);
        let one = rows.iter().find(|l| line_text(l).contains("one")).unwrap();
        let two = rows.iter().find(|l| line_text(l).contains("two")).unwrap();
        assert_eq!(one.src, Some(input.find("> one").unwrap()));
        assert_eq!(two.src, Some(input.find("> two").unwrap()));
    }

    #[test]
    fn indented_code_block_lines_get_per_line_src() {
        let input = "Para.\n\n    first\n    second\n";
        let (lines, _) = render_test(input);
        let rows = code_rows(&lines);
        let first = rows.iter().find(|l| line_text(l).contains("first")).unwrap();
        let second = rows.iter().find(|l| line_text(l).contains("second")).unwrap();
        assert_eq!(first.src, Some(input.find("    first").unwrap()));
        assert_eq!(second.src, Some(input.find("    second").unwrap()));
    }
```

The expected value is always the start of the *source line*, never the start of the code text. That's what `Anchor::capture` (Task 3) turns into a line number, and it holds even when the line has a `> ` prefix or indentation.

- [ ] **Step 2: Run the tests and check they fail**

Run: `cargo test code_block_ -- --nocapture`
Expected: the three new tests FAIL. Every code row has the block's start offset, so the `b` and `c` assertions fail.

- [ ] **Step 3: Record where the code text starts**

Renderer field (next to `code_block_content`):

```rust
    code_block_text_start: Option<usize>,
```

Initialize it to `None` in `new`. In `Event::Start(Tag::CodeBlock(kind))`, add `self.code_block_text_start = None;`. In the `Event::Text` handler, in the `else if self.in_code_block` branch:

```rust
                } else if self.in_code_block {
                    if self.code_block_text_start.is_none() {
                        self.code_block_text_start = Some(self.event_start);
                    }
                    self.code_block_content.push_str(&text);
```

- [ ] **Step 4: Assign per-line offsets in `emit_code_block`**

Add this helper method on `Renderer`:

```rust
    /// Byte offsets of the source lines holding each code line, starting at the
    /// source line that contains the first code text event.
    fn code_line_sources(&self, count: usize) -> Vec<Option<usize>> {
        let Some(text_start) = self.code_block_text_start else {
            return vec![None; count];
        };
        let mut pos = self.source[..text_start].rfind('\n').map_or(0, |i| i + 1);
        let mut out = Vec::with_capacity(count);
        for _ in 0..count {
            if pos >= self.source.len() {
                out.push(None);
                continue;
            }
            out.push(Some(pos));
            pos = self.source[pos..]
                .find('\n')
                .map_or(self.source.len(), |i| pos + i + 1);
        }
        out
    }
```

In `emit_code_block`, after `let code = std::mem::take(&mut self.code_block_content);`:

```rust
        let line_sources = self.code_line_sources(LinesWithEndings::from(&code).count());
```

In the code-line loop, use it on the row push (around line 404):

```rust
            self.lines.push(Line {
                spans,
                meta: LineMeta::CodeContent { block_id },
                src: line_sources[line_num],
            });
```

Mermaid diagram rows (`emit_diagram_block`) keep `src: None` from Task 1 and get stamped with the block start by the loop. That's intended, because diagram rows don't correspond to source lines.

- [ ] **Step 5: Run all checks**

Run: `cargo test && cargo clippy --all-targets && cargo fmt --check`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/markdown.rs
git commit -m "feat(render): map code block rows to their source lines"
```

---

### Task 3: `marks.rs` - anchors and row mapping

**Files:**
- Create: `src/marks.rs`
- Modify: `src/main.rs:1-9` (add `mod marks;` in alphabetical order, after `mod markdown;`)
- Test: `src/marks.rs` tests module

**Interfaces:**
- Consumes: `crate::style::Line` with `src` (Task 1).
- Produces:

```rust
#[derive(Clone, Debug, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct Anchor { pub line: usize, pub text: String }

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Resolved { pub byte: usize, pub line: usize, pub exact: bool }

impl Anchor {
    pub fn capture(content: &str, byte: usize) -> Anchor;
    pub fn resolve(&self, content: &str) -> Resolved;
}

pub fn source_at_row(lines: &[Line], row: usize) -> Option<usize>;
pub fn row_for_source(lines: &[Line], byte: usize) -> Option<usize>;
```

- [ ] **Step 1: Write the failing tests**

Create `src/marks.rs` with the test module first, and the signatures from the Interfaces block with `todo!()` bodies so it compiles:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::style::{Line, LineMeta, Style, StyledSpan};

    fn at(content: &str, needle: &str) -> usize {
        content.find(needle).unwrap()
    }

    // ── Anchor::capture ─────────────────────────────────────────────────────

    #[test]
    fn capture_records_line_and_trimmed_text() {
        let doc = "# Title\n\n   Some text  \nmore\n";
        let a = Anchor::capture(doc, at(doc, "Some"));
        assert_eq!(a, Anchor { line: 2, text: "Some text".to_string() });
    }

    #[test]
    fn capture_handles_multibyte_and_crlf() {
        let doc = "héllo wörld\r\nzweite Zeile\r\ndritte\r\n";
        let a = Anchor::capture(doc, at(doc, "zweite"));
        assert_eq!(a, Anchor { line: 1, text: "zweite Zeile".to_string() });
        // Offset inside a multibyte char must not panic and stays on line 0.
        let mid = doc.find('é').unwrap() + 1;
        assert_eq!(Anchor::capture(doc, mid).line, 0);
    }

    #[test]
    fn capture_clamps_out_of_range_offset() {
        let doc = "a\nb\n";
        assert_eq!(Anchor::capture(doc, 999), Anchor { line: 1, text: "b".to_string() });
        assert_eq!(Anchor::capture("", 5), Anchor { line: 0, text: String::new() });
    }

    #[test]
    fn long_line_fingerprint_still_matches() {
        let long = "x".repeat(300);
        let doc = format!("intro\n{long}\n");
        let a = Anchor::capture(&doc, at(&doc, "xxx"));
        assert_eq!(a.text.chars().count(), 256);
        let edited = format!("new\nlines\nintro\n{long}\n");
        let r = a.resolve(&edited);
        assert_eq!((r.line, r.exact), (3, true));
    }

    // ── Anchor::resolve ─────────────────────────────────────────────────────

    #[test]
    fn resolve_unchanged_is_exact() {
        let doc = "a\nb\nc\n";
        let r = Anchor::capture(doc, at(doc, "b")).resolve(doc);
        assert_eq!(r, Resolved { byte: 2, line: 1, exact: true });
    }

    #[test]
    fn resolve_follows_lines_inserted_above() {
        let doc = "a\n## Target\nc\n";
        let a = Anchor::capture(doc, at(doc, "## Target"));
        let edited = "new 1\nnew 2\na\n## Target\nc\n";
        let r = a.resolve(edited);
        assert_eq!(r, Resolved { byte: at(edited, "## Target"), line: 3, exact: true });
    }

    #[test]
    fn resolve_follows_lines_deleted_above() {
        let doc = "x\ny\nz\n## Target\n";
        let a = Anchor::capture(doc, at(doc, "## Target"));
        let r = a.resolve("z\n## Target\n");
        assert_eq!((r.line, r.exact), (1, true));
    }

    #[test]
    fn resolve_falls_back_to_line_when_text_gone() {
        let doc = "a\nb\nc\n";
        let a = Anchor::capture(doc, at(doc, "b"));
        let r = a.resolve("a\nB edited\nc\n");
        assert_eq!(r, Resolved { byte: 2, line: 1, exact: false });
    }

    #[test]
    fn resolve_prefers_nearest_duplicate_and_earlier_on_tie() {
        let a = Anchor { line: 2, text: "dup".to_string() };
        // Duplicates at 1 and 3 are equally near; earlier wins.
        let r = a.resolve("x\ndup\ny\ndup\n");
        assert_eq!((r.line, r.exact), (1, true));
        // Duplicates at 0 and 3; 3 is nearer to 2.
        let r = a.resolve("dup\nx\ny\ndup\n");
        assert_eq!((r.line, r.exact), (3, true));
    }

    #[test]
    fn resolve_clamps_when_file_truncated() {
        let a = Anchor { line: 10, text: "gone".to_string() };
        let r = a.resolve("one\ntwo\n");
        assert_eq!(r, Resolved { byte: 4, line: 1, exact: false });
    }

    #[test]
    fn resolve_empty_file() {
        let a = Anchor { line: 3, text: "x".to_string() };
        assert_eq!(a.resolve(""), Resolved { byte: 0, line: 0, exact: false });
    }

    #[test]
    fn resolve_empty_text_uses_line_number_only() {
        let a = Anchor { line: 1, text: String::new() };
        let r = a.resolve("a\n\nb\n");
        assert_eq!(r, Resolved { byte: 2, line: 1, exact: true });
    }

    #[test]
    fn resolve_crlf() {
        let doc = "one\r\ntwo\r\n";
        let a = Anchor::capture(doc, at(doc, "two"));
        assert_eq!(a.resolve(doc), Resolved { byte: 5, line: 1, exact: true });
    }

    // ── Row mapping ─────────────────────────────────────────────────────────

    fn row(src: Option<usize>) -> Line {
        Line {
            spans: vec![StyledSpan { text: "x".to_string(), style: Style::default() }],
            meta: LineMeta::None,
            src,
        }
    }

    #[test]
    fn source_at_row_scans_forward_then_backward() {
        let lines = vec![row(Some(0)), row(None), row(None), row(Some(20))];
        assert_eq!(source_at_row(&lines, 0), Some(0));
        assert_eq!(source_at_row(&lines, 1), Some(20));
        let tail = vec![row(Some(5)), row(None)];
        assert_eq!(source_at_row(&tail, 1), Some(5));
        assert_eq!(source_at_row(&[], 0), None);
        assert_eq!(source_at_row(&[row(None)], 0), None);
    }

    #[test]
    fn row_for_source_finds_first_row_of_containing_block() {
        // Block at 10 wraps to rows 1-3; byte 14 is a later source line in that block.
        let lines = vec![row(Some(0)), row(Some(10)), row(Some(10)), row(Some(10)), row(Some(30))];
        assert_eq!(row_for_source(&lines, 10), Some(1));
        assert_eq!(row_for_source(&lines, 14), Some(1));
        assert_eq!(row_for_source(&lines, 30), Some(4));
        assert_eq!(row_for_source(&lines, 99), Some(4));
    }

    #[test]
    fn row_for_source_before_first_src_goes_to_first_sourced_row() {
        let lines = vec![row(None), row(Some(8))];
        assert_eq!(row_for_source(&lines, 2), Some(1));
        assert_eq!(row_for_source(&[row(None)], 0), None);
    }
}
```

- [ ] **Step 2: Run the tests and check they fail**

Run: `cargo test marks::`
Expected: FAIL with `not yet implemented` panics.

- [ ] **Step 3: Implement**

Top of `src/marks.rs`:

```rust
use serde::{Deserialize, Serialize};

use crate::style::Line;

const MAX_TEXT_CHARS: usize = 256;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Anchor {
    pub line: usize,
    pub text: String,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Resolved {
    pub byte: usize,
    pub line: usize,
    pub exact: bool,
}

impl Anchor {
    pub fn capture(content: &str, byte: usize) -> Anchor {
        let starts = line_starts(content);
        let Some(last) = starts.len().checked_sub(1) else {
            return Anchor { line: 0, text: String::new() };
        };
        let line = starts.partition_point(|&s| s <= byte).saturating_sub(1).min(last);
        let text = content.lines().nth(line).map(fingerprint).unwrap_or_default();
        Anchor { line, text }
    }

    pub fn resolve(&self, content: &str) -> Resolved {
        let starts = line_starts(content);
        let Some(last) = starts.len().checked_sub(1) else {
            return Resolved { byte: 0, line: 0, exact: false };
        };
        let found = if self.text.is_empty() {
            (self.line <= last).then_some(self.line)
        } else {
            nearest_match(content, &self.text, self.line)
        };
        match found {
            Some(line) => Resolved { byte: starts[line], line, exact: true },
            None => {
                let line = self.line.min(last);
                Resolved { byte: starts[line], line, exact: false }
            }
        }
    }
}

fn fingerprint(line: &str) -> String {
    line.trim().chars().take(MAX_TEXT_CHARS).collect()
}

/// Byte offset where each line of `content` starts, consistent with `str::lines`.
fn line_starts(content: &str) -> Vec<usize> {
    if content.is_empty() {
        return Vec::new();
    }
    let mut starts = vec![0];
    starts.extend(
        content
            .match_indices('\n')
            .map(|(i, _)| i + 1)
            .filter(|&i| i < content.len()),
    );
    starts
}

fn nearest_match(content: &str, text: &str, target: usize) -> Option<usize> {
    content
        .lines()
        .enumerate()
        .filter(|(_, l)| fingerprint(l) == text)
        .map(|(i, _)| i)
        .min_by_key(|&i| (i.abs_diff(target), i))
}

/// Source offset to anchor a mark at, starting from the top visible row.
pub fn source_at_row(lines: &[Line], row: usize) -> Option<usize> {
    let row = row.min(lines.len());
    lines[row..]
        .iter()
        .find_map(|l| l.src)
        .or_else(|| lines[..row].iter().rev().find_map(|l| l.src))
}

/// First row of the block whose source offset is the greatest one at or before `byte`.
pub fn row_for_source(lines: &[Line], byte: usize) -> Option<usize> {
    let block = lines
        .iter()
        .filter_map(|l| l.src)
        .filter(|&s| s <= byte)
        .max()
        .or_else(|| lines.iter().find_map(|l| l.src))?;
    lines.iter().position(|l| l.src == Some(block))
}
```

Check `capture` against the multibyte test: `partition_point` only compares integers and never slices `content` at `byte`, so an offset in the middle of a character can't panic. Every value in `line_starts` comes right after a `\n`, so it is always a valid char boundary for slicing.

Add `mod marks;` to `src/main.rs`. Until Task 5 uses these items, the binary build will warn about dead code. Put `#![allow(dead_code)]` at the top of `src/marks.rs` with the comment `// Wired into the viewer in the marks integration task.` and remove it in Task 5. This keeps clippy at zero warnings between tasks.

- [ ] **Step 4: Run all checks**

Run: `cargo test && cargo clippy --all-targets && cargo fmt --check`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/marks.rs src/main.rs
git commit -m "feat(marks): add content anchors and row mapping"
```

---

### Task 4: `MarkStore` persistence

**Files:**
- Modify: `src/marks.rs`
- Modify: `Cargo.toml` (add a `[dev-dependencies]` section with `tempfile = "3"`)
- Test: `src/marks.rs` tests module

**Interfaces:**
- Consumes: `Anchor` (Task 3).
- Produces:

```rust
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum SaveStatus { Saved, Skipped, Unreadable }

pub struct MarkStore { /* private */ }

impl MarkStore {
    pub fn load() -> MarkStore;                  // default location; in-memory if no state/data dir
    pub fn load_from(path: PathBuf) -> MarkStore;
    pub fn in_memory() -> MarkStore;             // never touches disk
    pub fn get(&self, file: &Path, letter: char) -> Option<&Anchor>;
    pub fn set(&mut self, file: &Path, letter: char, anchor: Anchor) -> io::Result<SaveStatus>;
}
```

`SaveStatus::Saved` means it was written to disk. `Skipped` means memory only: an in-memory store, a path that can't be canonicalized, or an unreadable store after the one-time warning. `Unreadable` is returned exactly once per store, the first time `set` finds the file unreadable, so the viewer shows that toast only once.

- [ ] **Step 1: Add the dev-dependency**

Append to `Cargo.toml`:

```toml
[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 2: Write the failing tests**

Add to the `marks.rs` tests module:

```rust
    // ── MarkStore ───────────────────────────────────────────────────────────

    use std::fs;

    fn anchor(line: usize, text: &str) -> Anchor {
        Anchor { line, text: text.to_string() }
    }

    fn doc_in(dir: &tempfile::TempDir) -> std::path::PathBuf {
        let doc = dir.path().join("doc.md");
        fs::write(&doc, "# Doc\n").unwrap();
        doc
    }

    #[test]
    fn set_then_reload_round_trips() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("state").join("marks.json");
        let doc = doc_in(&dir);

        let mut store = MarkStore::load_from(store_path.clone());
        assert_eq!(store.set(&doc, 'a', anchor(3, "## Rollout")).unwrap(), SaveStatus::Saved);

        let reloaded = MarkStore::load_from(store_path.clone());
        assert_eq!(reloaded.get(&doc, 'a'), Some(&anchor(3, "## Rollout")));

        let json: serde_json::Value =
            serde_json::from_str(&fs::read_to_string(&store_path).unwrap()).unwrap();
        assert_eq!(json["version"], 1);
        let key = fs::canonicalize(&doc).unwrap().to_string_lossy().into_owned();
        assert_eq!(json["files"][key.as_str()]["a"]["line"], 3);
    }

    #[test]
    fn relative_and_absolute_paths_share_marks() {
        let dir = tempfile::tempdir().unwrap();
        let doc = doc_in(&dir);
        let mut store = MarkStore::load_from(dir.path().join("marks.json"));
        store.set(&doc, 'b', anchor(0, "# Doc")).unwrap();
        let indirect = dir.path().join(".").join("doc.md");
        assert_eq!(store.get(&indirect, 'b'), Some(&anchor(0, "# Doc")));
    }

    #[test]
    fn set_merges_with_entries_written_by_another_instance() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("marks.json");
        let doc = doc_in(&dir);

        let mut first = MarkStore::load_from(store_path.clone());
        let mut second = MarkStore::load_from(store_path.clone());
        first.set(&doc, 'a', anchor(1, "one")).unwrap();
        second.set(&doc, 'b', anchor(2, "two")).unwrap();

        let reloaded = MarkStore::load_from(store_path);
        assert_eq!(reloaded.get(&doc, 'a'), Some(&anchor(1, "one")));
        assert_eq!(reloaded.get(&doc, 'b'), Some(&anchor(2, "two")));
        // The second store also sees the first store's mark after its own write.
        assert_eq!(second.get(&doc, 'a'), Some(&anchor(1, "one")));
    }

    #[test]
    fn corrupt_file_is_never_overwritten() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("marks.json");
        fs::write(&store_path, "{ not json").unwrap();
        let doc = doc_in(&dir);

        let mut store = MarkStore::load_from(store_path.clone());
        assert_eq!(store.set(&doc, 'a', anchor(0, "# Doc")).unwrap(), SaveStatus::Unreadable);
        assert_eq!(store.set(&doc, 'b', anchor(0, "# Doc")).unwrap(), SaveStatus::Skipped);
        assert_eq!(fs::read_to_string(&store_path).unwrap(), "{ not json");
        // Marks still work for the session.
        assert_eq!(store.get(&doc, 'a'), Some(&anchor(0, "# Doc")));
    }

    #[test]
    fn unknown_version_is_treated_as_unreadable() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("marks.json");
        let original = r#"{"version": 2, "files": {}}"#;
        fs::write(&store_path, original).unwrap();
        let doc = doc_in(&dir);

        let mut store = MarkStore::load_from(store_path.clone());
        assert_eq!(store.set(&doc, 'a', anchor(0, "# Doc")).unwrap(), SaveStatus::Unreadable);
        assert_eq!(fs::read_to_string(&store_path).unwrap(), original);
    }

    #[test]
    fn file_corrupted_after_load_is_not_overwritten() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("marks.json");
        let doc = doc_in(&dir);
        let mut store = MarkStore::load_from(store_path.clone());
        fs::write(&store_path, "garbage").unwrap();
        assert_eq!(store.set(&doc, 'a', anchor(0, "# Doc")).unwrap(), SaveStatus::Unreadable);
        assert_eq!(fs::read_to_string(&store_path).unwrap(), "garbage");
    }

    #[test]
    fn missing_parent_directory_is_created() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("a").join("b").join("marks.json");
        let doc = doc_in(&dir);
        let mut store = MarkStore::load_from(store_path.clone());
        store.set(&doc, 'a', anchor(0, "# Doc")).unwrap();
        assert!(store_path.exists());
        let leftovers = fs::read_dir(store_path.parent().unwrap())
            .unwrap()
            .filter(|e| {
                e.as_ref()
                    .unwrap()
                    .file_name()
                    .to_string_lossy()
                    .ends_with(".tmp")
            })
            .count();
        assert_eq!(leftovers, 0, "temp file must be renamed away");
    }

    #[test]
    fn uncanonicalizable_path_is_memory_only() {
        let dir = tempfile::tempdir().unwrap();
        let store_path = dir.path().join("marks.json");
        let ghost = dir.path().join("does-not-exist.md");
        let mut store = MarkStore::load_from(store_path.clone());
        assert_eq!(store.set(&ghost, 'a', anchor(0, "x")).unwrap(), SaveStatus::Skipped);
        assert_eq!(store.get(&ghost, 'a'), Some(&anchor(0, "x")));
        assert!(!store_path.exists());
    }

    #[test]
    fn in_memory_store_never_writes() {
        let mut store = MarkStore::in_memory();
        let p = std::path::Path::new("doc.md");
        assert_eq!(store.set(p, 'a', anchor(0, "x")).unwrap(), SaveStatus::Skipped);
        assert_eq!(store.get(p, 'a'), Some(&anchor(0, "x")));
    }

    #[cfg(unix)]
    #[test]
    fn write_failure_is_reported_and_mark_kept() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let locked = dir.path().join("locked");
        fs::create_dir(&locked).unwrap();
        let doc = doc_in(&dir);
        let mut store = MarkStore::load_from(locked.join("marks.json"));
        fs::set_permissions(&locked, fs::Permissions::from_mode(0o500)).unwrap();
        let result = store.set(&doc, 'a', anchor(0, "# Doc"));
        fs::set_permissions(&locked, fs::Permissions::from_mode(0o700)).unwrap();
        assert!(result.is_err());
        assert_eq!(store.get(&doc, 'a'), Some(&anchor(0, "# Doc")));
    }
```

- [ ] **Step 3: Run the tests and check they fail**

Run: `cargo test marks::tests::`
Expected: compile error, because `MarkStore` and `SaveStatus` aren't defined. Add them with `todo!()` bodies, re-run, and expect panics.

- [ ] **Step 4: Implement**

Add to `src/marks.rs`:

```rust
use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

const STORE_VERSION: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum SaveStatus {
    Saved,
    Skipped,
    Unreadable,
}

#[derive(Serialize, Deserialize)]
struct StoreFile {
    version: u32,
    files: BTreeMap<String, BTreeMap<char, Anchor>>,
}

impl Default for StoreFile {
    fn default() -> Self {
        StoreFile {
            version: STORE_VERSION,
            files: BTreeMap::new(),
        }
    }
}

enum Disk {
    Missing,
    Valid(StoreFile),
    Unreadable,
}

pub struct MarkStore {
    path: Option<PathBuf>,
    data: StoreFile,
    writable: bool,
    warned: bool,
}

impl MarkStore {
    pub fn load() -> MarkStore {
        match default_path() {
            Some(path) => MarkStore::load_from(path),
            None => MarkStore::in_memory(),
        }
    }

    pub fn load_from(path: PathBuf) -> MarkStore {
        let (data, writable) = match read_disk(&path) {
            Disk::Missing => (StoreFile::default(), true),
            Disk::Valid(data) => (data, true),
            Disk::Unreadable => (StoreFile::default(), false),
        };
        MarkStore {
            path: Some(path),
            data,
            writable,
            warned: false,
        }
    }

    pub fn in_memory() -> MarkStore {
        MarkStore {
            path: None,
            data: StoreFile::default(),
            writable: false,
            warned: true,
        }
    }

    pub fn get(&self, file: &Path, letter: char) -> Option<&Anchor> {
        let (key, _) = file_key(file);
        self.data.files.get(&key)?.get(&letter)
    }

    pub fn set(&mut self, file: &Path, letter: char, anchor: Anchor) -> io::Result<SaveStatus> {
        let (key, persistent) = file_key(file);
        self.data
            .files
            .entry(key.clone())
            .or_default()
            .insert(letter, anchor.clone());

        let Some(path) = self.path.clone().filter(|_| persistent) else {
            return Ok(SaveStatus::Skipped);
        };
        if !self.writable {
            return Ok(self.unreadable_status());
        }

        let mut merged = match read_disk(&path) {
            Disk::Missing => StoreFile::default(),
            Disk::Valid(data) => data,
            Disk::Unreadable => {
                self.writable = false;
                return Ok(self.unreadable_status());
            }
        };
        merged.files.entry(key).or_default().insert(letter, anchor);
        write_atomic(&path, &merged)?;
        self.data = merged;
        Ok(SaveStatus::Saved)
    }

    fn unreadable_status(&mut self) -> SaveStatus {
        if self.warned {
            SaveStatus::Skipped
        } else {
            self.warned = true;
            SaveStatus::Unreadable
        }
    }
}

fn default_path() -> Option<PathBuf> {
    dirs::state_dir()
        .or_else(dirs::data_dir)
        .map(|d| d.join("mdterm").join("marks.json"))
}

/// Canonical path string for persistence, or the given path (memory-only) if it cannot be resolved.
fn file_key(file: &Path) -> (String, bool) {
    match fs::canonicalize(file) {
        Ok(p) => (p.to_string_lossy().into_owned(), true),
        Err(_) => (file.to_string_lossy().into_owned(), false),
    }
}

fn read_disk(path: &Path) -> Disk {
    match fs::read_to_string(path) {
        Err(e) if e.kind() == io::ErrorKind::NotFound => Disk::Missing,
        Err(_) => Disk::Unreadable,
        Ok(text) => match serde_json::from_str::<StoreFile>(&text) {
            Ok(data) if data.version == STORE_VERSION => Disk::Valid(data),
            _ => Disk::Unreadable,
        },
    }
}

fn write_atomic(path: &Path, data: &StoreFile) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = path.with_extension(format!("json.{}.tmp", std::process::id()));
    let json = serde_json::to_string_pretty(data).map_err(io::Error::other)?;
    fs::write(&tmp, json)?;
    fs::rename(&tmp, path).inspect_err(|_| {
        let _ = fs::remove_file(&tmp);
    })
}
```

Notes for the implementer:
- In `in_memory`, `warned: true` means it never reports `Unreadable`. Every `set` on it returns `Skipped`, because `path` is `None`.
- The pid in the temp file name stops two instances from overwriting each other's temp file. `missing_parent_directory_is_created` checks that no `*.tmp` file is left behind.
- The `relative_and_absolute_paths_share_marks` test depends on `canonicalize` resolving `./`. On macOS, `tempdir()` lives under `/var`, which is a symlink to `/private/var`. Canonicalizing both paths handles that.

- [ ] **Step 5: Run all checks**

Run: `cargo test && cargo clippy --all-targets && cargo fmt --check`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add Cargo.toml Cargo.lock src/marks.rs
git commit -m "feat(marks): persist marks per file with atomic writes"
```

---

### Task 5: Viewer integration, keys and docs

**Files:**
- Modify: `src/viewer.rs`:
  - `ViewerOptions` (line 27)
  - `ViewMode` neighborhood (add `MarkOp`, ~line 238)
  - `ViewerState` struct and `new` (lines 283-452)
  - `handle_event` (line 993)
  - `handle_normal` (line 1606, `m` arm at 1647)
  - `render_status_bar` (line 2778)
  - `help_sections` (line 3600-3640)
  - test helper `make_state_with_lines` (line 4250)
- Modify: `src/main.rs:124-132` (`ViewerOptions` construction)
- Modify: `src/marks.rs` (remove `#![allow(dead_code)]`)
- Modify: `README.md` (key tables ~lines 70-110), `CLAUDE.md` (architecture list)
- Test: `src/viewer.rs` tests module

**Interfaces:**
- Consumes: `marks::{Anchor, MarkStore, SaveStatus, source_at_row, row_for_source}` (Tasks 3-4) and `Line.src` (Tasks 1-2).
- Produces: the user-facing feature.

- [ ] **Step 1: Thread the store through `ViewerOptions`**

`src/viewer.rs`:

```rust
pub struct ViewerOptions {
    pub files: Vec<String>,
    pub initial_content: String,
    pub filename: String,
    pub theme: Theme,
    pub slide_mode: bool,
    pub line_numbers: bool,
    pub width_override: Option<usize>,
    pub marks: crate::marks::MarkStore,
}
```

`src/main.rs`, in the interactive branch only:

```rust
            width_override: if width > 0 { Some(width) } else { None },
            marks: marks::MarkStore::load(),
        };
```

In the test helper `make_state_with_lines`, add `marks: crate::marks::MarkStore::in_memory(),`.

Next to `ViewMode`:

```rust
#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkOp {
    Set,
    Jump,
}
```

`ViewerState` fields, placed after `nav_history`:

```rust
    // Marks: persisted per-file anchors and a pending `m` / `'` prefix
    marks: crate::marks::MarkStore,
    pending_mark: Option<MarkOp>,
```

In `ViewerState::new`: `marks: opts.marks, pending_mark: None,`. `opts.files` is moved earlier in `new`, so put `marks: opts.marks` in the struct literal. Partial moves out of `opts` are fine because each field is moved once.

Remove `#![allow(dead_code)]` and its comment from `src/marks.rs`.

- [ ] **Step 2: Write the failing tests**

Add to the `viewer.rs` tests module:

```rust
    // ── Marks ───────────────────────────────────────────────────────────────

    use crossterm::event::KeyEvent;

    // Long enough that every target row sits well above `max_offset` at a
    // 12-row terminal, so jumps are never clamped and assertions stay exact.
    const MARK_DOC: &str = "# Title\n\nIntro paragraph that is long enough to wrap when the terminal gets narrow enough.\n\n## Section A\n\n- parent item\n  - child item that is also fairly long so it wraps at narrow widths\n- sibling\n\n## Section B\n\nClosing text.\n\nFiller 1.\n\nFiller 2.\n\nFiller 3.\n\nFiller 4.\n\nFiller 5.\n\nFiller 6.\n\nFiller 7.\n\nFiller 8.\n\nFiller 9.\n\nFiller 10.\n";

    fn make_doc_state(content: &str, cols: u16) -> ViewerState {
        let opts = ViewerOptions {
            files: vec!["mark-test-doc.md".to_string()],
            initial_content: content.to_string(),
            filename: "mark-test-doc.md".to_string(),
            theme: crate::theme::Theme::dark(),
            slide_mode: false,
            line_numbers: false,
            width_override: None,
            marks: crate::marks::MarkStore::in_memory(),
        };
        let mut state = ViewerState::new(opts, cols, 12);
        state.rebuild();
        state
    }

    fn press(state: &mut ViewerState, c: char) -> bool {
        handle_event(state, Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)))
    }

    fn press_code(state: &mut ViewerState, code: KeyCode, mods: KeyModifiers) -> bool {
        handle_event(state, Event::Key(KeyEvent::new(code, mods)))
    }

    fn row_text(state: &ViewerState, row: usize) -> String {
        state.wrapped[row].spans.iter().map(|s| s.text.as_str()).collect()
    }

    fn row_of(state: &ViewerState, needle: &str) -> usize {
        state
            .wrapped
            .iter()
            .position(|l| l.spans.iter().map(|s| s.text.as_str()).collect::<String>().contains(needle))
            .unwrap()
    }

    fn toast(state: &ViewerState) -> String {
        state.toast.as_ref().map(|(m, _)| m.clone()).unwrap_or_default()
    }

    fn set_mark_at(state: &mut ViewerState, row: usize, letter: char) {
        state.offset = row;
        press(state, 'm');
        press(state, letter);
    }

    #[test]
    fn set_and_jump_round_trip() {
        let mut state = make_doc_state(MARK_DOC, 80);
        let target = row_of(&state, "Section B");
        set_mark_at(&mut state, target, 'a');
        assert_eq!(toast(&state), "Mark a set");
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert!(target < state.max_offset(), "fixture must not clamp");
        assert_eq!(state.offset, target);
        assert_eq!(toast(&state), "Jumped to mark a");
        assert_eq!(state.nav_history.last(), Some(&(0, 0)));
    }

    #[test]
    fn mark_survives_resize() {
        let mut state = make_doc_state(MARK_DOC, 80);
        set_mark_at(&mut state, row_of(&state, "Section B"), 'a');
        state.cols = 40;
        state.rebuild();
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'a');
        let expected = row_of(&state, "Section B");
        assert!(expected < state.max_offset(), "fixture must not clamp");
        assert_eq!(state.offset, expected);
    }

    #[test]
    fn mark_on_nested_list_item_round_trips() {
        let mut state = make_doc_state(MARK_DOC, 80);
        set_mark_at(&mut state, row_of(&state, "child item"), 'c');
        state.cols = 30;
        state.rebuild();
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'c');
        let expected = row_of(&state, "child item");
        assert!(expected < state.max_offset(), "fixture must not clamp");
        assert_eq!(state.offset, expected);
        assert!(row_text(&state, state.offset).contains("child item"));
    }

    #[test]
    fn mark_follows_lines_inserted_above_on_reload() {
        let mut state = make_doc_state(MARK_DOC, 80);
        set_mark_at(&mut state, row_of(&state, "Section B"), 'a');
        state.content = format!("# New top\n\nAdded.\n\n{MARK_DOC}");
        state.rebuild();
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert_eq!(state.offset, row_of(&state, "Section B"));
        assert_eq!(toast(&state), "Jumped to mark a");
        // Re-anchored to the new line.
        let path = std::path::Path::new("mark-test-doc.md");
        let stored = state.marks.get(path, 'a').unwrap();
        assert_eq!(stored.line, state.content.lines().position(|l| l == "## Section B").unwrap());
    }

    #[test]
    fn jump_after_truncation_clamps_and_reports_fallback() {
        let mut state = make_doc_state(MARK_DOC, 80);
        set_mark_at(&mut state, row_of(&state, "Closing text"), 'z');
        state.content = "# Title\n".to_string();
        state.rebuild();
        press(&mut state, '\'');
        press(&mut state, 'z');
        assert!(state.offset <= state.max_offset());
        assert_eq!(toast(&state), "Jumped to mark z (text not found)");
    }

    #[test]
    fn unknown_mark_reports_not_set() {
        let mut state = make_doc_state(MARK_DOC, 80);
        state.offset = 3;
        press(&mut state, '\'');
        press(&mut state, 'q');
        assert_eq!(state.offset, 3);
        assert_eq!(toast(&state), "Mark q not set");
        assert!(state.nav_history.is_empty());
    }

    #[test]
    fn prefix_takes_precedence_over_help_and_quit() {
        let mut state = make_doc_state(MARK_DOC, 80);
        press(&mut state, 'm');
        assert_eq!(state.pending_mark, Some(MarkOp::Set));
        assert!(!press(&mut state, 'h'));
        assert_eq!(state.mode, ViewMode::Normal);
        assert_eq!(toast(&state), "Mark h set");
        press(&mut state, '\'');
        assert!(!press(&mut state, 'q'), "'q after prefix must not quit");
        assert_eq!(state.pending_mark, None);
    }

    #[test]
    fn prefix_then_non_letter_cancels_without_side_effects() {
        let mut state = make_doc_state(MARK_DOC, 80);
        let path = std::path::Path::new("mark-test-doc.md");
        for key in [
            (KeyCode::Char('A'), KeyModifiers::SHIFT),
            (KeyCode::Char('1'), KeyModifiers::NONE),
            (KeyCode::Esc, KeyModifiers::NONE),
            (KeyCode::Char('x'), KeyModifiers::CONTROL),
            (KeyCode::Char('j'), KeyModifiers::ALT),
        ] {
            state.offset = 2;
            state.toast = None;
            press(&mut state, 'm');
            assert!(!press_code(&mut state, key.0, key.1), "{key:?} must not quit");
            assert_eq!(state.pending_mark, None);
            assert_eq!(state.offset, 2, "{key:?} must not scroll");
            assert!(state.toast.is_none(), "{key:?} must cancel silently");
        }
        assert!(state.marks.get(path, 'A').is_none());
        assert!(state.marks.get(path, 'x').is_none());
        assert!(state.marks.get(path, 'j').is_none());
    }

    #[test]
    fn ctrl_c_quits_while_prefix_pending() {
        let mut state = make_doc_state(MARK_DOC, 80);
        press(&mut state, 'm');
        assert!(press_code(&mut state, KeyCode::Char('c'), KeyModifiers::CONTROL));
    }

    #[test]
    fn marks_are_per_file() {
        let mut state = make_doc_state(MARK_DOC, 80);
        set_mark_at(&mut state, row_of(&state, "Section B"), 'a');
        state.files[0] = "other-doc.md".to_string();
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert_eq!(toast(&state), "Mark a not set");
    }

    #[test]
    fn marks_need_a_file() {
        let mut state = make_state_with_lines(vec![]);
        press(&mut state, 'm');
        assert_eq!(state.pending_mark, None);
        assert_eq!(toast(&state), "Marks need a file");
    }

    #[test]
    fn marks_unavailable_in_json_view() {
        let mut state = make_doc_state("{\"a\": 1}", 80);
        state.filename = "data.json".to_string();
        state.cached_json = None;
        state.rebuild();
        assert!(state.json_view.is_some());
        press(&mut state, 'm');
        assert_eq!(state.pending_mark, None);
        assert_eq!(toast(&state), "Marks not available in JSON view");
    }

    #[test]
    fn nothing_to_mark_in_empty_document() {
        let mut state = make_doc_state("", 80);
        press(&mut state, 'm');
        press(&mut state, 'a');
        assert_eq!(toast(&state), "Nothing to mark");
    }

    #[test]
    fn help_lists_mark_keys_and_moved_mouse_toggle() {
        let entries: Vec<&str> = help_sections()
            .iter()
            .flat_map(|s| s.entries.iter().map(|(k, _)| *k))
            .collect();
        assert!(entries.contains(&"m{a-z}"));
        assert!(entries.contains(&"'{a-z}"));
        assert!(entries.contains(&"M"));
        assert!(!entries.contains(&"m"));
    }
```

`handle_event` with `'m'` never touches the terminal, so these tests are safe. Don't send `M` through `handle_event` in tests, because it writes mouse-capture escape sequences to stdout. `help_lists_mark_keys_and_moved_mouse_toggle` covers the rebinding.

- [ ] **Step 3: Run the tests and check they fail**

Run: `cargo test viewer::tests::`
Expected: the new mark tests FAIL (`m` still toggles the mouse, `'` does nothing), and so does the help test. The existing tests still pass.

- [ ] **Step 4: Intercept the pending prefix in `handle_event`**

Directly after the existing Ctrl+C check (line 996-998), before `is_help_toggle`:

```rust
            if let Some(op) = state.pending_mark.take() {
                state.dirty = true;
                let plain = !ke
                    .modifiers
                    .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT);
                if let KeyCode::Char(letter @ 'a'..='z') = ke.code
                    && plain
                {
                    match op {
                        MarkOp::Set => state.set_mark(letter),
                        MarkOp::Jump => state.jump_to_mark(letter),
                    }
                }
                return false;
            }
```

- [ ] **Step 5: Bind `m`, `'` and `M` in `handle_normal`**

Replace the `KeyCode::Char('m') => { ... }` mouse arm (line 1647) with:

```rust
        // Marks
        KeyCode::Char('m') => state.begin_mark(MarkOp::Set),
        KeyCode::Char('\'') => state.begin_mark(MarkOp::Jump),

        // Mouse capture toggle
        KeyCode::Char('M') => {
            let mut stdout = io::stdout();
            if state.mouse_captured {
                let _ = execute!(stdout, DisableMouseCapture);
                state.mouse_captured = false;
                if state.cursor_on_clickable {
                    let _ = queue!(stdout, Print("\x1b]22;default\x07"));
                    let _ = stdout.flush();
                    state.cursor_on_clickable = false;
                }
                state.set_toast("Mouse capture OFF — select text freely");
            } else {
                let _ = execute!(stdout, EnableMouseCapture);
                state.mouse_captured = true;
                state.set_toast("Mouse capture ON — scroll with mouse");
            }
        }
```

This is the old `m` body, unchanged. Its existing toast strings are left as they are, because changing them is out of scope.

- [ ] **Step 6: Implement the `ViewerState` mark methods**

Add to `impl ViewerState` (next to `switch_file`):

```rust
    fn current_path(&self) -> Option<std::path::PathBuf> {
        self.files
            .get(self.current_file_idx)
            .map(std::path::PathBuf::from)
    }

    fn begin_mark(&mut self, op: MarkOp) {
        if self.files.is_empty() {
            self.set_toast("Marks need a file");
        } else if self.json_view.is_some() {
            self.set_toast("Marks not available in JSON view");
        } else {
            self.pending_mark = Some(op);
        }
    }

    fn set_mark(&mut self, letter: char) {
        let Some(path) = self.current_path() else {
            return;
        };
        let Some(byte) = crate::marks::source_at_row(&self.wrapped, self.offset) else {
            self.set_toast("Nothing to mark");
            return;
        };
        let anchor = crate::marks::Anchor::capture(&self.content, byte);
        let msg = match self.marks.set(&path, letter, anchor) {
            Ok(crate::marks::SaveStatus::Unreadable) => {
                "Marks file unreadable - not saving".to_string()
            }
            Ok(_) => format!("Mark {letter} set"),
            Err(_) => "Could not save marks".to_string(),
        };
        self.set_toast(msg);
    }

    fn jump_to_mark(&mut self, letter: char) {
        let Some(path) = self.current_path() else {
            return;
        };
        let Some(anchor) = self.marks.get(&path, letter).cloned() else {
            self.set_toast(format!("Mark {letter} not set"));
            return;
        };
        let resolved = anchor.resolve(&self.content);
        let Some(row) = crate::marks::row_for_source(&self.wrapped, resolved.byte) else {
            self.set_toast(format!("Mark {letter} not set"));
            return;
        };
        self.nav_history.push((self.current_file_idx, self.offset));
        self.offset = row.min(self.max_offset());
        if !resolved.exact {
            self.set_toast(format!("Jumped to mark {letter} (text not found)"));
            return;
        }
        if resolved.line != anchor.line {
            let moved = crate::marks::Anchor {
                line: resolved.line,
                text: anchor.text,
            };
            // The jump already succeeded; a failed re-anchor save is retried on the next jump.
            let _ = self.marks.set(&path, letter, moved);
        }
        self.set_toast(format!("Jumped to mark {letter}"));
    }
```

- [ ] **Step 7: Show the status hint**

In `render_status_bar`, directly after the `if state.mode == ViewMode::Search { ... }` block, add the same layout with the prefix label:

```rust
    if let Some(op) = state.pending_mark {
        let label = match op {
            MarkOp::Set => " m- ",
            MarkOp::Jump => " '- ",
        };
        let fill = width.saturating_sub(3 + label.chars().count());
        queue!(
            stdout,
            MoveTo(0, (viewport + 1) as u16),
            SetBackgroundColor(theme.bg),
            SetForegroundColor(theme.border),
            Print("╰─"),
            SetForegroundColor(theme.search_prompt),
            Print(label),
            SetForegroundColor(theme.border),
            Print("─".repeat(fill)),
            Print("╯"),
            SetAttribute(Attribute::Reset),
        )?;
        return Ok(());
    }
```

- [ ] **Step 8: Update the help overlay**

In `help_sections`, under "Navigation", after `("Backspace", ...)`:

```rust
                ("m{a-z}", "Set mark at current position"),
                ("'{a-z}", "Jump to mark (Backspace returns)"),
```

Under "Actions", change `("m", "Toggle mouse capture (for text select)")` to `("M", "Toggle mouse capture (for text select)")`.

- [ ] **Step 9: Run all checks**

Run: `cargo test && cargo clippy --all-targets && cargo fmt --check`
Expected: all pass, zero warnings. If `help_box_dimensions` tests depend on the number of entries, they compute it from `help_sections()`, so they adapt.

- [ ] **Step 10: Update README.md and CLAUDE.md**

`README.md`, in the "Navigation" key table, after the `Backspace` row:

```markdown
| `m` + `a`-`z` | Set a mark at the current position |
| `'` + `a`-`z` | Jump to a mark (`Backspace` returns) |
```

In the features/actions key table, after the `l` row:

```markdown
| `M` | Toggle mouse capture (for selecting text) |
```

Below the key tables, add:

```markdown
### Marks

Marks are saved per file and survive restarts. They follow their text when the file is edited, and are stored in `~/.local/state/mdterm/marks.json` on Linux and `~/Library/Application Support/mdterm/marks.json` on macOS.
```

`CLAUDE.md`:
- Change "Ten source files in `src/`" to "Eleven source files in `src/`".
- Add this bullet after `diagram.rs`:

  `- **marks.rs** - Persistent per-file marks. \`Anchor\` captures a source line (number + trimmed text) and resolves it against edited content; \`MarkStore\` loads/saves \`marks.json\` (state dir) with atomic writes and never overwrites an unreadable file. Rows map to source via \`Line.src\`.`
- In the `style.rs` bullet, mention that `Line.src` carries the source byte offset through wrapping.

- [ ] **Step 11: Commit**

```bash
git add src/viewer.rs src/main.rs src/marks.rs README.md CLAUDE.md
git commit -m "feat(viewer): add m/' marks and move mouse toggle to M"
```

---

### Task 6: End-to-end verification in a real terminal

**Files:** none changed, unless a defect is found. If one is, write a failing test in the owning task's module first, fix it, and commit `fix(marks): ...`.

**Interfaces:** consumes the built binary.

Use a scratch `HOME` (Linux) or the real state dir (macOS: back up `~/Library/Application Support/mdterm/marks.json` if it exists) and drive the TUI through `tmux`, so every step can be read back with `capture-pane`.

- [ ] **Step 1: Build and prepare**

```bash
cargo build --release
cp README.md /tmp/marks-e2e.md
tmux new-session -d -s marks -x 100 -y 30 "./target/release/mdterm /tmp/marks-e2e.md"
```

- [ ] **Step 2: Set, resize, toggle, jump**

1. `tmux send-keys -t marks G` then `k` x5. Read the top content row with `tmux capture-pane -pt marks | sed -n 2p`.
2. Send `m`, `a`, and confirm the status bar showed `m-` before the `a` (capture between the two keys) and the toast `Mark a set` after.
3. `tmux resize-window -t marks -x 60`, send `l` (line numbers) and `t` (theme), then `g`, `'`, `a`.
4. Confirm the top row shows the same block as in item 1 and the toast is `Jumped to mark a`.
5. Send `Backspace` and confirm it returns to the top.

- [ ] **Step 3: Edit above the mark while open**

1. In another shell: `printf '# Inserted\n\nNew paragraph.\n\n' | cat - /tmp/marks-e2e.md > /tmp/x && mv /tmp/x /tmp/marks-e2e.md`
2. Wait for the `File reloaded` toast, send `'`, `a`, and confirm it lands on the same block (not 4 lines early).

- [ ] **Step 4: Persistence across restart**

`tmux send-keys -t marks q`, start mdterm again in the same session, send `'`, `a`, and confirm the jump. `cat` the marks file and confirm it contains `version: 1`, the canonical path of `/tmp/marks-e2e.md` (`<tmp>` on macOS) and `"a"`.

- [ ] **Step 5: Corrupt store**

`printf '{ broken' > <marks.json path>`, restart, send `m`, `b`, and confirm the toast `Marks file unreadable - not saving`. Run `cat` and confirm the file is still `{ broken`. Send `'`, `b` and confirm it still jumps within the session.

- [ ] **Step 6: Mouse toggle and guards**

1. Send `M` and confirm `Mouse capture OFF`. Send `m`, `Esc` and confirm nothing happens.
2. Run `cat README.md | ./target/release/mdterm` in tmux, send `m`, and confirm `Marks need a file`.
3. Open a `.json` file, send `m`, and confirm `Marks not available in JSON view`.

- [ ] **Step 7: Clean up**

Restore any backed-up marks file, `tmux kill-session -t marks`, and remove `/tmp/marks-e2e.md`. Report what was observed at each step, including anything that looked off visually (status hint alignment, toast clipping at 60 columns).
