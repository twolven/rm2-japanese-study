# reMarkable 2 Japanese study kit

Tools for studying Japanese on a reMarkable 2 running [xovi](https://github.com/asivery/xovi) +
[AppLoad](https://github.com/asivery/rm-appload) + [KOReader](https://github.com/koreader/koreader):

- **Dictionaries for KOReader tap-to-lookup** — build StarDict files from the official EDRDG data
  - `build_jmdict_stardict.py` — JMdict (words, ~219k entries)
  - `build_kanjidic_stardict.py` — KANJIDIC2 (single kanji: on/kun readings, meanings, strokes, grade, JLPT)
- **Notebook templates** (1404×1872 grayscale PNG, the rM2 resolution)
  - kana practice grid (large squares, dashed centre guides)
  - genkō yōshi manuscript paper (20×20 with centre gutter)
  - tracing sheets: hiragana, katakana, and kanji by school grade (dark model → faint trace → blank, with guides)
- **Setup notes** for the xovi / Vellum / KOReader stack on firmware 3.25.x — [docs/SETUP.md](docs/SETUP.md)

Pre-rendered templates for hiragana, katakana and grade-1 kanji are in [`templates/`](templates/).
The dictionaries are not committed (they are built from upstream data, see below).

## Requirements

Python 3.9+ and [Pillow](https://pypi.org/project/Pillow/) (templates only). Dictionary scripts use the standard library.

## Build the dictionaries

```sh
curl -LO https://www.edrdg.org/pub/Nihongo/JMdict_e.gz
curl -LO https://www.edrdg.org/kanjidic/kanjidic2.xml.gz
python scripts/build_jmdict_stardict.py    JMdict_e.gz      out/JMdict-en
python scripts/build_kanjidic_stardict.py  kanjidic2.xml.gz out/KANJIDIC2-en
```

Copy each output folder into KOReader's `data/dict/` directory and restart KOReader.
KOReader's bundled Japanese plugin handles deinflection (食べました → 食べる).

## Build templates

You need a Japanese font (e.g. [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk), SIL OFL; not included).

```sh
python scripts/make_practice_grids.py templates/                       # kana grid + genkō yōshi
python scripts/make_trace_sheets.py --font NotoSansCJKjp-Regular.otf --out templates --set hiragana
python scripts/make_trace_sheets.py --font NotoSansCJKjp-Regular.otf --out templates --set katakana
python scripts/make_trace_sheets.py --font NotoSansCJKjp-Regular.otf --out templates \
        --set kanji --grade 2 --kanjidic kanjidic2.xml.gz               # grades 1–6, 8
```

Sets also include `hiragana-voiced` and `katakana-voiced`. Kanji sheets are ordered by stroke count.

## Install templates on the tablet

```sh
scp templates/*.png root@<tablet>:/usr/share/remarkable/templates/
scp root@<tablet>:/usr/share/remarkable/templates/templates.json templates.json.bak   # keep a backup
python scripts/add_templates.py templates.json.bak templates/manifest.json templates.json
scp templates.json root@<tablet>:/usr/share/remarkable/templates/templates.json
ssh root@<tablet> systemctl restart xochitl
```

`add_templates.py` is idempotent. A firmware update replaces the system partition, so re-run the install afterwards.
For other grades, add entries to `templates/manifest.json` (the `make_trace_sheets.py` output prints `filename<TAB>name` lines).

## Status

Built and installed on an rM2 running firmware 3.25.1.1. Dictionary files are valid StarDict 2.4.2 and were
spot-checked by index lookup; on-device lookup rendering was not part of the automated checks.
Use at your own risk — editing the templates folder and running xovi are unsupported by reMarkable.

## Licenses and data attribution

- Code in this repository: MIT (see [LICENSE](LICENSE)).
- JMdict and KANJIDIC2 are © the Electronic Dictionary Research and Development Group, used under
  [CC BY-SA 4.0](https://www.edrdg.org/edrdg/licence.html). Dictionaries you build from them are derivative
  works under the same license. See [NOTICE](NOTICE).
- Generated template images contain only glyph renderings and grid lines. Their glyphs come from whichever font you pass in; check that font's license before redistributing images (Noto CJK is SIL OFL 1.1).
