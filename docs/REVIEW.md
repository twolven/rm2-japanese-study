# Adversarial review

Self-review of the first release, done by trying to break it on a real device (rM2, firmware 3.25.1.1)
and against the source data. "Fixed" items were fixed in the same pass.

## Defects found and fixed

| # | Finding | How it was found | Fix |
|---|---|---|---|
| 1 | **Homographs in arbitrary order.** Looking up かみ listed 佳味 ("delicious taste") before 紙 / 神 / 髪. | Ran KOReader's own `sdcv` on the tablet. | Index ties are now ordered by JMdict priority tags (news1/ichi1/spec/gai1, then nfNN). Common entries carry a ★. Re-checked: 紙, 神, 髪 now come first. |
| 2 | **Cluttered tags**: "noun (common) (futsuumeishi)" on every sense, repeated. | Same lookup. | Romaji glosses stripped, tags abbreviated, tag shown only when it changes between senses. Usage notes (uk, slang, archaic…) added. |
| 3 | **Full-width headwords unfindable**: JMdict stores ＣＤ, so "CD" returned nothing. | `sdcv` lookup. | NFKC aliases added to the index (+3.5k words). |
| 4 | **Tracing sheets taught the wrong shapes.** A gothic font draws さ, き, ふ, り with disconnected strokes unlike handwriting, and there was no stroke order. | Visual inspection of the rendered sheet. | Rebuilt from KanjiVG stroke vectors: stroke-by-stroke rendering with KanjiVG's own stroke-order numbers. |
| 5 | **SSH over WLAN accepted root password login** (and the stock unit passes `-B`, which allows blank passwords). The tablet password had been shared in a chat session. | Read the dropbear unit; key auth was already installed. | WLAN-only drop-in disables password auth (`dropbear -s`). Verified: key login works, password login over WLAN is refused. The USB service is untouched as a recovery path. |
| 6 | **System partition nearly full** (92%, 20 MB free); the first stroke-order sheets were ~133 KB each. | `df` on the device. | PNGs posterized to 16 gray levels (the panel's depth): ~62 KB each. 80 templates use ~5 MB; ~15.7 MB stays free. |

## Verified

- Dictionaries: real lookups through the bundled `sdcv` on the tablet (食べる, 日本語, 山 → kanji entry, はし, かみ, CD).
- Coverage: every kanji in KANJIDIC2 grades 1–6 and 8 (1,936) has a KanjiVG entry. No sheet was silently shortened.
- Install is idempotent (`add_templates.py` replaces entries by filename); templates folder reinstalled without error; xochitl restarts cleanly and logs no template errors.
- Repo scanned for IPs, hostnames, local paths and credentials before publishing: none.

## Known limitations (accepted, not fixed)

- **Not visually verified on the e-ink screen**: how KOReader renders the dictionary HTML, and how the new templates look in the notebook picker. Lookups and file loading are verified; pixels are not.
- **JMdict**: no example sentences, no pitch accent, and sense restrictions to particular spellings (`stagk`/`stagr`) are ignored, so a sense may show under a form it doesn't apply to. The ★ marks the *entry* as common, not each individual spelling.
- **KANJIDIC2 JLPT** is the pre-2010 four-level scale (labelled "old JLPT"), not N5–N1. Grade, stroke count and frequency are current.
- **Dense kanji** (10+ strokes) have crowded stroke numbers. Readable, not pretty.
- **Template picker clutter**: 79 stock + 80 added = 159 entries. Kanji grade 8 (1,110 kanji, 70 more pages) is buildable but not installed by default.
- **No handwriting recognition**: the rM2 has none for Japanese, so practice is by eye, not scored.
- **No automated tests or CI.** Checks were manual (above). Scripts were run on Windows only; they are pure Python and use `os.path`.
- **Operational risk, by design**: xovi/AppLoad/Vellum are community software; packages run as root and xovi is `LD_PRELOAD`ed into the UI process. OS auto-updates are disabled, so the tablet gets no security patches until you re-enable them. Firmware 3.25.1.1 is not the newest.
- **The device root password can't be rotated** on reMarkable firmware. It is no longer usable over WLAN; it still works over USB.
