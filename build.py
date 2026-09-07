#!/usr/bin/env python3
"""
build.py — builds the two deliverables from guide/*.md:

  1. SELF-HOSTING-GUIDE.md   single-file Markdown (all chapters concatenated, links rewritten to anchors)
  2. docs/                   static website (one HTML page per chapter + index + search index)

Zero network dependencies. Requires: pip install markdown pymdown-extensions
(pymdown-extensions is optional; features degrade gracefully without it).

Usage:  python3 build.py
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency: pip install markdown pymdown-extensions")

ROOT = Path(__file__).resolve().parent
GUIDE_DIR = ROOT / "guide"
SITE_DIR = ROOT / "site"
DOCS_DIR = ROOT / "docs"
SINGLE_MD = ROOT / "SELF-HOSTING-GUIDE.md"

TITLE = "The Self-Hosting & Home Lab Guide"
TAGLINE = "A comprehensive, opinionated, in-depth guide to services worth self-hosting — and everything around them."
REPO_URL = "https://github.com/gorg667/self-host-guide"

# Part grouping for the sidebar. Keys are the numeric prefixes of chapter files.
PARTS = [
    ("Part I — Foundations", range(0, 7)),
    ("Part II — Core infrastructure", range(7, 14)),
    ("Part III — Application services", range(14, 27)),
    ("Part IV — Operations & reference", range(27, 40)),
]

CHAPTER_RE = re.compile(r"^(\d\d)-([a-z0-9-]+)\.md$")
MD_LINK_RE = re.compile(r"\]\((\d\d-[a-z0-9-]+\.md)(#[^)\s]*)?\)")


class Chapter:
    def __init__(self, path: Path):
        self.path = path
        m = CHAPTER_RE.match(path.name)
        if not m:
            raise ValueError(f"Bad chapter filename: {path.name}")
        self.num = int(m.group(1))
        self.slug = f"{m.group(1)}-{m.group(2)}"
        self.raw = path.read_text(encoding="utf-8")
        first = next((l for l in self.raw.splitlines() if l.startswith("# ")), None)
        self.title = first[2:].strip() if first else self.slug
        self.body_md = self.raw  # includes H1
        self.words = len(re.findall(r"\w+", self.raw))

    @property
    def anchor(self) -> str:
        return slugify(self.title)


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def load_chapters() -> list[Chapter]:
    files = sorted(p for p in GUIDE_DIR.glob("*.md") if CHAPTER_RE.match(p.name))
    return [Chapter(p) for p in files]


# --------------------------------------------------------------------------------------
# Single-file Markdown
# --------------------------------------------------------------------------------------
def build_single_md(chapters: list[Chapter]) -> None:
    by_slug = {c.slug: c for c in chapters}
    total_words = sum(c.words for c in chapters)

    out: list[str] = []
    out.append(f"# {TITLE}\n")
    out.append(f"> {TAGLINE}\n")
    out.append(
        f"*Generated {date.today().isoformat()} from the chapter sources in `guide/`. "
        f"{len(chapters)} chapters, ~{total_words:,} words. Web version: see `docs/` or the repository README. "
        f"Source: {REPO_URL}*\n"
    )
    out.append("\n## Table of contents\n")
    for part_title, rng in PARTS:
        part_chapters = [c for c in chapters if c.num in rng]
        if not part_chapters:
            continue
        out.append(f"\n**{part_title}**\n")
        for c in part_chapters:
            out.append(f"- [{c.num:02d}. {c.title}](#{c.anchor})")
    out.append("\n---\n")

    for c in chapters:
        body = c.body_md

        def repl(m: re.Match) -> str:
            target = m.group(1)
            frag = m.group(2) or ""
            tgt = by_slug.get(target[:-3])
            if tgt is None:
                return m.group(0)
            if frag:
                return f"]({frag})"  # heading anchors are global in a single doc
            return f"](#{tgt.anchor})"

        body = MD_LINK_RE.sub(repl, body)
        # Convert admonitions into blockquotes so the plain MD still reads well on GitHub.
        body = convert_admonitions_for_md(body)
        out.append(body.rstrip() + "\n\n---\n")

    SINGLE_MD.write_text("\n".join(out), encoding="utf-8")
    print(f"  wrote {SINGLE_MD.name} ({SINGLE_MD.stat().st_size/1024:.0f} KB, ~{total_words:,} words)")


ADMON_RE = re.compile(r'^!!! (\w+)(?: "([^"]*)")?\s*$')


def convert_admonitions_for_md(text: str) -> str:
    """Turn python-markdown `!!! type "Title"` blocks (4-space indented body) into GFM blockquotes."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    label = {"tip": "Tip", "note": "Note", "warning": "Warning", "danger": "Danger", "info": "Info", "example": "Example", "question": "Question", "success": "Success", "failure": "Failure", "bug": "Bug", "quote": "Quote", "abstract": "Summary"}
    while i < len(lines):
        m = ADMON_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        kind, title = m.group(1), m.group(2)
        title = title if title is not None else label.get(kind, kind.title())
        i += 1
        body: list[str] = []
        while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
            # stop at blank line followed by non-indented content
            if lines[i].strip() == "":
                if i + 1 < len(lines) and lines[i + 1].strip() != "" and not lines[i + 1].startswith("    "):
                    break
                body.append("")
            else:
                body.append(lines[i][4:])
            i += 1
        while body and body[-1] == "":
            body.pop()
        head = f"> **{title}**" if title else f"> **{label.get(kind, kind.title())}**"
        out.append(head)
        out.append(">")
        for b in body:
            out.append(f"> {b}" if b else ">")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Static site
