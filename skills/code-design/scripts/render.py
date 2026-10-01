#!/usr/bin/env python3
"""Render a code-design Markdown file into a lavish review page.

Usage: render.py <design.md> [-o <page.html>]

The Markdown stays the single source: the page embeds it and renders it in
the browser with marked, highlight.js and Mermaid. Fenced `decision` blocks
become native choice forms that queue one lavish prompt on submit:

    ```decision
    id: approach
    question: Which approach should the design use?
    - A: Check first, in the command (recommended)
    - B: Send first, explain on failure
    ```

`[new]`, `[modified]`, `[existing]`, `[removed]`, `[recommended]` and
`[rejected]` in headings, lists and tables render as badges.
"""

import argparse
import html
import json
import re
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en" data-theme="nord">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/daisyui.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/themes.css">
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.2.4/dist/index.global.js"></script>
<link rel="stylesheet" media="(prefers-color-scheme: light)" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<link rel="stylesheet" media="(prefers-color-scheme: dark)" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.documentElement.dataset.theme = "dim";
  }
</script>
<style>
  *, *::before, *::after { box-sizing: border-box; }
  :where(.grid, .flex) > * { min-width: 0; }
  html, body { background: var(--color-base-200); color: var(--color-base-content); min-height: 100%; }
  .doc { line-height: 1.65; }
  .doc :where(p, li, h1, h2, h3, h4) { overflow-wrap: anywhere; }
  .doc :where(td, th) { overflow-wrap: break-word; }
  .doc h1 { font-size: 2rem; font-weight: 700; line-height: 1.2; }
  .doc h2 { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.75rem; }
  .doc h3 { font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.5rem; }
  .doc h4 { font-weight: 600; margin: 1rem 0 0.25rem; }
  .doc p, .doc ul, .doc ol, .doc table, .doc pre, .doc blockquote { margin: 0.6rem 0; }
  .doc ul { list-style: disc; padding-left: 1.4rem; }
  .doc ol { list-style: decimal; padding-left: 1.4rem; }
  .doc li { margin: 0.2rem 0; }
  .doc a { color: var(--color-primary); text-decoration: underline; }
  .doc blockquote { border-left: 4px solid var(--color-primary); padding-left: 0.9rem; opacity: 0.85; }
  .doc :not(pre) > code { font-size: 0.85em; background: var(--color-base-200); padding: 0.1em 0.35em; border-radius: 4px; }
  .doc pre { border-radius: 8px; overflow-x: auto; font-size: 0.82rem; line-height: 1.5; }
  .doc pre code.hljs { padding: 0.9rem 1rem; border-radius: 8px; }
  .doc table { width: 100%; border-collapse: collapse; font-size: 0.9rem; display: block; overflow-x: auto; }
  .doc th, .doc td { border: 1px solid var(--color-base-300); padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }
  .doc th { background: var(--color-base-200); }
  .doc .diagram { background: var(--color-base-100); border: 1px solid var(--color-base-300); border-radius: 8px; padding: 1rem; overflow-x: auto; text-align: center; }
  .doc .diagram svg { max-width: 100%; height: auto; }
  .doc .diagram .cluster rect { fill: var(--color-base-200) !important; stroke: var(--color-base-300) !important; }
  .doc h3 + pre, .doc h3 + p + pre { margin-top: 0.5rem; }
  .toc a { display: block; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.875rem; }
  .toc a:hover { background: var(--color-base-300); }
</style>
</head>
<body>
<div class="max-w-7xl mx-auto px-4 py-8 lg:grid lg:grid-cols-[14rem_minmax(0,1fr)] lg:gap-8">
  <aside class="hidden lg:block">
    <nav class="toc sticky top-6 card bg-base-100 p-3" id="toc" aria-label="Contents"></nav>
  </aside>
  <main class="doc space-y-6 min-w-0" id="doc"></main>
