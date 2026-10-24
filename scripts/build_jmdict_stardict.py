"""Convert JMdict (EDRDG) to a StarDict dictionary for KOReader.

usage: build_jmdict_stardict.py JMdict_e.gz OUTDIR

- Entries sharing a headword are ordered by commonness (JMdict priority tags), so a tap on か み
  shows 紙 / 神 / 髪 before obscure homographs.
- Part-of-speech tags are shortened and shown only when they change between senses.
- Full-width / half-width headword variants also get an NFKC alias (ＣＤ is also findable as CD).
"""
import gzip, html, os, re, struct, sys, unicodedata
import xml.etree.ElementTree as ET

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
name = "JMdict-en"

COMMON = {"news1", "ichi1", "spec1", "spec2", "gai1"}
POS_SHORT = {
    "noun or participle which takes the aux. verb suru": "suru-noun",
    "transitive verb": "vt",
    "intransitive verb": "vi",
}


def clean_pos(p):
    p = re.sub(r" \([a-z\-]+\)", "", p)  # drop romaji glosses: "(futsuumeishi)", "(common)"
    return POS_SHORT.get(p, p)


def rank_of(el):
    tags = [t.text for t in el.iter() if t.tag in ("ke_pri", "re_pri") and t.text]
    score = 0 if COMMON & set(tags) else 1 if tags else 2
    nf = min((int(t[2:]) for t in tags if re.fullmatch(r"nf\d\d", t)), default=99)
    return score, nf


entries = []  # (words, html bytes, rank)
seq = 0
with gzip.open(src, "rb") as f:
    for _, el in ET.iterparse(f):
        if el.tag != "entry":
            continue
        kebs = [k.findtext("keb") for k in el.findall("k_ele")]
        rebs = [r.findtext("reb") for r in el.findall("r_ele")]
        score, nf = rank_of(el)
        head = "、".join(kebs[:3]) if kebs else rebs[0]
        parts = ["<b>%s</b>" % html.escape(head)]
        if score == 0:
            parts.append(" ★")
        if kebs:
            parts.append(" 【%s】" % html.escape("、".join(rebs)))
        parts.append("<ol>")
        prev_pos = None
        for s in el.findall("sense"):
            gl = [g.text for g in s.findall("gloss") if g.text]
            if not gl:
                continue
            pos = [clean_pos(p.text) for p in s.findall("pos") if p.text] or prev_pos or []
            tag = ""
            if pos and pos != prev_pos:
                tag = "<i>%s</i> " % html.escape(", ".join(pos))
            prev_pos = pos
            notes = [t.text for t in s.iter() if t.tag in ("misc", "field", "dial") and t.text]
            inf = [t.text for t in s.findall("s_inf") if t.text]
            note = " <small>(%s)</small>" % html.escape("; ".join(notes + inf)) if notes or inf else ""
            parts.append("<li>%s%s%s</li>" % (tag, html.escape("; ".join(gl)), note))
        parts.append("</ol>")
        words = []
        for w in kebs + rebs:
            for v in (w, unicodedata.normalize("NFKC", w)):
                if v and v not in words:
                    words.append(v)
        entries.append((words, "".join(parts).encode("utf-8"), (score, nf, seq)))
        seq += 1
        el.clear()

dict_buf = bytearray()
idx = []
for words, data, rank in entries:
    off, size = len(dict_buf), len(data)
    dict_buf += data
    for w in words:
        idx.append((w.encode("utf-8"), off, size, rank))

# StarDict order: ASCII case-insensitive compare, then plain byte compare; ties by commonness
idx.sort(key=lambda t: (bytes(c + 32 if 65 <= c <= 90 else c for c in t[0]), t[0], t[3]))

with open(os.path.join(outdir, name + ".dict"), "wb") as f:
    f.write(dict_buf)
with open(os.path.join(outdir, name + ".idx"), "wb") as f:
    for w, off, size, _ in idx:
        f.write(w + b"\0" + struct.pack(">II", off, size))
idxsize = os.path.getsize(os.path.join(outdir, name + ".idx"))
with open(os.path.join(outdir, name + ".ifo"), "w", encoding="utf-8", newline="\n") as f:
    f.write("StarDict's dict ifo file\nversion=2.4.2\n")
    f.write("bookname=JMdict (English)\nwordcount=%d\nidxfilesize=%d\n" % (len(idx), idxsize))
    f.write("sametypesequence=h\nauthor=EDRDG (Electronic Dictionary Research and Development Group)\n")
    f.write("website=https://www.edrdg.org/jmdict/j_jmdict.html\n")
    f.write("description=JMdict, CC BY-SA 4.0 (https://www.edrdg.org/edrdg/licence.html). Converted for personal use.\n")
print("entries", len(entries), "index words", len(idx), "dict bytes", len(dict_buf), "idx bytes", idxsize)
