"""Kana -> romaji (Hepburn-style, no macrons: long vowels are written as typed, e.g. とうきょう -> toukyou).

    from kana2romaji import to_romaji
    to_romaji("たべる") == "taberu"
"""
_BASE = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ゔ": "vu",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa", "っ": "",
}
_COMBO = {
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo", "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho", "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho", "ぢゃ": "ja", "ぢゅ": "ju", "ぢょ": "jo",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo", "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo", "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo", "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo", "てぃ": "ti", "でぃ": "di",
    "うぃ": "wi", "うぇ": "we", "うぉ": "wo", "ちぇ": "che", "しぇ": "she", "じぇ": "je",
    "つぁ": "tsa", "つぃ": "tsi", "つぇ": "tse", "つぉ": "tso", "ゔぁ": "va", "ゔぃ": "vi",
    "ゔぇ": "ve", "ゔぉ": "vo", "とぅ": "tu", "どぅ": "du",
}
_VOWELS = "aiueo"
# words whose final は is the topic particle, read "wa"
_OVERRIDE = {"こんにちは": "konnichiwa", "こんばんは": "konbanwa"}


def _to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def to_romaji(text):
    s = _to_hira(text)
    if s in _OVERRIDE:
        return _OVERRIDE[s]
    out, i, double = [], 0, False
    while i < len(s):
        c = s[i]
        if c == "っ":
            double = True; i += 1; continue
        if c == "ー":  # long vowel mark: repeat the last vowel
            last = next((ch for ch in reversed("".join(out)) if ch in _VOWELS), "")
            out.append(last); i += 1; continue
        pair = s[i:i + 2]
        if pair in _COMBO:
            r, i = _COMBO[pair], i + 2
        elif c in _BASE:
            r, i = _BASE[c], i + 1
        else:  # not kana (kanji, latin, punctuation): pass through
            out.append(c); double = False; i += 1; continue
        if c == "ん" and i < len(s) and (s[i] in "あいうえおやゆよ" or _to_hira(s[i]) in "あいうえおやゆよ"):
            r = "n'"
        if double and r:
            r = ("t" + r) if r.startswith("ch") else (r[0] + r)
            double = False
        out.append(r)
    return "".join(out)


if __name__ == "__main__":
    cases = {"たべる": "taberu", "しゅうまつ": "shuumatsu", "コーヒー": "koohii", "ざっし": "zasshi",
             "きょう": "kyou", "しんいち": "shin'ichi", "がっこう": "gakkou", "ありがとう": "arigatou",
             "こんにちは": "konnichiwa", "まっちゃ": "matcha", "ちゅうごく": "chuugoku", "パーティー": "paatii",
             "でんわ": "denwa", "シャツ": "shatsu", "ほん": "hon", "おはよう": "ohayou", "ふぁいる": "fairu"}
    bad = {k: (to_romaji(k), v) for k, v in cases.items() if to_romaji(k) != v}
    print("FAIL", bad) if bad else print("all %d ok" % len(cases))
