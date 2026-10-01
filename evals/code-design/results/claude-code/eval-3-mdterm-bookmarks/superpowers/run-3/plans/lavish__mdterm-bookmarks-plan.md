# mdterm Bookmarks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vim-style per-file marks (`m` + `a-z` sets, `'` + `a-z` jumps) that are saved between sessions and still land on the same passage after resizes and edits.

**Architecture:** Every rendered `Line` carries the 1-based source line it came from (`source_line`). A mark stores that source line plus its trimmed text, in `marks.toml` under the data directory. At jump time a pure `resolve` function maps the mark back to a source line, and the viewer scrolls to the first wrapped line at or after it. All mark logic and I/O lives in a new `src/marks.rs`. `viewer.rs` only adds a one-key prefix and two small handlers.

**Tech Stack:** Rust 2024, pulldown-cmark 0.11 (`into_offset_iter`), serde + toml 0.8, dirs 5, crossterm 0.28. New dev-dependency: `tempfile = "3"`.

**Spec:** `.lavish/mdterm-bookmarks.md` (approved). Read it alongside this plan.

## Global Constraints

- Marks file: `dirs::data_dir()/mdterm/marks.toml`. Never under the config dir.
- Mark letters: lowercase ASCII `a-z` only, with no Ctrl/Alt modifier.
- Source lines are 1-based everywhere (`Line::source_line`, `Mark::line`, `Resolved::line`).
- Mouse capture toggle moves from `m` to `M`. Behavior is otherwise unchanged.
- Toast strings, verbatim:
  - `Mark 'a' set`
  - `Jumped to 'a'`
  - `Mark 'a' moved - nearest position`
  - `Mark 'a' not set`
  - `Marks unavailable for stdin`
  - `Marks unavailable in JSON view`
  - `Marks unavailable in slide mode`
  - `marks.toml unreadable - marks not saved`
  - `Could not save mark: <reason>`
  - `Nothing to mark here` (added by this plan, see Review Focus)
- An unparseable `marks.toml` is never overwritten.
- Saves are a re-read, a one-entry update, then write `marks.toml.tmp` and `rename`.
- A jump pushes `(current_file_idx, offset)` onto `nav_history`.
- `cargo fmt`, `cargo clippy` and `cargo test` must be clean at the end of every task. The one exception is the `dead_code` warnings for `marks.rs` in Tasks 3-4, which Task 5 clears.
- Commit after each task, using the `/commit` skill if available.

## Review Focus

These five inputs follow from the spec but no spec test covers them. They're the ones most likely to bite a user:

1. **`Ctrl+c` while a mark prefix is pending** must still quit, as it does everywhere else. Test in Task 5.
2. **`q` or `Esc` while a prefix is pending** must only cancel the prefix, not quit the viewer. Test in Task 5.
3. **Two files open with Tab switching:** a mark set in file A must not exist in file B. Test in Task 5.
4. **CRLF files:** text fingerprints must match even though lines end in `\r\n`. Test in Task 3.
5. **Empty document, or nothing with a source line at or below the top of the screen:** `m a` must not panic. It shows `Nothing to mark here`. Test in Task 5.

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `src/style.rs` | Modify | `Line.source_line` field. `wrap_lines` copies it to every wrapped piece. |
| `src/markdown.rs` | Modify | Builds the line-start table and stamps `source_line` on every emitted line. Precise per-line values for code blocks and table rows. |
| `src/marks.rs` | Create | `Mark`, `Resolved`, `resolve`, `MarkStore`, `SaveError`. No terminal code. |
| `src/main.rs` | Modify | `mod marks;` |
| `src/json.rs` | Modify | `source_line: None` on `Line` literals (mechanical). |
| `src/viewer.rs` | Modify | `MarkOp`, `pending_mark`, `marks`, prefix handling, `set_mark`, `jump_to_mark`, `M` rebind, help entries, image-row propagation. |
| `Cargo.toml` | Modify | `[dev-dependencies] tempfile = "3"` |
| `README.md`, `CLAUDE.md` | Modify | Keybindings and architecture list. |

---

### Task 1: `source_line` on `Line`, kept through wrapping

**Files:**
- Modify: `src/style.rs:56-67` (struct + `Line::empty`), `src/style.rs:89-145` (`wrap_lines`), the other `Line { .. }` literals in `src/style.rs`
- Modify: every `Line { .. }` literal in `src/markdown.rs` (14), `src/json.rs` (17), `src/viewer.rs` (3, including test helper `line()` at ~4274)
- Modify: `src/viewer.rs:639` (image row expansion in `finalize_layout`)
- Test: `src/style.rs` `#[cfg(test)]` module (add one if missing)

**Interfaces:**
- Produces: `pub struct Line { pub spans: Vec<StyledSpan>, pub meta: LineMeta, pub source_line: Option<usize> }`. `wrap_lines(&[Line], usize) -> Vec<Line>` sets every output piece's `source_line` to its input line's value.

- [ ] **Step 1: Write the failing tests** in `src/style.rs`:

```rust
#[cfg(test)]
mod source_line_tests {
    use super::*;

    fn text_line(text: &str, source_line: Option<usize>) -> Line {
        Line {
            spans: vec![StyledSpan {
                text: text.to_string(),
                style: Style::default(),
            }],
            meta: LineMeta::None,
            source_line,
        }
    }

    #[test]
    fn wrap_copies_source_line_to_every_piece() {
        let long = "word ".repeat(30);
        let wrapped = wrap_lines(&[text_line(&long, Some(7))], 20);
        assert!(wrapped.len() > 1);
        assert!(wrapped.iter().all(|l| l.source_line == Some(7)));
    }

    #[test]
    fn wrap_copies_source_line_in_blockquotes() {
        let line = Line {
            spans: vec![
                StyledSpan {
                    text: BLOCKQUOTE_PREFIX.to_string(),
                    style: Style::default(),
                },
                StyledSpan {
                    text: "quoted ".repeat(20),
                    style: Style::default(),
                },
            ],
            meta: LineMeta::None,
            source_line: Some(3),
        };
        let wrapped = wrap_lines(&[line], 20);
        assert!(wrapped.len() > 1);
        assert!(wrapped.iter().all(|l| l.source_line == Some(3)));
    }

    #[test]
    fn short_line_keeps_source_line() {
        let wrapped = wrap_lines(&[text_line("short", Some(1))], 20);
        assert_eq!(wrapped[0].source_line, Some(1));
    }
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test source_line_tests`
Expected: compile error `struct Line has no field named source_line`.

