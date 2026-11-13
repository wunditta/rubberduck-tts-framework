#!/usr/bin/env python3
"""Expand the documentation shorthands of the wiki pages into badges before the pages are deployed.

Run from the repository root (the workflow does): python3 .github/badges.py wiki
Configuration: .github/badges.json (next to this file): types and colours, module colour and icon, badge look, options.

What is converted (outside fenced code blocks and code spans):
  [str] [num{}] [str/tab] ...        a type token: every alternative (split by "/") must be a known type from badges.json,
                                     "{}" suffixes mean "table of"; unknown tokens are left as they are
                                     the badges are SVG files the script writes into <wiki>/badges/ (look: "badge" in badges.json)
  [**name**](name.md) / (./name)     a module link whose page wiki/name.md exists: badge that links to the page
  [text](https://...)                an external link becomes an HTML <a> (optional, externalLinksToHtml): the configure-wiki
                                     action crashes on absolute URLs in Markdown links, HTML passes through untouched
"""
import json, re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CFG = json.loads((HERE / "badges.json").read_text(encoding="utf-8"))
TYPES = CFG["types"]
MODCOLOR = CFG.get("modulecolor", "#d4a017")    # fill of module badges ...
MODCOLORS = CFG.get("modules", {})               # ... unless the module has its own: "modules": {"core": "#...", "statemachine": "#..."}
EXT2HTML = CFG.get("externalLinksToHtml", True)
IN_CODE = CFG.get("badgesInCodeSpans", True)     # code spans with type tokens become <code> with badges (fenced blocks never)
B = CFG.get("badge", {})
HEIGHT = int(B.get("height", 18))                # px; the text inside is fontSize * height
FONTSIZE = float(B.get("fontSize", 0.9))         # multiple of the height
RADIUS = float(B.get("radius", 0.25))            # multiple of the height
PADDING = float(B.get("padding", 0.16))          # multiple of the height, left and right
FONT = B.get("font", "Verdana, DejaVu Sans, sans-serif")
TEXTCOLOR = B.get("textColor", "#000000")        # text colour of the type badges
MODTEXTCOLOR = B.get("moduleTextColor", TEXTCOLOR)  # text colour of the module badges (default: textColor)
CHARWIDTH = float(B.get("charWidth", 0.62))      # fallback glyph width (multiple of the font size) for characters not in VERDANA
CODEHEIGHT = int(B.get("codeHeight", 16))        # px; badges inside code spans (GitHub renders code at 85% of the body size)
MARGIN = float(B.get("textMargin", 0.08))        # safety margin on the measured text width (multiple of the font size) - room for fallback fonts
ALTGAP = B.get("altGap", "&thinsp;")             # between the badges of alternatives ([str/num])
ALTGAPCODE = B.get("altGapCode", "")            # the same inside code spans (monospace renders &thinsp; as a full space)
TABLEMIN = B.get("tableMinWidth", True)          # a column of badge-only cells gets its header widened with &nbsp; to the widest badge, so the column cannot shrink the images
LASTWIDTH = {}                                   # file name -> badge width in px (for TABLEMIN)
# Verdana advance widths in 1/2048 em (from the font's metrics); the text is centred, so a small error only moves the padding
VERDANA = {}
for chars, w in [("a", 1228), ("b", 1259), ("c", 1061), ("d", 1259), ("e", 1200), ("f", 702), ("g", 1259), ("h", 1265), ("i", 554), ("j", 666),
                 ("k", 1159), ("l", 554), ("m", 1960), ("n", 1265), ("o", 1227), ("p", 1259), ("q", 1259), ("r", 865), ("s", 1046), ("t", 772),
                 ("u", 1265), ("v", 1172), ("w", 1660), ("x", 1172), ("y", 1172), ("z", 1046),
                 ("A", 1395), ("B", 1413), ("C", 1430), ("D", 1593), ("E", 1294), ("F", 1178), ("G", 1588), ("H", 1540), ("I", 865), ("J", 937),
                 ("K", 1435), ("L", 1165), ("M", 1727), ("N", 1546), ("O", 1612), ("P", 1235), ("Q", 1612), ("R", 1424), ("S", 1400), ("T", 1262),
                 ("U", 1499), ("V", 1395), ("W", 2033), ("X", 1395), ("Y", 1262), ("Z", 1395),
                 ("0123456789", 1303), ("{}", 1303), ("/", 933), ("-", 933), ("_", 1303), (".", 745), (" ", 720), ("[]", 933), ("()", 850), (",", 745)]:
    for ch in chars:
        VERDANA[ch] = w / 2048

