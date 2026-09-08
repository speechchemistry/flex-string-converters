#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Generator for cv-patterns/converters/cv_profile.tsv
#
#   Downloads the six BIPA transcription-system tables from CLTS's cldf-clts/clts
#   repository at the pinned tag below, reconciles every row into exactly one of
#   the buckets described in plans/old/cv-pattern-from-phonemes.md, and writes the
#   result as a segments orthography profile (a Grapheme column plus a CV column).
#   Kept outside converters/ so the FlexTools scanner never sees it, and re-run it
#   whenever the pinned CLTS tag is bumped -- see cv-patterns/SPEC.md.
#
#   Tim Kempton
#   September 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency,
#   and is not itself a converter -- see AGENTS.md's Converter Conventions)
#

import csv
import io
import unicodedata
import urllib.request
from pathlib import Path

CLTS_TAG = "v2.3.0"
CLTS_DOI = "10.5281/zenodo.3515744"
BASE_URL = (
    f"https://raw.githubusercontent.com/cldf-clts/clts/{CLTS_TAG}"
    "/pkg/transcriptionsystems/bipa/"
)
TABLE_NAMES = ("consonants", "vowels", "tones", "diacritics", "markers", "normalize")
EXPECTED_ROW_COUNTS = {
    "consonants": 729,
    "vowels": 326,
    "tones": 132,
    "diacritics": 115,
    "markers": 6,
    "normalize": 46,
}

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "converters" / "cv_profile.tsv"

# A listed BIPA consonant grapheme is syllabic (a syllabic consonant is a
# vowel for CV purposes) when its own EXTRA column says so -- BIPA marks this
# with "syllabicity:syllabic" in EXTRA, not only with a combining mark: most
# of the 25 such graphemes carry the combining vertical line below/above
# (U+0329/U+030D, e.g. n̩), but 3 are Indological dot-below transliterations
# of the same alias (ḷ, ṇ, ṃ for l̩, n̩, m̩) with no such mark at all. Checking
# the mark alone silently missed those three on a first pass -- see
# cv-patterns/SPEC.md. See the SYL sentinel below for the unlisted case.
SYLLABICITY_EXTRA = "syllabicity:syllabic"

# Values for the profile's CV column, beyond plain "C" and "V" -- see
# cv-patterns/SPEC.md's "The profile's three special values".
NULL = "NULL"
SYL = "SYL"
TIE = "TIE"

# normalize.tsv rows that the generic resolution below (look up, or tokenise
# and reduce, the TARGET spelling) gets wrong, because the row's own meaning
# isn't "this SOURCE spells the same sequence of phones as TARGET":
#   - ǧ/ǯ/ǰ are each one *character* standing in for the affricate dʒ, which
#     is itself spelled with two characters and (per the tie-bar decision)
#     would resolve to two C's. A single character is one phone.
#   - "|" is a normalize.tsv self-alias (SOURCE and TARGET are the identical
#     codepoint) for a prosodic/foot-boundary mark. It isn't one of BIPA's own
#     6 markers.tsv rows, and nothing else in the source tables defines its
#     class, but it is functionally the same kind of thing they are: a
#     boundary mark that contributes nothing to a CV pattern.
NORMALIZE_OVERRIDES = {
    "ǧ": "C",
    "ǯ": "C",
    "ǰ": "C",
    "|": NULL,
}

# BIPA's own diacritics.tsv covers 7 of the 13 IPA tone diacritics this
# repository already recognises (chao-tone-letters/converters/diacritics2chao.py's
# TONE_DIACRITIC_TO_CHAO_LETTERS) -- the plain accent marks -- but not the 6
# combining contour marks (U+1DC4-U+1DC9), confirmed missing from both
# diacritics.tsv and tones.tsv. Left uncovered, real tone-marked data (found
# via the words.txt approval fixture, itself real Zhire data) would turn a
# tone mark this repository already treats as meaningful into an unrecognised
# "?", and the "so the two projects compose" guarantee in cv-patterns/SPEC.md
# would only hold for diacritics2chao.py's *output* (bare Chao tone letters),
# not for tone-marked input on its way in. See cv-patterns/SPEC.md's
# reconciliation for why these 6 are listed here as a named exception rather
# than folded into the BIPA-derived count above.
EXTRA_TONE_DIACRITICS = "᷄᷅᷆᷇᷈᷉"

# Two standard IPA diacritics confirmed missing from both diacritics.tsv and
# tones.tsv: dental (U+032A, ◌̪) and linguolabial (U+0347, ◌͇). Found via the
# PHOIBLE coverage test (cv-patterns/tests/test_phonemes2cv_source.py), which
# is the independent net over BIPA precisely so a source gap like this one
# surfaces on real attested segments rather than staying invisible -- see
# cv-patterns/SPEC.md. Unlike EXTRA_TONE_DIACRITICS above, nothing else in
# this repository already relies on these; they're added because they are
# themselves ordinary IPA, not because of any other converter's contract.
EXTRA_DIACRITICS = "̪͇"


