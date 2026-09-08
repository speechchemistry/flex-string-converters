#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   One-time generator for the bipa_graphemes source-derived fixture
#
#   Writes cv-patterns/tests/fixtures/phonemes2cv/inputs/bipa_graphemes.txt and
#   its approved counterpart directly from a fresh read of BIPA's own
#   consonants.tsv, vowels.tsv and tones.tsv -- not by promoting Convert()'s
#   own output, which would make the converter its own judge. See
#   cv-patterns/SPEC.md and the checking-a-converter-against-its-source skill.
#
#   Run once by hand whenever the pinned CLTS tag changes; not part of the
#   pytest suite itself, and not a converter -- see AGENTS.md's Converter
#   Conventions.
#
#   Tim Kempton
#   September 2026
#
#   Platforms: any Python 3
#

from pathlib import Path

from build_cv_profile import (
    EXPECTED_ROW_COUNTS,
    SYLLABICITY_EXTRA,
    base_letter_count,
    fetch_tsv,
)

FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "phonemes2cv"
)


def main():
    lines = []  # (grapheme, expected CV pattern)

    consonants = fetch_tsv("consonants")
    assert len(consonants) == EXPECTED_ROW_COUNTS["consonants"]
    for row in consonants:
        grapheme = row["GRAPHEME"].strip()
        is_click = row["MANNER"].endswith("click")
        if base_letter_count(grapheme) > 1 and not is_click:
            continue  # excluded tieless non-click digraph -- not in the profile
        expected = "V" if SYLLABICITY_EXTRA in row["EXTRA"] else "C"
        lines.append((grapheme, expected))

    vowels = fetch_tsv("vowels")
    assert len(vowels) == EXPECTED_ROW_COUNTS["vowels"]
    for row in vowels:
        lines.append((row["GRAPHEME"].strip(), "V"))

    tones = fetch_tsv("tones")
    assert len(tones) == EXPECTED_ROW_COUNTS["tones"]
    for row in tones:
        lines.append((row["GRAPHEME"].strip(), ""))

    inputs_path = FIXTURES_DIR / "inputs" / "bipa_graphemes.txt"
    approved_path = FIXTURES_DIR / "approved" / "bipa_graphemes.approved.txt"
    inputs_path.write_text(
        "\n".join(grapheme for grapheme, _ in lines) + "\n", encoding="utf-8"
    )
    approved_path.write_text(
        "\n".join(expected for _, expected in lines) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(lines)} rows to {inputs_path} and {approved_path}")


if __name__ == "__main__":
    main()
