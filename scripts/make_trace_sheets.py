"""Generate 1404x1872 grayscale stroke-order tracing sheets for the reMarkable 2.

Stroke geometry, stroke order and number positions come from KanjiVG (CC BY-SA 3.0, https://kanjivg.tagaini.net).
Each row holds two characters; per character three cells:
    [model with stroke-order numbers] [faint trace] [blank]       (dashed centre guides throughout)

usage:
  make_trace_sheets.py --kanjivg kanjivg-main.zip --font ANY.otf --out templates --set hiragana
  ... --set katakana | hiragana-voiced | katakana-voiced
  ... --set kanji --grade 1 --kanjidic kanjidic2.xml.gz        (grade 1-6, 8 = rest of jouyou)
Add --manifest templates/manifest.json to register the pages for scripts/add_templates.py.
--font is only used for the small stroke numbers; any font with digits works.
"""
import argparse, gzip, json, math, os, re, zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

W, H, CELL, COLS, ROWS = 1404, 1872, 216, 6, 8
PER_PAGE = ROWS * COLS // 3
BORDER, GUIDE, MODEL, TRACE = 90, 170, 85, 200
SS = 3                       # supersampling factor for smooth strokes
BOX = 109.0                  # KanjiVG coordinate box
GLYPH = 176                  # glyph box in px inside a 216 px cell
STROKE_W = 7.5               # px, in output scale

HIRA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")
HIRA_V = list("がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉっゃゅょゎ")
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOK = re.compile(r"([MmCcSsLlHhVvQqTtZz])|(" + NUM.pattern + ")")


def kata(chars):
    return [chr(ord(c) + 0x60) for c in chars]


def cubic(p0, p1, p2, p3, n=18):
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        yield (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
               u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def parse_path(d):
    """SVG path data -> list of (x, y) points (KanjiVG uses M, C, S and relative forms)."""
    toks, pts, cur, start, last_c2, cmd = TOK.findall(d), [], (0.0, 0.0), None, None, None
    i = 0
    def nums(k):
        nonlocal i
        out = [float(toks[i + j][1]) for j in range(k)]
        i += k
        return out
    while i < len(toks):
        if toks[i][0]:
            cmd = toks[i][0]; i += 1
            if cmd in "Zz":
                if start: pts.append(start); cur = start
                continue
        rel = cmd.islower(); C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "M":
            x, y = nums(2); cur = (ox + x, oy + y); start = cur; pts.append(cur); cmd = "l" if rel else "L"; last_c2 = None
        elif C == "L":
            x, y = nums(2); cur = (ox + x, oy + y); pts.append(cur); last_c2 = None
        elif C == "H":
            x, = nums(1); cur = (ox + x if rel else x, cur[1]); pts.append(cur); last_c2 = None
        elif C == "V":
            y, = nums(1); cur = (cur[0], oy + y if rel else y); pts.append(cur); last_c2 = None
        elif C == "C":
            a = nums(6); p1, p2, p3 = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3]), (ox + a[4], oy + a[5])
            pts += list(cubic(cur, p1, p2, p3)); cur, last_c2 = p3, p2
        elif C == "S":
            a = nums(4); p1 = (2 * cur[0] - last_c2[0], 2 * cur[1] - last_c2[1]) if last_c2 else cur
            p2, p3 = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            pts += list(cubic(cur, p1, p2, p3)); cur, last_c2 = p3, p2
        elif C == "Q":
            a = nums(4); q1, q3 = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            p1 = (cur[0] + 2 / 3 * (q1[0] - cur[0]), cur[1] + 2 / 3 * (q1[1] - cur[1]))
            p2 = (q3[0] + 2 / 3 * (q1[0] - q3[0]), q3[1] + 2 / 3 * (q1[1] - q3[1]))
            pts += list(cubic(cur, p1, p2, q3)); cur, last_c2 = q3, p2
        else:
            raise ValueError("unsupported path command " + cmd)
    return pts


def load_kanjivg(path, wanted):
    """{char: (strokes[[pts]], numbers[(n, x, y)])} from a KanjiVG "main" zip (one SVG per character)."""
    out = {}
    with zipfile.ZipFile(path) as zf:
        members = {os.path.basename(n): n for n in zf.namelist() if n.endswith(".svg")}
        for ch in wanted:
            member = members.get("%05x.svg" % ord(ch))
            if not member:
                continue
            root = ET.fromstring(zf.read(member))
            paths, nums = [], []
            for el in root.iter():
                tag = el.tag.rsplit("}", 1)[-1]
                m = re.search(r"-s(\d+)$", el.get("id") or "")
                if tag == "path" and m:
                    paths.append((int(m.group(1)), el.get("d")))
                elif tag == "text":
                    t = re.search(r"matrix\(1 0 0 1 ([-\d.]+) ([-\d.]+)\)", el.get("transform", ""))
                    if t and (el.text or "").strip().isdigit():
                        nums.append((int(el.text), float(t.group(1)), float(t.group(2))))
            out[ch] = ([parse_path(d) for _, d in sorted(paths)], sorted(nums))
    return out


