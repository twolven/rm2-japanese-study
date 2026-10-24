"""Convert KANJIDIC2 (EDRDG) to a StarDict dictionary for KOReader.

usage: build_kanjidic_stardict.py kanjidic2.xml.gz OUTDIR
"""
import gzip, html, os, struct, sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kana2romaji import to_romaji

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
name = "KANJIDIC2-en"

entries = []  # (headword, html bytes)
with gzip.open(src, "rb") as f:
    for _, el in ET.iterparse(f):
        if el.tag != "character":
            continue
        lit = el.findtext("literal")
        misc = el.find("misc")
        on, kun, mean = [], [], []
        for rm in el.iterfind("reading_meaning/rmgroup"):
            for r in rm.findall("reading"):
                t = r.get("r_type")
                if t == "ja_on":
                    on.append(r.text)
                elif t == "ja_kun":
                    kun.append(r.text)
            mean += [m.text for m in rm.findall("meaning") if "m_lang" not in m.attrib]
        facts = []
        if misc is not None:
            sc = misc.findtext("stroke_count")
            if sc: facts.append("%s strokes" % sc)
            g = misc.findtext("grade")
            if g:
                facts.append("jōyō grade %s" % g if int(g) <= 6 else "jōyō (secondary)" if g == "8" else "jinmeiyō" if g in ("9", "10") else "grade %s" % g)
            jl = misc.findtext("jlpt")
            if jl: facts.append("old JLPT %s" % jl)
            fr = misc.findtext("freq")
            if fr: facts.append("freq #%s" % fr)
        h = ["<b>%s</b> " % html.escape(lit)]
        if facts:
            h.append("<small>%s</small><br>" % html.escape(" · ".join(facts)))
        def rd(x):  # "た.べる" -> "た.べる (ta.beru)"; "-" marks affixes
            r = ".".join(to_romaji(seg) for seg in x.replace("-", "").split("."))
            return "%s (%s)" % (x, r.lower())
        if on:   h.append("音 on: %s<br>" % html.escape("、".join(rd(x) for x in on)))
        if kun:  h.append("訓 kun: %s<br>" % html.escape("、".join(rd(x) for x in kun)))
        if mean: h.append(html.escape("; ".join(mean)))
        entries.append((lit, "".join(h).encode("utf-8")))
        el.clear()

dict_buf, idx = bytearray(), []
for w, data in entries:
    idx.append((w.encode("utf-8"), len(dict_buf), len(data)))
    dict_buf += data
idx.sort(key=lambda t: (bytes(c + 32 if 65 <= c <= 90 else c for c in t[0]), t[0]))

with open(os.path.join(outdir, name + ".dict"), "wb") as f:
    f.write(dict_buf)
with open(os.path.join(outdir, name + ".idx"), "wb") as f:
    for w, off, size in idx:
        f.write(w + b"\0" + struct.pack(">II", off, size))
with open(os.path.join(outdir, name + ".ifo"), "w", encoding="utf-8", newline="\n") as f:
    f.write("StarDict's dict ifo file\nversion=2.4.2\n")
    f.write("bookname=KANJIDIC2 (English)\nwordcount=%d\nidxfilesize=%d\n" % (len(idx), os.path.getsize(os.path.join(outdir, name + ".idx"))))
    f.write("sametypesequence=h\nauthor=EDRDG (Electronic Dictionary Research and Development Group)\n")
    f.write("website=https://www.edrdg.org/wiki/index.php/KANJIDIC_Project\n")
    f.write("description=KANJIDIC2, CC BY-SA 4.0 (https://www.edrdg.org/edrdg/licence.html). Converted for personal use.\n")
print("kanji", len(entries))