def text_width(text, fs):
    return sum(VERDANA.get(ch, CHARWIDTH) for ch in text) * fs * (1 + MARGIN)
BASELINE = float(B.get("baseline", 0.37))        # baseline below the badge centre, as a multiple of the font size (centres the x-height)
BADGEDIR = B.get("dir", "badges")                # folder inside the wiki folder that receives the SVG files
ALIGN = B.get("align", "texttop")                # <img align=...>: GitHub strips style attributes but keeps align (baseline, middle, absmiddle, absbottom, texttop, top, bottom)
SHIFT = float(B.get("shift", 0))                 # transparent band added to the image, as a multiple of the height: >0 below (the badge moves up), <0 above (moves down)
CODESHIFT = float(B.get("codeShift", SHIFT))     # type badges inside code spans: their own shift (default: shift)
MODSCALE = float(B.get("moduleScale", 1))        # module badges: height = height * moduleScale
MODSHIFT = float(B.get("moduleShift", SHIFT))    # module badges: their own shift (default: shift)
ICON = B.get("icon")                             # module badges: {"path": svg path data, "box": [x, y, w, h] of the path, "rotate": 90, "height": 0.84, "padding": 0.2, "gap": 0.12, "color": "#d9690b"}
WIKI = None                                      # set in main(): the wiki folder
WRITTEN = {}                                     # text,fill -> file name

def icon_svg(x0, height):
    """the module icon at x0 (left edge), vertically centred; returns (svg fragment, width)"""
    bx, by, bw, bh = ICON["box"]
    rot = ICON.get("rotate", 0)
    # size of the icon after the rotation (90/270 swap width and height)
    pw, ph = (bh, bw) if rot % 180 == 90 else (bw, bh)
    ih = height * float(ICON.get("height", 0.84))
    sc = ih / ph
    iw = pw * sc
    y0 = (height - ih) / 2
    # move the path's box to the origin, rotate about the origin, shift the rotated box to positive coordinates, then scale and place
    if rot % 360 == 90:    post = f"translate({bh},0) rotate(90)"
    elif rot % 360 == 270: post = f"translate(0,{bw}) rotate(-90)"
    elif rot % 360 == 180: post = f"translate({bw},{bh}) rotate(180)"
    else:                  post = ""
    tf = f"translate({x0:.2f},{y0:.2f}) scale({sc:.5f}) {post} translate({-bx},{-by})"
    return f'<path d="{ICON["path"]}" fill="{ICON.get("color", TEXTCOLOR)}" transform="{tf}"/>', iw

def badge_file(text, fill, with_icon=False, height=None, shift=None):
    """write (once) the SVG for this text/colour/height into <wiki>/<dir>/ and return its URL for <img src>"""
    H = height or HEIGHT
    S = SHIFT if shift is None else shift
    key = (text, fill, with_icon, H, S)
    if key not in WRITTEN:
        fs = H * FONTSIZE
        tw = round(text_width(text, fs), 1)
        pad = H * PADDING
        icon, iw, left = "", 0.0, pad
        if with_icon and ICON:
            icon, iw = icon_svg(H * float(ICON.get("padding", 0.2)), H)
            left = H * float(ICON.get("padding", 0.2)) + iw + H * float(ICON.get("gap", 0.12))
        w = round(left + tw + pad, 1)
        r = round(H * RADIUS, 1)
        band = round(abs(S) * H, 1)                       # transparent space above (shift<0) or below (shift>0) the badge
        top = band if S < 0 else 0
        total = round(H + band, 1)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{total}" viewBox="0 0 {w} {total}" role="img" aria-label="{text}">'
               f'<g transform="translate(0,{top})"><rect width="{w}" height="{H}" rx="{r}" fill="{fill}"/>{icon}'
               f'<text x="{left + tw/2:.1f}" y="{H/2 + fs*BASELINE:.1f}" text-anchor="middle" '
               f'font-family="{FONT}" font-size="{fs:.1f}" fill="{MODTEXTCOLOR if with_icon else TEXTCOLOR}">{html_escape(text)}</text></g></svg>')
        name = re.sub(r"[^A-Za-z0-9]+", "-", text.replace("{}", "-tab")).strip("-") + "-" + fill.lstrip("#") + ("-m" if with_icon else "") + (f"-{H}" if H != HEIGHT else "") + (f"-s{S}".replace(".", "_") if S != SHIFT else "") + ".svg"
        (WIKI / BADGEDIR).mkdir(parents=True, exist_ok=True)
        (WIKI / BADGEDIR / name).write_text(svg, encoding="utf-8")
        WRITTEN[key] = name
        LASTWIDTH[name] = w
    return f"{BADGEDIR}/{WRITTEN[key]}"

