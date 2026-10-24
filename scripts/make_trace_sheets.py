"""Generate 1404x1872 grayscale tracing-practice sheets for the reMarkable 2.

Each row holds two characters; per character: [dark model][faint trace][blank], with centre guides.

usage:
  make_trace_sheets.py --font NotoSansCJKjp-Regular.otf --out OUTDIR --set hiragana
  make_trace_sheets.py ... --set katakana | hiragana-voiced | katakana-voiced
  make_trace_sheets.py ... --set kanji --grade 1 --kanjidic kanjidic2.xml.gz
Prints one line per page: <filename>\t<template name>
"""
import argparse, gzip, os
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

W, H, CELL, COLS, ROWS = 1404, 1872, 216, 6, 8
PER_PAGE = ROWS * COLS // 3
BORDER, GUIDE, MODEL, TRACE = 90, 170, 40, 205

HIRA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")
HIRA_V = list("がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉっゃゅょゎ")


def kata(chars):
    return [chr(ord(c) + 0x60) for c in chars]


def kanji_for_grade(path, grade):
    out = []
    with gzip.open(path, "rb") as f:
        for _, el in ET.iterparse(f):
            if el.tag == "character":
                if el.findtext("misc/grade") == str(grade):
                    out.append((int(el.findtext("misc/stroke_count") or 99), el.findtext("literal")))
                el.clear()
    return [c for _, c in sorted(out)]  # simpler kanji first


def dashed(d, p0, p1, fill):
    (x0, y0), (x1, y1) = p0, p1
    if x0 == x1:
        for y in range(y0, y1, 16):
            d.line([(x0, y), (x0, min(y + 8, y1))], fill=fill, width=2)
    else:
        for x in range(x0, x1, 16):
            d.line([(x, y0), (min(x + 8, x1), y0)], fill=fill, width=2)


def page(chars, font):
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
    # thicker divider between the two characters of a row
    d.line([(x0 + 3 * CELL, y0), (x0 + 3 * CELL, y0 + ROWS * CELL)], fill=BORDER, width=6)
    for n, ch in enumerate(chars):
        r, half = divmod(n, 2)
        cx = x0 + (half * 3) * CELL
        cy = y0 + r * CELL + CELL // 2
        d.text((cx + CELL // 2, cy), ch, font=font, fill=MODEL, anchor="mm")
        d.text((cx + CELL + CELL // 2, cy), ch, font=font, fill=TRACE, anchor="mm")
    return img


ap = argparse.ArgumentParser()
ap.add_argument("--font", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--set", required=True, choices=["hiragana", "katakana", "hiragana-voiced", "katakana-voiced", "kanji"])
ap.add_argument("--grade", type=int)
ap.add_argument("--kanjidic")
a = ap.parse_args()

if a.set == "hiragana": chars, label, slug = HIRA, "Hiragana trace", "Hiragana Trace"
elif a.set == "hiragana-voiced": chars, label, slug = HIRA_V, "Hiragana voiced trace", "Hiragana Voiced Trace"
elif a.set == "katakana": chars, label, slug = kata(HIRA), "Katakana trace", "Katakana Trace"
elif a.set == "katakana-voiced": chars, label, slug = kata(HIRA_V), "Katakana voiced trace", "Katakana Voiced Trace"
else:
    chars, label, slug = kanji_for_grade(a.kanjidic, a.grade), "Kanji G%d trace" % a.grade, "Kanji G%d Trace" % a.grade

font = ImageFont.truetype(a.font, 150)
os.makedirs(a.out, exist_ok=True)
pages = [chars[i:i + PER_PAGE] for i in range(0, len(chars), PER_PAGE)]
for i, ch in enumerate(pages, 1):
    fn = "%s %d" % (slug, i)
    page(ch, font).save(os.path.join(a.out, fn + ".png"), optimize=True)
    print("%s\t%s %d/%d (%s–%s)" % (fn, label, i, len(pages), ch[0], ch[-1]))
