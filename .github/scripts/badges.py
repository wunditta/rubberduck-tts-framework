#!/usr/bin/env python3
"""Expand the documentation shorthands of the wiki pages into badges before the pages are deployed.

Run from the repository root (the workflow does): python3 .github/scripts/badges.py wiki
Configuration: .github/badges.json (types and colours, module colour, style).

What is converted (outside fenced code blocks and code spans):
  [str] [num{}] [str/tab] ...        a type token: every alternative (split by "/") must be a known type from badges.json,
                                     "{}" suffixes mean "table of"; unknown tokens are left as they are
                                     the badges are SVG files the script writes into <wiki>/badges/ (look: "badge" in badges.json)
  [**name**](name.md) / (./name)     a module link whose page wiki/name.md exists: badge that links to the page
  [text](https://...)                an external link becomes an HTML <a> (optional, externalLinksToHtml): the configure-wiki
                                     action crashes on absolute URLs in Markdown links, HTML passes through untouched
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / ".github" / "badges.json").read_text(encoding="utf-8"))
TYPES = CFG["types"]
MODCOLOR = CFG.get("modulecolor", "#d4a017")
EXT2HTML = CFG.get("externalLinksToHtml", True)
IN_CODE = CFG.get("badgesInCodeSpans", True)     # code spans with type tokens become <code> with badges (fenced blocks never)
B = CFG.get("badge", {})
HEIGHT = int(B.get("height", 18))                # px; the text inside is fontSize * height
FONTSIZE = float(B.get("fontSize", 0.9))         # multiple of the height
RADIUS = float(B.get("radius", 0.25))            # multiple of the height
PADDING = float(B.get("padding", 0.16))          # multiple of the height, left and right
FONT = B.get("font", "Verdana, DejaVu Sans, sans-serif")
TEXTCOLOR = B.get("textColor", "#000000")
CHARWIDTH = float(B.get("charWidth", 0.62))      # average glyph width as a multiple of the font size (Verdana ~0.62)
BASELINE = float(B.get("baseline", 0.37))        # baseline below the badge centre, as a multiple of the font size (centres the x-height)
BADGEDIR = B.get("dir", "badges")                # folder inside the wiki folder that receives the SVG files
ALIGN = B.get("align", "texttop")                # <img align=...>: GitHub strips style attributes but keeps align (baseline, middle, absmiddle, absbottom, texttop, top, bottom)
SHIFT = float(B.get("shift", 0))                 # transparent band added to the image, as a multiple of the height: >0 below (the badge moves up), <0 above (moves down)
ICON = B.get("icon")                             # module badges: {"path": svg path data, "box": [x, y, w, h] of the path, "rotate": 90, "height": 0.84, "padding": 0.2, "gap": 0.12, "color": "#d9690b"}
WIKI = None                                      # set in main(): the wiki folder
WRITTEN = {}                                     # text,fill -> file name

def icon_svg(x0):
    """the module icon at x0 (left edge), vertically centred; returns (svg fragment, width)"""
    bx, by, bw, bh = ICON["box"]
    rot = ICON.get("rotate", 0)
    # size of the icon after the rotation (90/270 swap width and height)
    pw, ph = (bh, bw) if rot % 180 == 90 else (bw, bh)
    ih = HEIGHT * float(ICON.get("height", 0.84))
    sc = ih / ph
    iw = pw * sc
    y0 = (HEIGHT - ih) / 2
    # move the path's box to the origin, rotate about the origin, shift the rotated box to positive coordinates, then scale and place
    if rot % 360 == 90:    post = f"translate({bh},0) rotate(90)"
    elif rot % 360 == 270: post = f"translate(0,{bw}) rotate(-90)"
    elif rot % 360 == 180: post = f"translate({bw},{bh}) rotate(180)"
    else:                  post = ""
    tf = f"translate({x0:.2f},{y0:.2f}) scale({sc:.5f}) {post} translate({-bx},{-by})"
    return f'<path d="{ICON["path"]}" fill="{ICON.get("color", TEXTCOLOR)}" transform="{tf}"/>', iw

def badge_file(text, fill, with_icon=False):
    """write (once) the SVG for this text/colour into <wiki>/<dir>/ and return its URL for <img src>"""
    key = (text, fill, with_icon)
    if key not in WRITTEN:
        fs = HEIGHT * FONTSIZE
        tw = round(len(text) * fs * CHARWIDTH, 1)
        pad = HEIGHT * PADDING
        icon, iw, left = "", 0.0, pad
        if with_icon and ICON:
            icon, iw = icon_svg(HEIGHT * float(ICON.get("padding", 0.2)))
            left = HEIGHT * float(ICON.get("padding", 0.2)) + iw + HEIGHT * float(ICON.get("gap", 0.12))
        w = round(left + tw + pad, 1)
        r = round(HEIGHT * RADIUS, 1)
        band = round(abs(SHIFT) * HEIGHT, 1)              # transparent space above (shift<0) or below (shift>0) the badge
        top = band if SHIFT < 0 else 0
        total = round(HEIGHT + band, 1)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{total}" viewBox="0 0 {w} {total}" role="img" aria-label="{text}">'
               f'<g transform="translate(0,{top})"><rect width="{w}" height="{HEIGHT}" rx="{r}" fill="{fill}"/>{icon}'
               f'<text x="{left + tw/2:.1f}" y="{HEIGHT/2 + fs*BASELINE:.1f}" text-anchor="middle" '
               f'font-family="{FONT}" font-size="{fs:.1f}" fill="{TEXTCOLOR}" textLength="{tw}" lengthAdjust="spacingAndGlyphs">{html_escape(text)}</text></g></svg>')
        name = re.sub(r"[^A-Za-z0-9]+", "-", text.replace("{}", "-tab")).strip("-") + "-" + fill.lstrip("#") + ("-m" if with_icon else "") + ".svg"
        (WIKI / BADGEDIR).mkdir(parents=True, exist_ok=True)
        (WIKI / BADGEDIR / name).write_text(svg, encoding="utf-8")
        WRITTEN[key] = name
    return f"{BADGEDIR}/{WRITTEN[key]}"

def img(text, fill, with_icon=False):
    total = round(HEIGHT * (1 + abs(SHIFT)))
    return f'<img alt="{text}" src="{badge_file(text, fill, with_icon)}" height="{total}" align="{ALIGN}">'

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
        out.append(img(text, TYPES[base]))
    return "".join(out)

def module_badge(name):
    return f'<a href="./{name}">{img(name, MODCOLOR, True)}</a>'

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
    global WIKI
    wiki = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "wiki")
    WIKI = wiki
    pages = {p.stem for p in wiki.glob("*.md")}
    for p in sorted(wiki.glob("*.md")):
        convert_file(p, pages)

if __name__ == "__main__":
    main()
