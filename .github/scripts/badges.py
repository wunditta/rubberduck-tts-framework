#!/usr/bin/env python3
"""Expand the documentation shorthands of the wiki pages into badges before the pages are deployed.

Run from the repository root (the workflow does): python3 .github/scripts/badges.py wiki
Configuration: .github/badges.json (types and colours, module colour, style).

What is converted (outside fenced code blocks and code spans):
  [str] [num{}] [str/tab] ...        a type token: every alternative (split by "/") must be a known type from badges.json,
                                     "{}" suffixes mean "table of"; unknown tokens are left as they are
  [**name**](name.md) / (./name)     a module link whose page wiki/name.md exists: badge that links to the page
  [text](https://...)                an external link becomes an HTML <a> (optional, externalLinksToHtml): the configure-wiki
                                     action crashes on absolute URLs in Markdown links, HTML passes through untouched
"""
import json, re, sys, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / ".github" / "badges.json").read_text(encoding="utf-8"))
TYPES = CFG["types"]
STYLE = CFG.get("style", "flat-square")
MODCOLOR = CFG.get("modulecolor", "d4a017")
EXT2HTML = CFG.get("externalLinksToHtml", True)
IN_CODE = CFG.get("badgesInCodeSpans", True)     # code spans with type tokens become <code> with badges (fenced blocks never)
TYPE_LABEL = CFG.get("typeLabel", "")            # "" = label-less badge (just the type name), like the TTS API docs

def esc(s):
    return s.replace("-", "--").replace("_", "__").replace(" ", "_")

def shield(label, text, color):
    label = urllib.parse.quote(esc(label), safe="")      # "" gives a label-less badge: badge/-text-color
    text = urllib.parse.quote(esc(text), safe="/")
    return f"https://img.shields.io/badge/{label}-{text}-{color}?style={STYLE}"

def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def convert_code_span(span):
    """`setTable(tgt [any{}], ...)` -> <code>setTable(tgt <img ...>, ...)</code> when it holds a known type token; else unchanged"""
    inner = span[1:-1]
    if not TYPE_TOKEN.search(inner):
        return span
    pieces, pos, found = [], 0, False
    for m in TYPE_TOKEN.finditer(inner):
        html = type_badges(m.group(1))
        if html is None:
            continue
        found = True
        pieces.append(html_escape(inner[pos:m.start()]))
        pieces.append(html)
        pos = m.end()
    if not found:
        return span
    pieces.append(html_escape(inner[pos:]))
    return "<code>" + "".join(pieces) + "</code>"

def type_badges(inner):
    """[str/num{}] -> HTML of one badge per alternative, or None if any base is unknown."""
    out = []
    for part in inner.split("/"):
        base, suf = part, ""
        while base.endswith("{}"):
            base, suf = base[:-2], suf + "{}"
        if base not in TYPES:
            return None
        text = base + suf
        out.append(f'<img alt="{text}" src="{shield(TYPE_LABEL, text, TYPES[base])}">')
    return "".join(out)

def module_badge(name):
    return f'<a href="./{name}"><img alt="{name}" src="{shield("module", name, MODCOLOR)}"></a>'

TYPE_TOKEN = re.compile(r"\[([a-zA-Z/{}]+)\](?![(\[])")
MODULE_LINK = re.compile(r"\[\*\*`?([A-Za-z0-9_-]+)`?\*\*\]\((?:\./)?([A-Za-z0-9_-]+)(?:\.md)?\)")
EXT_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\((https?://[^)\s]+)\)")

def convert_modules(line, pages):
    """module links are matched on the whole line: their label may contain a code span (`name`)"""
    def mod(m):
        label, target = m.group(1), m.group(2)
        if target in pages:
            return module_badge(target)
        return m.group(0)
    return MODULE_LINK.sub(mod, line)

def convert_text(text, pages):
    if EXT2HTML:
        text = EXT_LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    def typ(m):
        html = type_badges(m.group(1))
        return html if html is not None else m.group(0)
    return TYPE_TOKEN.sub(typ, text)

def convert_file(path, pages):
    src = path.read_text(encoding="utf-8")
    out, fence = [], False
    for line in src.split("\n"):
        if line.strip().startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        line = convert_modules(line, pages)
        parts = re.split(r"(`[^`\n]*`)", line)          # keep code spans untouched
        for i in range(0, len(parts), 2):
            parts[i] = convert_text(parts[i], pages)
        if IN_CODE:
            for i in range(1, len(parts), 2):
                parts[i] = convert_code_span(parts[i])
        out.append("".join(parts))
    new = "\n".join(out)
    if new != src:
        path.write_text(new, encoding="utf-8")
        print(f"badges: converted {path}")

def main():
    wiki = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "wiki")
    pages = {p.stem for p in wiki.glob("*.md")}
    for p in sorted(wiki.glob("*.md")):
        convert_file(p, pages)

if __name__ == "__main__":
    main()
