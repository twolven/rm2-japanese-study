# reMarkable 2 Japanese study kit

Tools for studying Japanese on a reMarkable 2 running [xovi](https://github.com/asivery/xovi) +
[AppLoad](https://github.com/asivery/rm-appload) + [KOReader](https://github.com/koreader/koreader):

- **Dictionaries for KOReader tap-to-lookup** — build StarDict files from the official EDRDG data
  - `build_jmdict_stardict.py` — JMdict (words, ~219k entries; common words first, ★-marked; readings shown with romaji)
  - `build_kanjidic_stardict.py` — KANJIDIC2 (single kanji: on/kun readings with romaji, meanings, strokes, grade, JLPT)
- **Notebook templates** (1404×1872 grayscale PNG, the rM2 resolution)
  - kana practice grid (large squares, dashed centre guides)
  - genkō yōshi manuscript paper (20×20 with centre gutter)
  - stroke-order tracing sheets: hiragana, katakana, and kanji by school grade (model with stroke numbers → faint trace → blank), each model labelled with its romaji (kana) or English meaning (kanji) — built for complete beginners
- **Setup notes** for the xovi / Vellum / KOReader stack on firmware 3.25.x — [docs/SETUP.md](docs/SETUP.md)

Pre-rendered templates (kana, voiced kana, kanji grades 1–6) are in [`templates/`](templates/).
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
Romaji is written as typed, without macrons (とうきょう → toukyou); `scripts/kana2romaji.py` is the shared converter (run it to execute its self-test).

## Build templates

Stroke shapes and stroke order come from [KanjiVG](https://kanjivg.tagaini.net) (CC BY-SA 3.0).
Download the **`kanjivg-*-main.zip`** asset from the [latest release](https://github.com/KanjiVG/kanjivg/releases/latest)
(the combined `.xml.gz` has no stroke-number positions). `--font` is only used for the small stroke numbers and labels; use a font with Latin letters (e.g. Noto Sans CJK JP).

```sh
python scripts/make_practice_grids.py templates/                       # kana grid + genkō yōshi
K="--kanjivg kanjivg-main.zip --font NotoSansCJKjp-Regular.otf --out templates --manifest templates/manifest.json"
python scripts/make_trace_sheets.py $K --set hiragana
python scripts/make_trace_sheets.py $K --set katakana                  # also: hiragana-voiced, katakana-voiced
python scripts/make_trace_sheets.py $K --set kanji --grade 2 --kanjidic kanjidic2.xml.gz   # grades 1-6, 8
```

Each page: two characters per row, each as *[model with stroke-order numbers] [faint trace] [blank]*.
Kanji are ordered by stroke count within a grade. Pages are posterized to 16 gray levels (the rM2 panel depth), ~60 KB each.
Grade 8 (the remaining jōyō kanji) is 70 pages — buildable, but left out of the pre-rendered set to keep the template picker usable.

## Install templates on the tablet

```sh
scp templates/*.png root@<tablet>:/usr/share/remarkable/templates/
scp root@<tablet>:/usr/share/remarkable/templates/templates.json templates.json.bak   # keep a backup
python scripts/add_templates.py templates.json.bak templates/manifest.json templates.json
scp templates.json root@<tablet>:/usr/share/remarkable/templates/templates.json
ssh root@<tablet> systemctl restart xochitl
```

`add_templates.py` is idempotent. A firmware update replaces the system partition, so re-run the install afterwards.
Generating with `--manifest` registers each page in `templates/manifest.json`, so any grade you build is picked up by `add_templates.py`.

## Status

Built and installed on an rM2 running firmware 3.25.1.1. Dictionaries were verified with real lookups through KOReader's bundled `sdcv`;
see [docs/REVIEW.md](docs/REVIEW.md) for the adversarial review (defects found, fixes, and known limitations).
Use at your own risk — editing the templates folder and running xovi are unsupported by reMarkable.

## Licenses and data attribution

- Code in this repository: MIT (see [LICENSE](LICENSE)).
- JMdict and KANJIDIC2 are © the Electronic Dictionary Research and Development Group, used under
  [CC BY-SA 4.0](https://www.edrdg.org/edrdg/licence.html). Dictionaries you build from them are derivative
  works under the same license. See [NOTICE](NOTICE).
- Stroke templates in `templates/` are derived from KanjiVG and are therefore under **CC BY-SA 3.0** (attribution: KanjiVG, https://kanjivg.tagaini.net). The grid templates contain only lines.