- [ ] **Step 3: Add the field and update `Line::empty`**

```rust
#[derive(Clone, Debug, Default)]
pub struct Line {
    pub spans: Vec<StyledSpan>,
    pub meta: LineMeta,
    /// 1-based line in the source document this rendered line came from.
    pub source_line: Option<usize>,
}

impl Line {
    pub fn empty() -> Self {
        Line {
            spans: vec![],
            meta: LineMeta::None,
            source_line: None,
        }
    }
```

- [ ] **Step 4: Copy `source_line` in `wrap_lines`.** In the blockquote branch, after `w.meta = line.meta.clone();` add `w.source_line = line.source_line;`. In the general branch, add this right after `let mut wrapped = word_wrap(line, width);`:

```rust
            for w in &mut wrapped {
                w.source_line = line.source_line;
            }
```

The short-line branch already clones the whole line.

- [ ] **Step 5: Fix every remaining literal.** Run `cargo build 2>&1 | grep -A3 "missing field"`. Add `source_line: None,` to every reported `Line { .. }` literal in `style.rs`, `markdown.rs`, `json.rs` and `viewer.rs`. Task 2 replaces the `markdown.rs` values. One exception: the image row expansion in `finalize_layout` (`src/viewer.rs:639`) uses the original row's value:

```rust
                let source_line = self.wrapped[i].source_line;
                for r in 0..actual_rows {
                    new_wrapped.push(Line {
                        spans: vec![],
                        meta: LineMeta::Image {
                            url: url.clone(),
                            alt: alt.clone(),
                            row: r,
                            total_rows: actual_rows,
                        },
                        source_line,
                    });
                }
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cargo test`
Expected: all tests pass, including the 3 new ones.

- [ ] **Step 7: Lint and commit**

```bash
cargo fmt && cargo clippy
git add src/style.rs src/markdown.rs src/json.rs src/viewer.rs
git commit -m "feat(style): track source line on rendered lines"
```

---

### Task 2: Markdown renderer fills in `source_line`

**Files:**
- Modify: `src/markdown.rs`: `Renderer` struct (lines 16-70), `Renderer::new` (80-126), `flush_line_with_meta` (189-204), `emit_code_block` (228-420), `emit_table` (527-703), `process` arms for `CodeBlock` (837-849) and tables (971-998), `render_with` loop (1585-1589)
- Test: `src/markdown.rs` `mod tests` (from line 1598)

**Interfaces:**
- Consumes: `Line::source_line` (Task 1).
- Produces: every line returned by `markdown::render` / `render_with` has `source_line: Some(n)` with `1 <= n <= line count`. The value is the source line where that rendered line's content starts. Code block content line `i` maps to its own source line, and each table row maps to its own source line.

- [ ] **Step 1: Write the failing tests** at the end of `mod tests` in `src/markdown.rs`:

```rust
    // ── Source lines ────────────────────────────────────────────────────────

    fn source_of(lines: &[Line], needle: &str) -> Option<usize> {
        lines
            .iter()
            .find(|l| line_text(l).contains(needle))
            .and_then(|l| l.source_line)
    }

    #[test]
    fn source_line_headings_and_paragraphs() {
        let (lines, _) = render_test("# Title\n\nFirst para\nsecond line\n\n## Next\n");
        assert_eq!(source_of(&lines, "Title"), Some(1));
        assert_eq!(source_of(&lines, "First para"), Some(3));
        assert_eq!(source_of(&lines, "Next"), Some(6));
    }

    #[test]
    fn source_line_list_items() {
        let (lines, _) = render_test("- one\n- two\n  - nested\n");
        assert_eq!(source_of(&lines, "one"), Some(1));
        assert_eq!(source_of(&lines, "two"), Some(2));
        assert_eq!(source_of(&lines, "nested"), Some(3));
    }

    #[test]
    fn source_line_code_block_per_line() {
        let (lines, _) = render_test("Intro\n\n```rust\nlet a = 1;\nlet b = 2;\n```\n");
        assert_eq!(source_of(&lines, "╭"), Some(3));
        assert_eq!(source_of(&lines, "let a"), Some(4));
        assert_eq!(source_of(&lines, "let b"), Some(5));
        assert_eq!(source_of(&lines, "╰"), Some(6));
    }

    #[test]
    fn source_line_indented_code_block() {
        let (lines, _) = render_test("Intro\n\n    first\n    second\n");
        assert_eq!(source_of(&lines, "first"), Some(3));
        assert_eq!(source_of(&lines, "second"), Some(4));
    }

    #[test]
    fn source_line_table_rows() {
        let (lines, _) = render_test("| A | B |\n|---|---|\n| x | y |\n| z | w |\n");
        assert_eq!(source_of(&lines, "A"), Some(1));
        assert_eq!(source_of(&lines, "x"), Some(3));
        assert_eq!(source_of(&lines, "z"), Some(4));
    }

    #[test]
    fn every_line_has_a_source_line() {
        let input = "# H\n\npara\n\n> quote\n\n- item\n\n---\n\n```\ncode\n```\n\n| a |\n|---|\n| b |\n";
        let (lines, _) = render_test(input);
        let count = input.lines().count();
        for line in &lines {
            let n = line.source_line.expect("missing source_line");
            assert!((1..=count).contains(&n), "out of range: {n}");
        }
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test source_line`
Expected: FAIL. The values are `None`, because Task 1 set every literal to `None`.

- [ ] **Step 3: Add renderer state and helpers.** Add these fields to `Renderer`:

```rust
    // Source line tracking
    line_starts: Vec<usize>,
    line_count: usize,
    current_src: Option<usize>,
    code_block_first_line: usize,
    code_block_fenced: bool,
    table_row_lines: Vec<usize>,
```

