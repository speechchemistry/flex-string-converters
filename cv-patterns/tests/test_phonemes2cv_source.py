# -*- coding: utf-8 -*-
#
#   Source-derived checks for phonemes2cv.py
#
#   The bipa_graphemes fixture (fixtures/phonemes2cv/{inputs,approved}/bipa_graphemes.*)
#   is exercised through the ordinary CLI approval test in
#   test_phonemes2cv_cli.py already, since it's just another *.txt pair under
#   inputs/ and approved/ -- see cv-patterns/tools/build_bipa_graphemes_fixture.py
#   for how it was derived (from BIPA's own tables, never by promoting
#   Convert()'s output) and cv-patterns/SPEC.md for what it proves.
#
#   This file holds the other source-derived check: PHOIBLE's segment
#   inventory is the independent net (see cv-patterns/SPEC.md's "Why BIPA is
#   the source, and what PHOIBLE is for"), used here as an assertion rather
#   than an approval file, entirely offline against the checked-in
#   phoible_segments.txt fixture.
#

from pathlib import Path

from phonemes2cv import Convert

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "phonemes2cv"

# The 23 of 2162 PHOIBLE segments that produce a "?", reviewed and accepted as
# PHOIBLE-specific or otherwise non-standard notation rather than a BIPA
# coverage gap -- see cv-patterns/SPEC.md's reconciliation. Two similar
# findings from this same coverage test *were* real BIPA gaps and are already
# fixed in cv_profile.tsv (dental U+032A, linguolabial U+0347, plus 6 tone
# contour marks found via real-word testing): this list is what's left after
# those fixes. Named explicitly, rather than just asserting a count, so that a
# *different* segment producing "?" -- a real regression, or a genuinely new
# gap -- still fails this test instead of silently fitting under a number.
KNOWN_UNRECOGNIZED_SEGMENTS = frozenset({
    # Double-click "‼": PHOIBLE's own notation for a click type BIPA spells
    # differently, not standard IPA.
    "k‼", "k‼x", "k‼xʼ", "k‼ʰ", "k‼ʰʼ", "k‼ʼ",
    "ŋ‼", "ŋ‼ʰ",
    "ɡ‼", "ɡ‼x", "ɡ‼xʼ", "ɡ‼ʱ",
    # Raised capital E (ᴱ): an idiosyncratic PHOIBLE marking, not general IPA.
    "aᴱ", "oᴱ", "uᴱ",
    # Small-capital D (ᴅ): likewise idiosyncratic, not general IPA.
    "ᴅ", "ᴅ̪", "ᴅ̪̰",
    # Asterisk-prefixed segments: PHOIBLE's own marker (e.g. for a
    # reconstructed segment), not a transcribed phone at all.
    "*R", "*Rʲ", "*R̪", "*R̪̥", "*R̪̰",
})


def test_no_phoible_segment_produces_an_unexpected_unrecognized_symbol():
    segments = (
        FIXTURES_DIR.joinpath("phoible_segments.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert len(segments) == 2162

    # A tieless affricate or other bare digraph PHOIBLE lists (e.g. "ts",
    # "tʃ") is *expected* to come out CC, per the tie-bar decision in
    # cv-patterns/SPEC.md -- that's a real answer, not a "?". This assertion
    # is only about symbols the converter doesn't recognise at all.
    unrecognized = {segment for segment in segments if "?" in Convert(segment)}

    assert unrecognized == KNOWN_UNRECOGNIZED_SEGMENTS, (
        f"unexpected: {sorted(unrecognized - KNOWN_UNRECOGNIZED_SEGMENTS)}; "
        f"no longer failing (update the allow-list): "
        f"{sorted(KNOWN_UNRECOGNIZED_SEGMENTS - unrecognized)}"
    )