def kanji_for_grade(path, grade):
    out = []
    with gzip.open(path, "rb") as f:
        for _, el in ET.iterparse(f):
            if el.tag == "character":
                if el.findtext("misc/grade") == str(grade):
                    out.append((int(el.findtext("misc/stroke_count") or 99), el.findtext("literal")))
                el.clear()
    return [c for _, c in sorted(out)]  # simpler kanji first


def stroke_mask(strokes, width):
    """Antialiased stroke mask (L, 0 = nothing, 255 = ink) the size of one cell."""
    size = CELL * SS
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    k = GLYPH / BOX * SS
    off = (size - BOX * k) / 2
    r = width * SS / 2
    for pts in strokes:
        xy = [(off + x * k, off + y * k) for x, y in pts]
        d.line(xy, fill=255, width=int(width * SS), joint="curve")
        for x, y in (xy[0], xy[-1]):  # round caps
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return m.resize((CELL, CELL), Image.LANCZOS)


def dashed(d, p0, p1, fill):
    (x0, y0), (x1, y1) = p0, p1
    if x0 == x1:
        for y in range(y0, y1, 16):
            d.line([(x0, y), (x0, min(y + 8, y1))], fill=fill, width=2)
    else:
        for x in range(x0, x1, 16):
            d.line([(x, y0), (min(x + 8, x1), y0)], fill=fill, width=2)


def page(chars, vg, numfont):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    x0, y0 = (W - COLS * CELL) // 2, (H - ROWS * CELL) // 2
    for r in range(ROWS):
        for c in range(COLS):
            x, y = x0 + c * CELL, y0 + r * CELL
            dashed(d, (x + CELL // 2, y + 6), (x + CELL // 2, y + CELL - 6), GUIDE)
            dashed(d, (x + 6, y + CELL // 2), (x + CELL - 6, y + CELL // 2), GUIDE)
    for i in range(COLS + 1):
        d.line([(x0 + i * CELL, y0), (x0 + i * CELL, y0 + ROWS * CELL)], fill=BORDER, width=3)
    for i in range(ROWS + 1):
        d.line([(x0, y0 + i * CELL), (x0 + COLS * CELL, y0 + i * CELL)], fill=BORDER, width=3)
    d.line([(x0 + 3 * CELL, y0), (x0 + 3 * CELL, y0 + ROWS * CELL)], fill=BORDER, width=6)
    k = GLYPH / BOX
    off = (CELL - BOX * k) / 2
    for n, ch in enumerate(chars):
        r, half = divmod(n, 2)
        cx, cy = x0 + half * 3 * CELL, y0 + r * CELL
        strokes, numbers = vg[ch]
        mask = stroke_mask(strokes, STROKE_W)
        img.paste(MODEL, (cx, cy), mask)
        img.paste(TRACE, (cx + CELL, cy), mask)
        for num, nx, ny in numbers:  # stroke-order numbers with a white halo
            d.text((cx + off + nx * k, cy + off + ny * k), str(num), font=numfont, fill=0,
                   anchor="mm", stroke_width=3, stroke_fill=255)
    return img


ap = argparse.ArgumentParser()
ap.add_argument("--kanjivg", required=True)
ap.add_argument("--font", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--set", required=True, choices=["hiragana", "katakana", "hiragana-voiced", "katakana-voiced", "kanji"])
ap.add_argument("--grade", type=int)
ap.add_argument("--kanjidic")
ap.add_argument("--manifest")
a = ap.parse_args()

if a.set == "hiragana": chars, label, slug = HIRA, "Hiragana trace", "Hiragana Trace"
elif a.set == "hiragana-voiced": chars, label, slug = HIRA_V, "Hiragana voiced trace", "Hiragana Voiced Trace"
elif a.set == "katakana": chars, label, slug = kata(HIRA), "Katakana trace", "Katakana Trace"
elif a.set == "katakana-voiced": chars, label, slug = kata(HIRA_V), "Katakana voiced trace", "Katakana Voiced Trace"
else:
    chars, label, slug = kanji_for_grade(a.kanjidic, a.grade), "Kanji G%d trace" % a.grade, "Kanji G%d Trace" % a.grade

vg = load_kanjivg(a.kanjivg, chars)
missing = [c for c in chars if c not in vg]
if missing:
    print("warning: not in KanjiVG, skipped:", "".join(missing))
    chars = [c for c in chars if c in vg]
numfont = ImageFont.truetype(a.font, 22)
os.makedirs(a.out, exist_ok=True)
entries = []
pages = [chars[i:i + PER_PAGE] for i in range(0, len(chars), PER_PAGE)]
for i, ch in enumerate(pages, 1):
    fn = "%s %d" % (slug, i)
    # the rM2 panel shows 16 gray levels; posterizing halves the PNG size (matters: the system partition is small)
    page(ch, vg, numfont).point(lambda v: min(255, round(v / 17) * 17)).save(os.path.join(a.out, fn + ".png"), optimize=True)
    entries.append({"filename": fn, "name": "%s %d/%d (%s–%s)" % (label, i, len(pages), ch[0], ch[-1])})
    print("%s\t%s" % (fn, entries[-1]["name"]))
if a.manifest:
    cur = json.load(open(a.manifest, encoding="utf-8")) if os.path.exists(a.manifest) else []
    mine = {e["filename"] for e in entries}
    cur = [e for e in cur if e["filename"] not in mine] + entries
    json.dump(cur, open(a.manifest, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