# --------------------------------------------------------------------------------------
def md_renderer():
    exts = [
        "extra",           # tables, fenced_code, footnotes, attr_list, def_list, abbr, md_in_html
        "admonition",
        "toc",
        "sane_lists",
        "codehilite",
    ]
    cfg = {
        "toc": {"permalink": "#", "toc_depth": "2-4", "slugify": lambda v, s: slugify(v)},
        "codehilite": {"guess_lang": False, "css_class": "highlight", "noclasses": False},
    }
    try:
        import pymdownx  # noqa: F401
        exts += ["pymdownx.superfences", "pymdownx.tasklist", "pymdownx.tilde", "pymdownx.keys"]
        cfg["pymdownx.superfences"] = {
            "custom_fences": [
                {"name": "mermaid", "class": "mermaid", "format": lambda src, lang, css_class, options, md, **kw: f'<pre class="mermaid">{html.escape(src)}</pre>'}
            ]
        }
        exts.remove("extra")
        exts += ["tables", "footnotes", "attr_list", "def_list", "abbr", "md_in_html"]
    except ImportError:
        pass
    return markdown.Markdown(extensions=exts, extension_configs=cfg)


def read_site_asset(name: str) -> str:
    return (SITE_DIR / name).read_text(encoding="utf-8")


def render_sidebar(chapters: list[Chapter], current: Chapter | None, depth_prefix: str) -> str:
    parts_html: list[str] = []
    for part_title, rng in PARTS:
        part_chapters = [c for c in chapters if c.num in rng]
        if not part_chapters:
            continue
        items = []
        for c in part_chapters:
            cls = ' class="active"' if current is c else ""
            items.append(f'<li{cls}><a href="{depth_prefix}{c.slug}/"><span class="num">{c.num:02d}</span> {html.escape(c.title)}</a></li>')
        parts_html.append(f'<div class="part"><div class="part-title">{html.escape(part_title)}</div><ul>{"".join(items)}</ul></div>')
    return "".join(parts_html)


def rewrite_site_links(body_html: str) -> str:
    # chapter links NN-slug.md -> ../NN-slug/
    def repl(m: re.Match) -> str:
        return f'href="../{m.group(1)}/{m.group(2) or ""}"'
    body_html = re.sub(r'href="(\d\d-[a-z0-9-]+)\.md(#[^"]*)?"', repl, body_html)
    # external links open in new tab
    body_html = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body_html)
    return body_html