</div>
<script type="application/json" id="source">__SOURCE__</script>
<script>
  const BADGES = { new: "badge-primary", modified: "badge-warning", existing: "badge-ghost", removed: "badge-error",
    recommended: "badge-success", rejected: "badge-neutral" };
  const BADGE_TAG = /\[(new|modified|existing|removed|recommended|rejected)\]/gi;
  const source = JSON.parse(document.getElementById("source").textContent);

  function escape(text) {
    return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function parseDecision(text) {
    const spec = { id: "decision", question: "Decision", options: [] };
    for (const line of text.split("\n")) {
      const option = line.match(/^\s*-\s*([^:]+):\s*(.+)$/);
      const field = line.match(/^\s*(id|question):\s*(.+)$/);
      if (option) {
        const recommended = /\(recommended\)\s*$/i.test(option[2]);
        spec.options.push({ key: option[1].trim(), label: option[2].replace(/\s*\(recommended\)\s*$/i, ""), recommended });
      } else if (field) {
        spec[field[1]] = field[2].trim();
      }
    }
    return spec;
  }

  function decisionForm(spec) {
    const options = spec.options.map((o) => `
      <label class="flex gap-3 items-start p-2 rounded-lg hover:bg-base-200 cursor-pointer">
        <input type="radio" class="radio radio-primary radio-sm mt-1" name="choice" value="${escape(o.key)}" data-label="${escape(o.label)}" ${o.recommended ? "checked" : ""}>
        <span><b>${escape(o.key)}</b> - ${escape(o.label)} ${o.recommended ? '<span class="badge badge-primary badge-sm ml-1">recommended</span>' : ""}</span>
      </label>`).join("");
    return `
      <form class="decision border border-primary/40 rounded-xl p-4 my-4 space-y-2 bg-base-100" data-lavish-question="${escape(spec.id)}" data-question="${escape(spec.question)}">
        <p class="font-semibold">${escape(spec.question)}</p>
        ${options}
        <textarea name="notes" class="textarea textarea-bordered w-full" rows="2" placeholder="Notes or changes (optional)"></textarea>
        <button type="submit" class="btn btn-primary btn-sm">Queue answer</button>
        <span class="text-sm opacity-70 ml-2" role="status"></span>
      </form>`;
  }

  window.diagrams = [];
  const renderer = new marked.Renderer();
  renderer.code = (code, lang) => {
    const language = (lang || "").trim().split(/\s+/)[0];
    if (language === "mermaid") {
      window.diagrams.push(code);
      return `<div class="diagram" data-diagram="${window.diagrams.length - 1}"></div>`;
    }
    if (language === "decision") return decisionForm(parseDecision(code));
    const cls = language ? ` class="language-${escape(language)}"` : "";
    return `<pre><code${cls}>${escape(code)}</code></pre>`;
  };

  const doc = document.getElementById("doc");
  const scratch = document.createElement("div");
  scratch.innerHTML = marked.parse(source, { renderer, gfm: true, breaks: true });

  const header = document.createElement("header");
  header.className = "space-y-3 pb-2";
  let section = null;
  const sections = [];
  for (const node of [...scratch.childNodes]) {
    if (node.nodeName === "H2") {
      section = document.createElement("section");
      section.className = "card bg-base-100 shadow-sm";
      const body = document.createElement("div");
      body.className = "card-body";
      section.appendChild(body);
      sections.push(section);
    }
    (section ? section.firstChild : header).appendChild(node);
  }
  doc.appendChild(header);
  sections.forEach((s) => doc.appendChild(s));
  const h1 = header.querySelector("h1");
  if (h1) document.title = h1.textContent;

  for (const el of doc.querySelectorAll("h1, h2, h3, h4, li, td, p")) {
    for (const text of [...el.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE)) {
      if (!text.textContent.match(BADGE_TAG)) continue;
      const span = document.createElement("span");
      span.innerHTML = escape(text.textContent).replace(BADGE_TAG,
        (_, kind) => `<span class="badge badge-sm ${BADGES[kind.toLowerCase()]} align-middle">${kind.toLowerCase()}</span>`);
      text.replaceWith(...span.childNodes);
    }
  }

  const toc = document.getElementById("toc");
  doc.querySelectorAll("h2").forEach((h, i) => {
    h.id = h.id || `s${i + 1}`;
    const link = document.createElement("a");
    link.href = `#${h.id}`;
    const label = h.cloneNode(true);
    label.querySelectorAll(".badge").forEach((badge) => badge.remove());
    link.textContent = label.textContent.trim();
    toc.appendChild(link);
  });
  if (!toc.children.length) toc.closest("aside").remove();

  doc.querySelectorAll("pre code").forEach((block) => hljs.highlightElement(block));

  doc.querySelectorAll("form.decision").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const picked = form.querySelector("input[name=choice]:checked");
      if (!picked) return;
      const notes = form.querySelector("textarea").value.trim();
      const question = form.dataset.question;
      const text = `${question} -> ${picked.value} (${picked.dataset.label})` + (notes ? `. Notes: ${notes}` : "");
      if (window.lavish) {
        window.lavish.queuePrompt(text, { tag: "choice", text, element: form,
          data: { question: form.dataset.lavishQuestion, answer: picked.value, notes } });
        form.querySelector("[role=status]").textContent = "Queued.";
      } else {
        navigator.clipboard?.writeText(text);
        form.querySelector("[role=status]").textContent = "Copied - paste it into the chat.";
      }
    });
  });
</script>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.15.0/dist/mermaid.esm.min.mjs";
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const UNIT_CLASSES = dark
    ? "classDef new fill:#1e3a5f,stroke:#60a5fa,color:#e5e7eb\nclassDef modified fill:#4a3b10,stroke:#fbbf24,color:#e5e7eb\nclassDef existing fill:#2a2f3a,stroke:#6b7280,color:#9ca3af"
    : "classDef new fill:#dbeafe,stroke:#2563eb,color:#1e3a8a\nclassDef modified fill:#fef3c7,stroke:#d97706,color:#78350f\nclassDef existing fill:#f3f4f6,stroke:#9ca3af,color:#4b5563";
  mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict" });
  for (const el of document.querySelectorAll("[data-diagram]")) {
    let code = window.diagrams[Number(el.dataset.diagram)];
    if (/^\s*(flowchart|graph)\b/.test(code)) code += "\n" + UNIT_CLASSES;
    try {
      const { svg } = await mermaid.render(`diagram-${el.dataset.diagram}`, code);
      el.innerHTML = svg;
    } catch (error) {
      el.classList.add("text-left");
      el.innerHTML = `<p class="text-error text-sm">Diagram failed to render: ${String(error.message || error).split("\n")[0]}</p><pre></pre>`;
      el.querySelector("pre").textContent = code;
    }
  }
</script>
</body>
</html>
"""


def title_of(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return re.sub(r"[`*_]", "", match.group(1)).strip() if match else fallback


def render(markdown: str, fallback_title: str) -> str:
    source = json.dumps(markdown).replace("</", "<\\/")
    return (TEMPLATE
            .replace("__TITLE__", html.escape(title_of(markdown, fallback_title)))
            .replace("__SOURCE__", source))


def main():
    parser = argparse.ArgumentParser(description="Render a code-design Markdown file into a lavish review page.")
    parser.add_argument("markdown", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.markdown.with_suffix(".html")
    output.write_text(render(args.markdown.read_text(), args.markdown.stem))
    print(output)


if __name__ == "__main__":
    main()