def img(text, fill, with_icon=False, height=None, shift=None):
    H = height or HEIGHT
    S = SHIFT if shift is None else shift
    total = round(H * (1 + abs(S)))
    return f'<img alt="{text}" src="{badge_file(text, fill, with_icon, H, S)}" height="{total}" align="{ALIGN}">'

def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def convert_code_span(span):
    """`setTable(tgt [any{}], ...)` -> <code>setTable(tgt <img ...>, ...)</code> when it holds a known type token; else unchanged"""
    inner = span[1:-1]
    if not TYPE_TOKEN.search(inner):
        return span
    pieces, pos, found = [], 0, False
    for m in TYPE_TOKEN.finditer(inner):
        html = type_badges(m.group(1), CODEHEIGHT, True)
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

def type_badges(inner, height=None, incode=False):
    """[str/num{}] -> HTML of one badge per alternative, or None if any base is unknown.
    [(str/tab){}] -> one badge "str/tab{}" (a table whose items are strings or tables), coloured like a table."""
    g = GROUP_TOKEN.fullmatch(inner)
    if g:
        bases = g.group(1).split("/")
        if any(b not in TYPES for b in bases) or "tab" not in TYPES:
            return None
        return img(g.group(1) + g.group(2), TYPES["tab"], False, height, CODESHIFT if incode else None)
    out = []
    for part in inner.split("/"):
        base, suf = part, ""
        while base.endswith("{}"):
            base, suf = base[:-2], suf + "{}"
        if base not in TYPES:
            return None
        text = base + suf
        out.append(img(text, TYPES[base], False, height, CODESHIFT if incode else None))
    return (ALTGAPCODE if incode else ALTGAP).join(out)

def module_badge(name):
    return f'<a href="./{name}">{img(name, MODCOLORS.get(name, MODCOLOR), True, round(HEIGHT * MODSCALE, 1), MODSHIFT)}</a>'

TYPE_TOKEN = re.compile(r"\[((?:[a-zA-Z/{}]+|\([a-zA-Z/]+\)(?:\{\})+))\](?![(\[])")
GROUP_TOKEN = re.compile(r"\(([a-zA-Z/]+)\)((?:\{\})+)")
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

CELL_IMG = re.compile(r'<img alt="[^"]*" src="[^"]*/([^"/]+\.svg)"[^>]*>')

def badge_only_width(cell):
    """width in px of the badges in a cell that holds nothing but badges, else 0"""
    inner = cell.strip()
    if not inner:
        return 0
    rest = CELL_IMG.sub("", inner)
    rest = re.sub(r"</?a[^>]*>|&thinsp;", "", rest).strip()
    if rest:
        return 0                                      # the cell holds text as well: that already gives it a width
    return sum(LASTWIDTH.get(m.group(1), 0) for m in CELL_IMG.finditer(inner))

def pad_table(lines):
    """a whole table (header, separator, rows): a column holding badge-only cells gets its header cell widened with
    &nbsp; on both sides (one is ~0.28 em) until it is as wide as the widest badge cell, so the column cannot shrink
    the images; the rows themselves stay untouched and the header text stays centred"""
    if len(lines) < 3:
        return lines
    rows = [l.split("|") for l in lines]
    head = rows[0]
    for i in range(len(head)):
        text = head[i].strip()
        if not text:
            continue
        widest = max((badge_only_width(r[i]) for r in rows[2:] if i < len(r)), default=0)
        have = text_width(re.sub(r"[*_`]", "", text), 16)       # the header text at GitHub's body size (bold: roughly)
        if widest <= have:
            continue
        n = int((widest - have) / (16 * 0.28)) + 3
        half = "&nbsp;" * ((n + 1) // 2)
        head[i] = " " + half + text + half + " "
    lines[0] = "|".join(head)
    return lines

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
    if TABLEMIN:
        # tables as blocks: consecutive lines starting with "|"
        i = 0
        while i < len(out):
            if out[i].lstrip().startswith("|"):
                j = i
                while j < len(out) and out[j].lstrip().startswith("|"):
                    j += 1
                out[i:j] = pad_table(out[i:j])
                i = j
            else:
                i += 1
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