Initialize them in `Renderer::new`: `line_starts: line_starts(source)`, `line_count: source.lines().count().max(1)`, `current_src: None`, `code_block_first_line: 1`, `code_block_fenced: false`, `table_row_lines: Vec::new()`. Then add these to `impl Renderer`:

```rust
    /// 1-based source line containing `byte`. Clamped so an event at the very
    /// end of a newline-terminated input maps to the last real line.
    fn line_of(&self, byte: usize) -> usize {
        self.line_starts
            .partition_point(|&start| start <= byte)
            .min(self.line_count)
    }

    /// Give lines pushed since `from` the source line of the event that
    /// produced them, unless they already have one, and remember where the
    /// pending span buffer started.
    fn stamp_new_lines(&mut self, from: usize, line: usize) {
        for l in &mut self.lines[from..] {
            l.source_line.get_or_insert(line);
        }
        if self.current_src.is_none() && !self.current_spans.is_empty() {
            self.current_src = Some(line);
        }
    }
```

And this free function:

```rust
fn line_starts(source: &str) -> Vec<usize> {
    std::iter::once(0)
        .chain(source.match_indices('\n').map(|(i, _)| i + 1))
        .collect()
}
```

- [ ] **Step 4: Stamp in the event loop and in `flush_line_with_meta`.** Replace the loop in `render_with`:

```rust
    for (event, range) in parser.into_offset_iter() {
        let from = renderer.lines.len();
        let line = renderer.line_of(range.start);
        renderer.process(event, range);
        renderer.stamp_new_lines(from, line);
    }
```

In `flush_line_with_meta`, take the recorded source line for the buffered spans. A paragraph's text is often flushed by a later event, such as the start of a nested list, and this keeps it from picking up that event's line:

```rust
            spans.append(&mut self.current_spans);
            let source_line = self.current_src.take();
            self.lines.push(Line {
                spans,
                meta,
                source_line,
            });
```

- [ ] **Step 5: Code blocks get one source line per line.** In `process`, change `Event::Start(Tag::CodeBlock(kind))`:

```rust
            Event::Start(Tag::CodeBlock(kind)) => {
                self.in_code_block = true;
                self.code_block_fenced = matches!(kind, CodeBlockKind::Fenced(_));
                self.code_block_first_line =
                    self.line_of(source_range.start) + usize::from(self.code_block_fenced);
                self.code_block_lang = match kind {
                    CodeBlockKind::Fenced(lang) => lang.to_string(),
                    CodeBlockKind::Indented => String::new(),
                };
                self.code_block_content.clear();
            }
```

In `emit_code_block`, after `let block_id = ...;`, add:

```rust
        let first_line = self.code_block_first_line;
        let fence_line = first_line - usize::from(self.code_block_fenced);
```

Set `source_line: Some(fence_line)` on the top border. Set `source_line: Some(first_line + line_num)` on each code line inside `for (line_num, line_str) in ...`. Set this on the bottom border:

```rust
            source_line: Some(
                first_line + code.lines().count().max(1) - 1 + usize::from(self.code_block_fenced),
            ),
```

`emit_diagram_block` (mermaid) keeps `None` and gets the default stamp, the event's start line. A diagram has no per-line mapping.

- [ ] **Step 6: Table rows get one source line per row.** In `process`:

```rust
            Event::Start(Tag::Table(alignments)) => {
                self.in_table = true;
                self.table_alignments = alignments;
                self.table_head.clear();
                self.table_rows.clear();
                self.table_row_lines.clear();
            }
```

Add `self.table_row_lines.clear();` to `End(TagEnd::Table)` after `emit_table()`. Push `self.table_row_lines.push(self.line_of(source_range.start));` in both `Start(Tag::TableHead)` and `Start(Tag::TableRow)`. In `emit_table`, after `num_cols` is known, add:

```rust
        let row_line = |idx: usize| self.table_row_lines.get(idx).copied();
        let last_row_line = self.table_row_lines.last().copied();
```

Then make the pushes use them. `row_line` borrows `self`, so collect each value into a local before `self.lines.push`:

```rust
        let mut top = make_rule("╭", "┬", "╮", &col_widths);
        top.source_line = row_line(0);
        self.lines.push(top);
        // inside the row loop, per visual line:
        let source_line = row_line(row_idx);
        self.lines.push(Line { spans, meta: LineMeta::None, source_line });
        // separator after a row:
        let mut sep = make_rule("├", "┼", "┤", &col_widths);
        sep.source_line = row_line(row_idx);
        self.lines.push(sep);
        // bottom:
        let mut bottom = make_rule("╰", "┴", "╯", &col_widths);
        bottom.source_line = last_row_line;
        self.lines.push(bottom);
```

If the borrow checker rejects the `row_line` closure while `self.lines` is mutably borrowed, replace it with `let row_lines = self.table_row_lines.clone();` and index `row_lines.get(idx).copied()`.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cargo test`
Expected: all pass, including the 6 new `source_line` tests and every existing markdown test.

- [ ] **Step 8: Lint and commit**

```bash
cargo fmt && cargo clippy
git add src/markdown.rs
git commit -m "feat(markdown): stamp source lines on rendered output"
```

---

### Task 3: `marks::resolve`

**Files:**
- Create: `src/marks.rs`
- Modify: `src/main.rs` (add `mod marks;` after `mod markdown;`)
- Test: `src/marks.rs` `#[cfg(test)] mod tests`

**Interfaces:**
- Produces:
  - `pub struct Mark { pub line: usize, pub text: String }` (derives `Serialize, Deserialize, Clone, PartialEq, Debug`)
  - `pub struct Resolved { pub line: usize, pub exact: bool }` (derives `PartialEq, Debug`)
  - `pub fn resolve(mark: &Mark, source: &str) -> Resolved`