def page(template: str, **kw: str) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def build_site(chapters: list[Chapter]) -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()
    (DOCS_DIR / ".nojekyll").write_text("")
    shutil.copy(SITE_DIR / "style.css", DOCS_DIR / "style.css")
    shutil.copy(SITE_DIR / "app.js", DOCS_DIR / "app.js")
    # pygments css
    try:
        from pygments.formatters import HtmlFormatter
        css = HtmlFormatter(style="default").get_style_defs(".highlight")
        css_dark = HtmlFormatter(style="monokai").get_style_defs("html[data-theme='dark'] .highlight")
        (DOCS_DIR / "pygments.css").write_text(css + "\n" + css_dark)
    except Exception:
        (DOCS_DIR / "pygments.css").write_text("")

    template = read_site_asset("template.html")
    search_index: list[dict] = []
    total_words = sum(c.words for c in chapters)

    for idx, c in enumerate(chapters):
        md = md_renderer()
        body_html = md.convert(c.body_md)
        body_html = rewrite_site_links(body_html)
        toc_html = getattr(md, "toc", "")
        prev_c = chapters[idx - 1] if idx > 0 else None
        next_c = chapters[idx + 1] if idx + 1 < len(chapters) else None
        prev_html = f'<a class="prev" href="../{prev_c.slug}/">← {prev_c.num:02d}. {html.escape(prev_c.title)}</a>' if prev_c else "<span></span>"
        next_html = f'<a class="next" href="../{next_c.slug}/">{next_c.num:02d}. {html.escape(next_c.title)} →</a>' if next_c else "<span></span>"

        out_dir = DOCS_DIR / c.slug
        out_dir.mkdir()
        (out_dir / "index.html").write_text(
            page(
                template,
                TITLE=html.escape(c.title) + " — " + TITLE,
                SITE_TITLE=TITLE,
                ROOT="../",
                SIDEBAR=render_sidebar(chapters, c, "../"),
                TOC=toc_html,
                CONTENT=body_html,
                PREVNEXT=f'<nav class="prevnext">{prev_html}{next_html}</nav>',
                META=f"Chapter {c.num:02d} · ~{c.words:,} words · {max(1, c.words // 220)} min read",
                EDIT_URL=f"{REPO_URL}/blob/main/guide/{c.path.name}",
                REPO_URL=REPO_URL,
                BUILD_DATE=date.today().isoformat(),
            ),
            encoding="utf-8",
        )

        # search index: split by H2/H3 sections
        for sec in split_sections(c.body_md):
            search_index.append({
                "c": c.title,
                "u": f"{c.slug}/" + (f"#{slugify(sec['h'])}" if sec["h"] != c.title else ""),
                "h": sec["h"],
                "t": sec["text"][:600],
            })

    (DOCS_DIR / "search-index.json").write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")

    # index page
    intro_md = read_site_asset("index.md")
    intro_md = intro_md.replace("{{CHAPTER_COUNT}}", str(len(chapters))).replace("{{WORD_COUNT}}", f"{total_words:,}")
    cards = []
    for part_title, rng in PARTS:
        pcs = [c for c in chapters if c.num in rng]
        if not pcs:
            continue
        cards.append(f'<h2 class="part-heading">{html.escape(part_title)}</h2><div class="cards">')
        for c in pcs:
            summary = first_paragraph(c.body_md)
            cards.append(
                f'<a class="card" href="{c.slug}/"><div class="card-num">{c.num:02d}</div>'
                f'<div class="card-title">{html.escape(c.title)}</div>'
                f'<div class="card-summary">{html.escape(summary)}</div>'
                f'<div class="card-meta">~{c.words:,} words</div></a>'
            )
        cards.append("</div>")
    md = md_renderer()
    index_html = md.convert(intro_md) + "".join(cards)
    index_html = rewrite_site_links(index_html).replace('href="../', 'href="')
    (DOCS_DIR / "index.html").write_text(
        page(
            template,
            TITLE=TITLE,
            SITE_TITLE=TITLE,
            ROOT="",
            SIDEBAR=render_sidebar(chapters, None, ""),
            TOC="",
            CONTENT=index_html,
            PREVNEXT="",
            META=f"{len(chapters)} chapters · ~{total_words:,} words",
            EDIT_URL=f"{REPO_URL}/blob/main/site/index.md",
            REPO_URL=REPO_URL,
            BUILD_DATE=date.today().isoformat(),
        ),
        encoding="utf-8",
    )
    # sitemap + 404
    (DOCS_DIR / "404.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Not found</title><script>location.href=location.pathname.split("/").slice(0,2).join("/")+"/";</script>Not found.'
    )
    print(f"  wrote docs/ ({len(chapters)+1} pages, {len(search_index)} search sections)")


def first_paragraph(md_text: str) -> str:
    lines = md_text.splitlines()
    buf: list[str] = []
    started = False
    for l in lines:
        if l.startswith("#"):
            if started:
                break
            continue
        if l.strip() == "":
            if started:
                break
            continue
        if l.startswith(("!!!", "|", "```", "-", "*", ">", "<")):
            if started:
                break
            continue
        started = True
        buf.append(l.strip())
    text = " ".join(buf)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return text[:220] + ("…" if len(text) > 220 else "")


def split_sections(md_text: str) -> list[dict]:
    sections: list[dict] = []
    cur_h = None
    cur: list[str] = []
    in_code = False
    for l in md_text.splitlines():
        if l.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", l)
        if m:
            if cur_h is not None:
                sections.append({"h": cur_h, "text": clean_text(" ".join(cur))})
            cur_h = m.group(2).strip()
            cur = []
        else:
            cur.append(l)
    if cur_h is not None:
        sections.append({"h": cur_h, "text": clean_text(" ".join(cur))})
    return sections


def clean_text(t: str) -> str:
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[|#*_`>!]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def check_links(chapters: list[Chapter]) -> None:
    slugs = {c.slug for c in chapters}
    for c in chapters:
        for m in MD_LINK_RE.finditer(c.raw):
            tgt = m.group(1)[:-3]
            if tgt not in slugs:
                print(f"  WARN broken chapter link in {c.path.name}: {m.group(1)}")


def main() -> None:
    chapters = load_chapters()
    if not chapters:
        sys.exit("No chapters found in guide/")
    print(f"Building from {len(chapters)} chapters:")
    for c in chapters:
        print(f"  {c.slug:40s} {c.words:>7,} words")
    check_links(chapters)
    build_single_md(chapters)
    build_site(chapters)
    print("Done.")


if __name__ == "__main__":
    main()