def fetch_tsv(name):
    with urllib.request.urlopen(BASE_URL + name + ".tsv") as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def base_letter_count(grapheme):
    # Counts codepoints that are letters proper (Ll/Lu/Lo) after NFD
    # decomposition, which is what distinguishes a single phone carrying
    # secondary-articulation modifier letters (Lm, e.g. kʷ) or combining
    # diacritics (Mn) from a sequence of more than one base consonant letter
    # (e.g. kp, ŋǃ). Verified against BIPA's own MANNER column: filtering on
    # this count plus "MANNER ends in click" reproduces the 532/48/149 split
    # this file's reconciliation states -- see cv-patterns/SPEC.md.
    nfd = unicodedata.normalize("NFD", grapheme)
    return sum(1 for ch in nfd if unicodedata.category(ch) in ("Ll", "Lu", "Lo"))


class Reconciler:
    def __init__(self):
        self.profile = {}  # NFD grapheme -> CV value

    def add(self, grapheme, value):
        grapheme = unicodedata.normalize("NFD", grapheme.strip())
        if not grapheme:
            raise ValueError("empty grapheme after stripping")
        existing = self.profile.get(grapheme)
        if existing is not None and existing != value:
            raise AssertionError(
                f"conflicting CV value for {grapheme!r}: {existing!r} vs {value!r}"
            )
        self.profile[grapheme] = value

    def resolve(self, target):
        # Tokenises `target` by longest match against the profile built so
        # far, then reduces it with the same TIE/SYL/NULL rules the converter's
        # own post-pass applies, so a normalize.tsv alias gets the class its
        # target spelling would actually produce. Used only for the ~40 of 46
        # normalize.tsv rows not covered by NORMALIZE_OVERRIDES or the
        # tie-bar/diacritic-alias special cases below.
        nfd = unicodedata.normalize("NFD", target)
        lengths = sorted({len(g) for g in self.profile}, reverse=True)
        tokens = []
        i = 0
        while i < len(nfd):
            for length in lengths:
                candidate = nfd[i : i + length]
                if candidate in self.profile:
                    tokens.append(self.profile[candidate])
                    i += length
                    break
            else:
                raise AssertionError(
                    f"cannot resolve normalize.tsv target {target!r}: "
                    f"no match at position {i} ({nfd[i]!r})"
                )
        reduced = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == NULL:
                i += 1
                continue
            if token == TIE:
                if reduced:
                    reduced.pop()
                i += 1
                while i < len(tokens) and tokens[i] == NULL:
                    i += 1
                if i < len(tokens):
                    reduced.append(tokens[i])
                    i += 1
                continue
            if token == SYL:
                if reduced:
                    reduced[-1] = "V"
                i += 1
                continue
            reduced.append(token)
            i += 1
        if not reduced:
            return NULL
        if len(reduced) == 1 and reduced[0] in ("C", "V"):
            return reduced[0]
        raise AssertionError(
            f"normalize.tsv target {target!r} resolved to {reduced!r}, "
            "not a single C/V/NULL -- add it to NORMALIZE_OVERRIDES"
        )