- [ ] **Step 1: Write the failing tests.** Create `src/marks.rs` with only the tests and `use super::*;`, and add `mod marks;` to `main.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn mark(line: usize, text: &str) -> Mark {
        Mark {
            line,
            text: text.to_string(),
        }
    }

    fn at(line: usize, exact: bool) -> Resolved {
        Resolved { line, exact }
    }

    #[test]
    fn exact_line_and_text() {
        assert_eq!(resolve(&mark(2, "two"), "one\ntwo\nthree\n"), at(2, true));
    }

    #[test]
    fn text_moved_down() {
        let src = "new\nnew\none\ntwo\nthree\n";
        assert_eq!(resolve(&mark(2, "two"), src), at(4, true));
    }

    #[test]
    fn text_moved_up() {
        assert_eq!(resolve(&mark(5, "three"), "one\nthree\n"), at(2, true));
    }

    #[test]
    fn matches_on_trimmed_text() {
        assert_eq!(resolve(&mark(1, "two"), "one\n   two  \n"), at(2, true));
    }

    #[test]
    fn duplicate_text_picks_nearest() {
        let src = "x\nfoo\nx\nx\nx\nx\nfoo\nx\n";
        assert_eq!(resolve(&mark(6, "foo"), src), at(7, true));
    }

    #[test]
    fn tie_prefers_earlier_line() {
        let src = "foo\nx\nfoo\n";
        assert_eq!(resolve(&mark(2, "foo"), src), at(1, true));
    }

    #[test]
    fn missing_text_falls_back_to_line() {
        assert_eq!(resolve(&mark(2, "gone"), "a\nb\nc\n"), at(2, false));
    }

    #[test]
    fn missing_text_past_end_is_clamped() {
        assert_eq!(resolve(&mark(10, "gone"), "a\nb\n"), at(2, false));
    }

    #[test]
    fn blank_text_uses_line_only() {
        assert_eq!(resolve(&mark(2, ""), "a\n\nc\n"), at(2, true));
        assert_eq!(resolve(&mark(9, ""), "a\n\nc\n"), at(3, false));
    }

    #[test]
    fn empty_document() {
        assert_eq!(resolve(&mark(4, "x"), ""), at(1, false));
    }

    #[test]
    fn crlf_lines_match() {
        assert_eq!(resolve(&mark(1, "two"), "one\r\ntwo\r\n"), at(2, true));
    }
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test marks::tests`
Expected: compile error, `cannot find type Mark` / `cannot find function resolve`.

- [ ] **Step 3: Implement** at the top of `src/marks.rs`:

```rust
use serde::{Deserialize, Serialize};

/// A saved position: 1-based source line plus that line's trimmed text.
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct Mark {
    pub line: usize,
    pub text: String,
}

#[derive(PartialEq, Debug)]
pub struct Resolved {
    pub line: usize,
    /// False when the marked text was not found and the stored line was used.
    pub exact: bool,
}

/// Map a mark onto the current source: the line whose trimmed text matches,
/// nearest to the stored line (earlier wins a tie), else the stored line.
pub fn resolve(mark: &Mark, source: &str) -> Resolved {
    let lines: Vec<&str> = source.lines().collect();
    let clamped = mark.line.clamp(1, lines.len().max(1));
    if mark.text.is_empty() {
        return Resolved {
            line: clamped,
            exact: clamped == mark.line,
        };
    }
    lines
        .iter()
        .enumerate()
        .filter(|(_, l)| l.trim() == mark.text)
        .map(|(i, _)| i + 1)
        .min_by_key(|&n| n.abs_diff(mark.line))
        .map_or(
            Resolved {
                line: clamped,
                exact: false,
            },
            |line| Resolved { line, exact: true },
        )
}
```

