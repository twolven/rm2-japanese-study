import gzip, struct, sys, os, html
import xml.etree.ElementTree as ET

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
name = "JMdict-en"

entries = []  # (list of headwords, html bytes)
with gzip.open(src, "rb") as f:
    for _, el in ET.iterparse(f):
        if el.tag != "entry":
            continue
        kebs = [k.findtext("keb") for k in el.findall("k_ele")]
        rebs = [r.findtext("reb") for r in el.findall("r_ele")]
        parts = []
        head = "、".join(kebs[:3]) if kebs else ""
        parts.append("<b>%s</b>" % html.escape(head or rebs[0]))
        if kebs:
            parts.append(" 【%s】" % html.escape("、".join(rebs)))
        parts.append("<ol>")
        for s in el.findall("sense"):
            gl = [g.text for g in s.findall("gloss") if g.text]
            if not gl:
                continue
            pos = ", ".join(p.text for p in s.findall("pos") if p.text)
            tag = "<i>%s</i> " % html.escape(pos) if pos else ""
            parts.append("<li>%s%s</li>" % (tag, html.escape("; ".join(gl))))
        parts.append("</ol>")
        words = []
        for w in kebs + rebs:
            if w and w not in words:
                words.append(w)
        entries.append((words, "".join(parts).encode("utf-8")))
        el.clear()

dict_buf = bytearray()
idx = []
for words, data in entries:
    off, size = len(dict_buf), len(data)
    dict_buf += data
    for w in words:
        idx.append((w.encode("utf-8"), off, size))

# StarDict order: ASCII case-insensitive compare, then plain byte compare
def key(t):
    b = t[0]
    return (bytes(c + 32 if 65 <= c <= 90 else c for c in b), b)
idx.sort(key=key)

with open(os.path.join(outdir, name + ".dict"), "wb") as f:
    f.write(dict_buf)
with open(os.path.join(outdir, name + ".idx"), "wb") as f:
    for w, off, size in idx:
        f.write(w + b"\0" + struct.pack(">II", off, size))
idxsize = os.path.getsize(os.path.join(outdir, name + ".idx"))
with open(os.path.join(outdir, name + ".ifo"), "w", encoding="utf-8", newline="\n") as f:
    f.write("StarDict's dict ifo file\nversion=2.4.2\n")
    f.write("bookname=JMdict (English)\nwordcount=%d\nidxfilesize=%d\n" % (len(idx), idxsize))
    f.write("sametypesequence=h\nauthor=EDRDG (Electronic Dictionary Research and Development Group)\n")
    f.write("website=https://www.edrdg.org/jmdict/j_jmdict.html\n")
    f.write("description=JMdict, CC BY-SA 4.0 (https://www.edrdg.org/edrdg/licence.html). Converted for personal use.\n")
print("entries", len(entries), "index words", len(idx), "dict bytes", len(dict_buf), "idx bytes", idxsize)