def build_profile():
    tables = {name: fetch_tsv(name) for name in TABLE_NAMES}
    for name, rows in tables.items():
        expected = EXPECTED_ROW_COUNTS[name]
        if len(rows) != expected:
            raise AssertionError(
                f"{name}.tsv has {len(rows)} rows, expected {expected} -- "
                f"BIPA {CLTS_TAG} has changed; re-derive the reconciliation "
                "in cv-patterns/SPEC.md before updating these counts"
            )

    r = Reconciler()

    # --- Consonants: 729 rows in three buckets (see cv-patterns/SPEC.md) ---
    single_base, multi_click, multi_nonclick = [], [], []
    for row in tables["consonants"]:
        grapheme = row["GRAPHEME"]
        is_click = row["MANNER"].endswith("click")
        if base_letter_count(grapheme) <= 1:
            single_base.append(row)
        elif is_click:
            multi_click.append(row)
        else:
            multi_nonclick.append(row)
    assert len(single_base) == 532, f"expected 532 single-base rows, got {len(single_base)}"
    assert len(multi_click) == 48, f"expected 48 multi-base click rows, got {len(multi_click)}"
    assert len(multi_nonclick) == 149, (
        f"expected 149 excluded tieless non-click multi-base rows, got {len(multi_nonclick)}"
    )

    syllabic_count = 0
    for row in single_base + multi_click:
        grapheme = row["GRAPHEME"]
        if SYLLABICITY_EXTRA in row["EXTRA"]:
            r.add(grapheme, "V")
            syllabic_count += 1
        else:
            r.add(grapheme, "C")
    assert syllabic_count == 25, (
        f"expected 25 listed syllabic consonants, got {syllabic_count}"
    )
    # multi_nonclick (149 rows) is deliberately excluded: it segments into its
    # parts instead, per the tie-bar decision.

    # --- Vowels: 326 rows, all V; none has more than one base letter ---
    for row in tables["vowels"]:
        grapheme = row["GRAPHEME"]
        assert base_letter_count(grapheme) <= 1, (
            f"vowel grapheme {grapheme!r} has more than one base letter"
        )
        r.add(grapheme, "V")

    # --- Diacritics: 115 rows, NULL except the 4 syllabicity rows ---
    syllabicity_rows = 0
    for row in tables["diacritics"]:
        grapheme = row["GRAPHEME"].replace("◌", "")  # strip the ◌ placeholder
        if row["FEATURE"] == "syllabicity":
            syllabicity_rows += 1
            r.add(grapheme, SYL if row["VALUE"] == "syllabic" else NULL)
        else:
            r.add(grapheme, NULL)
    assert syllabicity_rows == 4, f"expected 4 syllabicity rows, got {syllabicity_rows}"

    # --- Tones: 132 rows, NULL ---
    for row in tables["tones"]:
        r.add(row["GRAPHEME"], NULL)

    # --- Markers: 6 rows, NULL ---
    for row in tables["markers"]:
        r.add(row["GRAPHEME"], NULL)

    # --- normalize.tsv: 46 rows, not optional (see cv-patterns/SPEC.md) ---
    tie_rows = 0
    for row in tables["normalize"]:
        source, target = row["SOURCE"], row["TARGET"]
        source_stripped = source.replace("◌", "")
        target_stripped = target.replace("◌", "")
        if source_stripped in ("͡", "͜") and not target_stripped:
            # The 2 tie-bar rows (◌͡◌, ◌͜◌) become
            # standalone TIE rows.
            r.add(source_stripped, TIE)
            tie_rows += 1
        elif "◌" in source:
            # A diacritic-to-diacritic alias (e.g. ◌̱ -> ◌̠):
            # resolve via the already-known class of the stripped target mark.
            r.add(source_stripped, r.profile[unicodedata.normalize("NFD", target_stripped)])
        elif source in NORMALIZE_OVERRIDES:
            r.add(source, NORMALIZE_OVERRIDES[source])
        else:
            r.add(source, r.resolve(target))
    assert tie_rows == 2, f"expected 2 tie-bar rows in normalize.tsv, got {tie_rows}"

    # --- The 6 extra tone diacritics BIPA v2.3.0 doesn't list (see above) ---
    for mark in EXTRA_TONE_DIACRITICS:
        r.add(mark, NULL)

    # --- The 2 extra IPA diacritics BIPA v2.3.0 doesn't list (see above) ---
    for mark in EXTRA_DIACRITICS:
        r.add(mark, NULL)

    return r.profile


def write_profile(profile):
    lines = [
        "# cv-patterns/converters/cv_profile.tsv",
        "#",
        "# A segments (https://pypi.org/project/segments/) orthography profile mapping",
        "# IPA/BIPA graphemes to a CV-pattern class. Generated by",
        "# cv-patterns/tools/build_cv_profile.py -- do not hand-edit; re-run the",
        "# generator instead, and see cv-patterns/SPEC.md for the reconciliation.",
        "#",
        "# Source: BIPA (List, Anderson, Tresoldi, Rzymski & Forkel), the broad IPA",
        f"# transcription system from CLTS (cldf-clts/clts), tag {CLTS_TAG},",
        f"# DOI {CLTS_DOI}. Licence: CC-BY-4.0.",
        "#",
        "# Changes made from the source: consonant rows filtered to three buckets",
        "# (single-base and multi-base-click kept as C, tieless non-click digraphs",
        "# excluded); a CV column derived from the source's own MANNER/TYPE/FEATURE",
        "# columns and table membership; 6 combining contour tone diacritics",
        "# (U+1DC4-U+1DC9) added beyond BIPA's own tables, from this repository's",
        "# own chao-tone-letters/converters/diacritics2chao.py; and 2 further IPA",
        "# diacritics (dental U+032A, linguolabial U+0347) added after PHOIBLE's",
        "# segment inventory showed them missing from BIPA v2.3.0 entirely. See",
        "# cv-patterns/SPEC.md for the full reconciliation this generator implements.",
        "#",
        "Grapheme\tCV",
    ]
    for grapheme in sorted(profile):
        lines.append(f"{grapheme}\t{profile[grapheme]}")
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    profile = build_profile()
    write_profile(profile)
    print(f"Wrote {len(profile)} graphemes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