`Iterator::min_by_key` returns the first of several equal minimums, so on a tie the earlier line wins. `str::lines` strips the `\r` in `\r\n`. Non-empty text with no match, including in an empty document, always gives `exact: false`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cargo test marks::tests`
Expected: 11 passed. `cargo build` shows `dead_code` warnings for `marks.rs`, which is expected until Task 5.

- [ ] **Step 5: Commit**

```bash
cargo fmt
git add src/marks.rs src/main.rs
git commit -m "feat(marks): resolve marks against edited source"
```

---

### Task 4: `MarkStore` persistence

**Files:**
- Modify: `src/marks.rs`
- Modify: `Cargo.toml` (add `[dev-dependencies]` with `tempfile = "3"`)
- Test: `src/marks.rs` `mod store_tests`

**Interfaces:**
- Consumes: `Mark` (Task 3).
- Produces:
  - `pub struct MarkStore`
  - `MarkStore::load() -> Self` (uses `dirs::data_dir()/mdterm/marks.toml`)
  - `MarkStore::load_from(path: PathBuf) -> Self`
  - `MarkStore::get(&self, file: &Path, letter: char) -> Option<&Mark>`
  - `MarkStore::set(&mut self, file: &Path, letter: char, mark: Mark) -> Result<(), SaveError>`
  - `pub enum SaveError { NoDataDir, Unreadable, Io(std::io::Error) }`, implementing `Display`

- [ ] **Step 1: Add the dev-dependency** to `Cargo.toml`:

```toml
[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 2: Write the failing tests** in `src/marks.rs`:

```rust
#[cfg(test)]
mod store_tests {
    use super::*;
    use std::fs;

    fn mark(line: usize, text: &str) -> Mark {
        Mark {
            line,
            text: text.to_string(),
        }
    }

    fn setup() -> (tempfile::TempDir, PathBuf, PathBuf) {
        let dir = tempfile::tempdir().unwrap();
        let doc = dir.path().join("doc.md");
        fs::write(&doc, "# doc\n").unwrap();
        let store = dir.path().join("data").join("mdterm").join("marks.toml");
        (dir, doc, store)
    }

    #[test]
    fn set_then_reload() {
        let (_dir, doc, path) = setup();
        let mut store = MarkStore::load_from(path.clone());
        store.set(&doc, 'a', mark(3, "hello")).unwrap();
        assert_eq!(store.get(&doc, 'a'), Some(&mark(3, "hello")));
        let reloaded = MarkStore::load_from(path);
        assert_eq!(reloaded.get(&doc, 'a'), Some(&mark(3, "hello")));
        assert_eq!(reloaded.get(&doc, 'b'), None);
    }

    #[test]
    fn creates_missing_directories() {
        let (_dir, doc, path) = setup();
        assert!(!path.parent().unwrap().exists());
        MarkStore::load_from(path.clone())
            .set(&doc, 'a', mark(1, "x"))
            .unwrap();
        assert!(path.exists());
        assert!(!path.with_extension("toml.tmp").exists());
    }

    #[test]
    fn overwriting_a_letter_replaces_it() {
        let (_dir, doc, path) = setup();
        let mut store = MarkStore::load_from(path.clone());
        store.set(&doc, 'a', mark(1, "old")).unwrap();
        store.set(&doc, 'a', mark(9, "new")).unwrap();
        assert_eq!(MarkStore::load_from(path).get(&doc, 'a'), Some(&mark(9, "new")));
    }

    #[test]
    fn two_stores_merge_instead_of_clobbering() {
        let (dir, doc, path) = setup();
        let other = dir.path().join("other.md");
        fs::write(&other, "x\n").unwrap();
        let mut first = MarkStore::load_from(path.clone());
        let mut second = MarkStore::load_from(path.clone());
        first.set(&doc, 'a', mark(1, "a")).unwrap();
        second.set(&other, 'b', mark(2, "b")).unwrap();
        let reloaded = MarkStore::load_from(path);
        assert_eq!(reloaded.get(&doc, 'a'), Some(&mark(1, "a")));
        assert_eq!(reloaded.get(&other, 'b'), Some(&mark(2, "b")));
    }

    #[test]
    fn paths_are_canonicalized() {
        let (dir, doc, path) = setup();
        let mut store = MarkStore::load_from(path);
        store.set(&doc, 'a', mark(1, "x")).unwrap();
        let indirect = dir.path().join(".").join("doc.md");
        assert_eq!(store.get(&indirect, 'a'), Some(&mark(1, "x")));
    }

    #[test]
    fn corrupt_file_is_never_overwritten() {
        let (_dir, doc, path) = setup();
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(&path, "not [valid toml").unwrap();
        let mut store = MarkStore::load_from(path.clone());
        let err = store.set(&doc, 'a', mark(1, "x")).unwrap_err();
        assert!(matches!(err, SaveError::Unreadable));
        assert_eq!(fs::read_to_string(&path).unwrap(), "not [valid toml");
        assert_eq!(store.get(&doc, 'a'), Some(&mark(1, "x")));
    }

    #[test]
    fn file_corrupted_after_load_is_not_overwritten() {
        let (_dir, doc, path) = setup();
        let mut store = MarkStore::load_from(path.clone());
        store.set(&doc, 'a', mark(1, "x")).unwrap();
        fs::write(&path, "garbage = [").unwrap();
        assert!(matches!(store.set(&doc, 'b', mark(2, "y")), Err(SaveError::Unreadable)));
        assert_eq!(fs::read_to_string(&path).unwrap(), "garbage = [");
    }
}
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cargo test marks::store_tests`
Expected: compile error, `cannot find type MarkStore`.

- [ ] **Step 4: Implement.** Extend the imports at the top of `src/marks.rs`, then add the store below `resolve`:

```rust
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fmt;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

/// Letter -> mark. Keys are one-letter strings because TOML keys are strings.
type FileMarks = BTreeMap<String, Mark>;
/// Canonical file path -> that file's marks.
type AllMarks = BTreeMap<String, FileMarks>;

#[derive(Debug)]
pub enum SaveError {
    NoDataDir,
    Unreadable,
    Io(io::Error),
}

impl fmt::Display for SaveError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            SaveError::NoDataDir => write!(f, "no data directory"),
            SaveError::Unreadable => write!(f, "marks.toml unreadable"),
            SaveError::Io(e) => write!(f, "{e}"),
        }
    }
}

impl From<io::Error> for SaveError {
    fn from(e: io::Error) -> Self {
        SaveError::Io(e)
    }
}

pub struct MarkStore {
    path: Option<PathBuf>,
    /// False once the file on disk failed to parse; it is then never written.
    writable: bool,
    files: AllMarks,
}

impl MarkStore {
    pub fn load() -> Self {
        match dirs::data_dir() {
            Some(dir) => Self::load_from(dir.join("mdterm").join("marks.toml")),
            None => MarkStore {
                path: None,
                writable: false,
                files: AllMarks::new(),
            },
        }
    }

    pub fn load_from(path: PathBuf) -> Self {
        let loaded = read(&path);
        MarkStore {
            path: Some(path),
            writable: loaded.is_some(),
            files: loaded.unwrap_or_default(),
        }
    }

    pub fn get(&self, file: &Path, letter: char) -> Option<&Mark> {
        self.files.get(&file_key(file))?.get(&letter.to_string())
    }

    /// Record the mark in memory, then persist it. The in-memory mark is kept
    /// even when saving fails, so it still works for this session.
    pub fn set(&mut self, file: &Path, letter: char, mark: Mark) -> Result<(), SaveError> {
        let key = file_key(file);
        let letter = letter.to_string();
        self.files
            .entry(key.clone())
            .or_default()
            .insert(letter.clone(), mark.clone());

        let path = self.path.clone().ok_or(SaveError::NoDataDir)?;
        if !self.writable {
            return Err(SaveError::Unreadable);
        }
        let Some(mut on_disk) = read(&path) else {
            self.writable = false;
            return Err(SaveError::Unreadable);
        };
        on_disk.entry(key).or_default().insert(letter, mark);
        write_atomic(&path, &on_disk)?;
        for (file, marks) in on_disk {
            self.files.entry(file).or_default().extend(marks);
        }
        Ok(())
    }
}

fn file_key(file: &Path) -> String {
    fs::canonicalize(file)
        .unwrap_or_else(|_| file.to_path_buf())
        .to_string_lossy()
        .into_owned()
}

/// `None` means the file exists but cannot be read or parsed.
fn read(path: &Path) -> Option<AllMarks> {
    match fs::read_to_string(path) {
        Ok(text) => toml::from_str(&text).ok(),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Some(AllMarks::new()),
        Err(_) => None,
    }
}

fn write_atomic(path: &Path, marks: &AllMarks) -> Result<(), SaveError> {
    if let Some(dir) = path.parent() {
        fs::create_dir_all(dir)?;
    }
    let text = toml::to_string(marks).map_err(io::Error::other)?;
    let tmp = path.with_extension("toml.tmp");
    fs::write(&tmp, text)?;
    fs::rename(&tmp, path)?;
    Ok(())
}
```

The on-disk layout is toml's default serialization of `path -> letter -> { line, text }`. It's the same logical shape as the spec's example, though toml may print it with `["<path>".a]` table headers rather than inline tables. Tests only check round trips.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test marks::`
Expected: all 18 `marks` tests pass.

- [ ] **Step 6: Commit**

```bash
cargo fmt
git add Cargo.toml Cargo.lock src/marks.rs
git commit -m "feat(marks): persist marks per file in the data directory"
```

---

### Task 5: Viewer keys - `m`/`'` prefix, set, jump, `M` for mouse

**Files:**
- Modify: `src/viewer.rs`:
  - `ViewMode` area (~line 229, add `MarkOp`)
  - `ViewerState` struct (283-372) and `ViewerState::new` (406-451)
  - `handle_event` (993-998, pending check after Ctrl+c)
  - `handle_normal` (1606-1663: prefix before the slide-mode return, `m` -> `M`)
  - `help_sections` (3597-3650)
  - `mod tests` (3962+)
- Test: `src/viewer.rs` `mod tests`

**Interfaces:**
- Consumes: `Line::source_line` (Task 1). `crate::marks::{Mark, MarkStore, SaveError, resolve}` (Tasks 3-4).
- Produces: user-visible behavior only. Private functions in `viewer.rs`:
  - `begin_mark(&mut ViewerState, MarkOp)`
  - `marks_unavailable(&ViewerState) -> Option<&'static str>`
  - `set_mark(&mut ViewerState, char)`
  - `jump_to_mark(&mut ViewerState, char)`

- [ ] **Step 1: Write the failing tests** inside `mod tests` in `src/viewer.rs`:

```rust
    // ── Marks ──────────────────────────────────────────────────────────────

    use crossterm::event::KeyEvent;

    fn mark_state_files(docs: &[(&str, &str)], slide_mode: bool) -> (tempfile::TempDir, ViewerState) {
        let dir = tempfile::tempdir().unwrap();
        let mut files = Vec::new();
        for (name, content) in docs {
            let path = dir.path().join(name);
            std::fs::write(&path, content).unwrap();
            files.push(path.to_string_lossy().into_owned());
        }
        let opts = ViewerOptions {
            files: files.clone(),
            initial_content: docs[0].1.to_string(),
            filename: files[0].clone(),
            theme: crate::theme::Theme::dark(),
            slide_mode,
            line_numbers: false,
            width_override: None,
        };
        let mut state = ViewerState::new(opts, 80, 24);
        state.marks = crate::marks::MarkStore::load_from(dir.path().join("marks.toml"));
        state.rebuild();
        (dir, state)
    }

    fn mark_state(content: &str) -> (tempfile::TempDir, ViewerState) {
        mark_state_files(&[("doc.md", content)], false)
    }

    fn paragraphs(n: usize) -> String {
        (1..=n).map(|i| format!("Paragraph {i}\n\n")).collect()
    }

    fn key(state: &mut ViewerState, code: KeyCode, mods: KeyModifiers) -> bool {
        handle_event(state, Event::Key(KeyEvent::new(code, mods)))
    }

    fn press(state: &mut ViewerState, c: char) -> bool {
        key(state, KeyCode::Char(c), KeyModifiers::NONE)
    }

    fn toast(state: &ViewerState) -> Option<&str> {
        state.toast.as_ref().map(|(msg, _)| msg.as_str())
    }

    fn top_text(state: &ViewerState) -> String {
        state.wrapped[state.offset]
            .spans
            .iter()
            .map(|s| s.text.as_str())
            .collect()
    }

    fn scroll_to(state: &mut ViewerState, needle: &str) {
        state.offset = state
            .wrapped
            .iter()
            .position(|l| l.spans.iter().any(|s| s.text.contains(needle)))
            .unwrap();
    }

    #[test]
    fn set_and_jump_back() {
        let (_dir, mut state) = mark_state(&paragraphs(100));
        scroll_to(&mut state, "Paragraph 50");
        let marked = state.offset;
        press(&mut state, 'm');
        press(&mut state, 'a');
        assert_eq!(toast(&state), Some("Mark 'a' set"));
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert_eq!(state.offset, marked);
        assert_eq!(toast(&state), Some("Jumped to 'a'"));
        assert_eq!(state.nav_history.last(), Some(&(0, 0)));
    }

    #[test]
    fn jump_survives_edit_above_mark() {
        let (_dir, mut state) = mark_state(&paragraphs(100));
        scroll_to(&mut state, "Paragraph 50");
        press(&mut state, 'm');
        press(&mut state, 'a');
        state.content = format!("Inserted\n\nMore\n\n{}", paragraphs(100));
        state.rebuild();
        state.offset = 0;
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert!(top_text(&state).contains("Paragraph 50"));
        assert_eq!(toast(&state), Some("Jumped to 'a'"));
    }

    #[test]
    fn jump_reports_moved_when_text_is_gone() {
        let (_dir, mut state) = mark_state(&paragraphs(100));
        scroll_to(&mut state, "Paragraph 50");
        press(&mut state, 'm');
        press(&mut state, 'a');
        state.content = paragraphs(100).replace("Paragraph 50\n", "Rewritten\n");
        state.rebuild();
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert_eq!(toast(&state), Some("Mark 'a' moved - nearest position"));
    }

    #[test]
    fn jump_to_unset_mark() {
        let (_dir, mut state) = mark_state(&paragraphs(10));
        press(&mut state, '\'');
        press(&mut state, 'x');
        assert_eq!(toast(&state), Some("Mark 'x' not set"));
        assert!(state.nav_history.is_empty());
    }

    #[test]
    fn non_letter_cancels_prefix() {
        let (_dir, mut state) = mark_state(&paragraphs(10));
        press(&mut state, 'm');
        press(&mut state, '1');
        assert!(state.pending_mark.is_none());
        press(&mut state, '\'');
        press(&mut state, '1');
        assert!(state.toast.is_none());
    }

    #[test]
    fn esc_and_q_during_prefix_do_not_quit() {
        let (_dir, mut state) = mark_state(&paragraphs(10));
        press(&mut state, 'm');
        assert!(!key(&mut state, KeyCode::Esc, KeyModifiers::NONE));
        press(&mut state, 'm');
        assert!(!press(&mut state, 'q'));
        assert!(state.pending_mark.is_none());
    }

    #[test]
    fn ctrl_c_during_prefix_quits() {
        let (_dir, mut state) = mark_state(&paragraphs(10));
        press(&mut state, 'm');
        assert!(key(&mut state, KeyCode::Char('c'), KeyModifiers::CONTROL));
    }

    #[test]
    fn marks_are_per_file() {
        let docs = [("a.md", "Alpha\n"), ("b.md", "Beta\n")];
        let (_dir, mut state) = mark_state_files(&docs, false);
        press(&mut state, 'm');
        press(&mut state, 'a');
        state.switch_file(1);
        press(&mut state, '\'');
        press(&mut state, 'a');
        assert_eq!(toast(&state), Some("Mark 'a' not set"));
    }

    #[test]
    fn empty_document_has_nothing_to_mark() {
        let (_dir, mut state) = mark_state("");
        press(&mut state, 'm');
        press(&mut state, 'a');
        assert_eq!(toast(&state), Some("Nothing to mark here"));
    }

    #[test]
    fn marks_unavailable_for_stdin() {
        let mut state = make_state_with_lines(vec![]);
        state.filename = "<stdin>".to_string();
        press(&mut state, 'm');
        assert_eq!(toast(&state), Some("Marks unavailable for stdin"));
        assert!(state.pending_mark.is_none());
    }

    #[test]
    fn marks_unavailable_in_json_view() {
        let (_dir, mut state) = mark_state_files(&[("doc.json", "{\"a\": 1}")], false);
        assert!(state.json_view.is_some());
        press(&mut state, '\'');
        assert_eq!(toast(&state), Some("Marks unavailable in JSON view"));
    }

    #[test]
    fn marks_unavailable_in_slide_mode() {
        let (_dir, mut state) = mark_state_files(&[("doc.md", "One\n\n---\n\nTwo\n")], true);
        press(&mut state, 'm');
        assert_eq!(toast(&state), Some("Marks unavailable in slide mode"));
    }

    #[test]
    fn help_lists_mark_and_mouse_keys() {
        let keys: Vec<&str> = help_sections()
            .iter()
            .flat_map(|s| s.entries.iter().map(|(k, _)| *k))
            .collect();
        assert!(keys.contains(&"m a-z"));
        assert!(keys.contains(&"' a-z"));
        assert!(keys.contains(&"M"));
        assert!(!keys.contains(&"m"));
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test viewer::tests`
Expected: compile errors, `no field marks` / `no field pending_mark`.

- [ ] **Step 3: Add state.** Below `ViewMode` (~line 245), add:

```rust
/// A mark prefix (`m` or `'`) waiting for its letter.
#[derive(PartialEq, Copy, Clone, Debug)]
enum MarkOp {
    Set,
    Jump,
}
```

Add these to `ViewerState` after `nav_history`:

```rust
    // Bookmarks: pending `m`/`'` prefix and the persistent store
    pending_mark: Option<MarkOp>,
    marks: crate::marks::MarkStore,
```

And to `ViewerState::new`: `pending_mark: None, marks: crate::marks::MarkStore::load(),`.

- [ ] **Step 4: Handle the pending prefix in `handle_event`**, directly after the `Ctrl+c` check (line 996-998) and before `is_help_toggle`:

```rust
            if let Some(op) = state.pending_mark.take() {
                if let KeyCode::Char(letter) = ke.code
                    && letter.is_ascii_lowercase()
                    && !ke
                        .modifiers
                        .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
                {
                    match op {
                        MarkOp::Set => set_mark(state, letter),
                        MarkOp::Jump => jump_to_mark(state, letter),
                    }
                }
                state.dirty = true;
                return false;
            }
```

- [ ] **Step 5: Start the prefix in `handle_normal`**, before `if state.slide_mode {` (line 1610), so slide mode can show its toast:

```rust
    let mark_op = match code {
        KeyCode::Char('m') => Some(MarkOp::Set),
        KeyCode::Char('\'') => Some(MarkOp::Jump),
        _ => None,
    };
    if let Some(op) = mark_op {
        begin_mark(state, op);
        return false;
    }
```

Change the mouse capture arm from `KeyCode::Char('m') => {` to `KeyCode::Char('M') => {`. Leave the body unchanged.

- [ ] **Step 6: Add the handlers** after `handle_normal`:

```rust
fn marks_unavailable(state: &ViewerState) -> Option<&'static str> {
    if state.files.is_empty() {
        Some("Marks unavailable for stdin")
    } else if state.json_view.is_some() {
        Some("Marks unavailable in JSON view")
    } else if state.slide_mode {
        Some("Marks unavailable in slide mode")
    } else {
        None
    }
}

fn begin_mark(state: &mut ViewerState, op: MarkOp) {
    match marks_unavailable(state) {
        Some(reason) => state.set_toast(reason),
        None => state.pending_mark = Some(op),
    }
}

fn current_file_path(state: &ViewerState) -> PathBuf {
    PathBuf::from(&state.files[state.current_file_idx])
}

fn set_mark(state: &mut ViewerState, letter: char) {
    let Some(line) = state
        .wrapped
        .iter()
        .skip(state.offset)
        .find_map(|l| l.source_line)
    else {
        state.set_toast("Nothing to mark here");
        return;
    };
    let text = state
        .content
        .lines()
        .nth(line - 1)
        .unwrap_or("")
        .trim()
        .to_string();
    let path = current_file_path(state);
    let msg = match state.marks.set(&path, letter, Mark { line, text }) {
        Ok(()) => format!("Mark '{letter}' set"),
        Err(SaveError::Unreadable) => "marks.toml unreadable - marks not saved".to_string(),
        Err(e) => format!("Could not save mark: {e}"),
    };
    state.set_toast(msg);
}

fn jump_to_mark(state: &mut ViewerState, letter: char) {
    let path = current_file_path(state);
    let Some(mark) = state.marks.get(&path, letter).cloned() else {
        state.set_toast(format!("Mark '{letter}' not set"));
        return;
    };
    let target = resolve(&mark, &state.content);
    let max = state.max_offset();
    let idx = state
        .wrapped
        .iter()
        .position(|l| l.source_line.is_some_and(|s| s >= target.line))
        .unwrap_or(max);
    state.nav_history.push((state.current_file_idx, state.offset));
    state.offset = idx.min(max);
    state.set_toast(if target.exact {
        format!("Jumped to '{letter}'")
    } else {
        format!("Mark '{letter}' moved - nearest position")
    });
}
```

Add `use crate::marks::{Mark, SaveError, resolve};` to the `viewer.rs` imports, and add `use std::path::PathBuf;` if it isn't imported yet.

- [ ] **Step 7: Update the help table** in `help_sections`. Add these to the end of `Navigation`, after `Backspace`:

```rust
                ("m a-z", "Set mark at top of screen"),
                ("' a-z", "Jump to mark"),
```

In `Actions`, replace `("m", "Toggle mouse capture (for text select)")` with `("M", "Toggle mouse capture (for text select)")`.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `cargo test`
Expected: all pass, including the 13 new viewer tests. `help_sections_no_duplicate_keys` still passes. Also check that `help_box_dimensions` fits the new rows: run `cargo run -- test.md` in an 80x24 terminal, press `?`, and scroll the help to the end.

- [ ] **Step 9: Lint and commit**

```bash
cargo fmt && cargo clippy
git add src/viewer.rs
git commit -m "feat(viewer): add m/' bookmarks and move mouse toggle to M"
```

---

### Task 6: Docs and end-to-end verification

**Files:**
- Modify: `README.md` (Navigation and Features key tables, ~lines 70-100)
- Modify: `CLAUDE.md` (Architecture list)

**Interfaces:**
- Consumes: the finished feature (Tasks 1-5).

- [ ] **Step 1: README.** Add these rows to the Navigation table after `Backspace`:

```markdown
| `m` + `a-z` | Set a mark at the top of the screen (saved per file) |
| `'` + `a-z` | Jump to a mark (`Backspace` returns) |
```

Add this row to the Features table:

```markdown
| `M` | Toggle mouse capture (for selecting text) |
```

- [ ] **Step 2: CLAUDE.md.** Change "Ten source files" to "Eleven source files", and add this after the `config.rs` entry:

```markdown
- **marks.rs** - Bookmarks. `resolve` maps a saved mark (1-based source line + trimmed text) onto the current source; `MarkStore` persists marks per canonical file path in `dirs::data_dir()/mdterm/marks.toml` with re-read + atomic write on every set. Never overwrites an unparseable file.
```

Also update the `style.rs` entry to mention that `Line.source_line` links rendered lines back to the source.

- [ ] **Step 3: End-to-end run in tmux, with a throwaway home directory**

```bash
cargo build --release
E2E=$(mktemp -d); cp test.md "$E2E/doc.md"
tmux new-session -d -s marks -x 100 -y 30 \
  "env -u XDG_DATA_HOME HOME=$E2E ./target/release/mdterm $E2E/doc.md"
sleep 1
tmux send-keys -t marks ']' ']' ']'
sleep 0.3; tmux capture-pane -p -t marks | sed -n 2,3p > "$E2E/before.txt"
tmux send-keys -t marks m a
sleep 0.3; tmux capture-pane -p -t marks | grep "Mark 'a' set"
tmux send-keys -t marks q
find "$E2E" -name marks.toml -exec cat {} \;
```

Expected: the toast line is printed. `marks.toml` exists under `$E2E/Library/Application Support/mdterm/` (macOS) or `$E2E/.local/share/mdterm/` (Linux) and contains `doc.md`.

- [ ] **Step 4: Edit the file, resize, reopen and jump**

```bash
printf 'Inserted 1\n\nInserted 2\n\nInserted 3\n\n' | cat - "$E2E/doc.md" > "$E2E/tmp" && mv "$E2E/tmp" "$E2E/doc.md"
tmux new-session -d -s marks2 -x 70 -y 30 \
  "env -u XDG_DATA_HOME HOME=$E2E ./target/release/mdterm $E2E/doc.md"
sleep 1
tmux send-keys -t marks2 "'" a
sleep 0.3; tmux capture-pane -p -t marks2 | sed -n 2,3p
tmux capture-pane -p -t marks2 | grep "Jumped to 'a'"
tmux send-keys -t marks2 BSpace
sleep 0.3; tmux capture-pane -p -t marks2 | sed -n 2,3p
tmux send-keys -t marks2 M
sleep 0.3; tmux capture-pane -p -t marks2 | grep "Mouse capture OFF"
tmux kill-session -t marks2
```

Expected:
- After `'a`, the top lines show the same heading as `before.txt`. Line wrapping may differ at 70 columns.
- The `Jumped to 'a'` toast appears.
- `Backspace` returns to the top of the document.
- `M` shows the mouse-capture toast.

If anything differs, stop and debug with superpowers:systematic-debugging before going further.

- [ ] **Step 5: Final checks and commit**

```bash
cargo fmt --check && cargo clippy -- -D warnings && cargo test
git add README.md CLAUDE.md
git commit -m "docs: document bookmarks and the M mouse toggle"
```

---

## Self-Review Notes

- **Spec coverage:**

  | Spec item | Task |
  |---|---|
  | Keybindings | 5 |
  | `M` rebind | 5 |
  | `source_line` | 1 |
  | Stamping, code/table precision | 2 |
  | `resolve` rules 1-4 | 3 |
  | Store, canonical keys, atomic re-read write, corrupt never overwritten | 4 |
  | Availability toasts, set/jump, `nav_history`, all toast strings | 5 |
  | Docs, E2E success criterion | 6 |
  | Auto-reload | Needs no code: `jump_to_mark` resolves against current `state.content` |

- **Additions beyond the spec:**
  - `Nothing to mark here` toast (Review Focus 5).
  - In-memory merge of other instances' marks after a successful save.
- **Type consistency:** `Mark`, `Resolved`, `resolve`, `MarkStore::{load, load_from, get, set}`, `SaveError::{NoDataDir, Unreadable, Io}`, `MarkOp::{Set, Jump}`, `pending_mark` and `marks` are used under the same names in Tasks 3, 4 and 5.
