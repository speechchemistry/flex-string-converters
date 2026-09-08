# -*- coding: utf-8 -*-
#
#   Unit tests for cv-patterns/converters/phonemes2cv.py
#
#   Each parametrized case is one row of the Worked Examples table in
#   cv-patterns/SPEC.md (itself carried over from plans/old/cv-pattern-from-phonemes.md),
#   covering every rule in isolation. A few rules need a second example beyond
#   that table, added as their own test below.
#

import unicodedata

import pytest

from phonemes2cv import Convert

WORKED_EXAMPLES = [
    ("nə̀jɛt", "CVCVC"),
    ("nəjɛt ˨ ˨˧", "CVCVC"),
    ("tʷa", "CV"),
    ("kʰat", "CVC"),
    ("ᵐba", "CV"),
    ("ʰta", "CV"),
    ("t͡ʃa", "CV"),
    ("tʃa", "CCV"),
    ("ŋǃa", "CV"),
    ("kn̩", "CV"),
    ("aɪ", "VV"),
    ("a͡ɪ", "V"),
    ("ˈtata", "CVCV"),
    ("ab ec", "VC VC"),
    ("7a", "?V"),
]


@pytest.mark.parametrize("input_string,expected", WORKED_EXAMPLES)
def test_worked_example(input_string, expected):
    assert Convert(input_string) == expected


def test_tie_bar_undertie():
    # The tie-bar rule recognises both codepoints: U+0361 (the worked examples
    # above use it via t͡ʃa) and U+035C, the less common "undertie".
    assert Convert("t͜s") == "C"


def test_syllabic_promotion_unlisted():
    # BIPA lists 25 syllabic consonants directly (kn̩ above is one); a
    # syllabic mark on a consonant BIPA doesn't list has to work the same way,
    # via the SYL sentinel's generic post-pass promotion.
    assert Convert("bd̩") == "CV"


def test_nfc_and_nfd_input_give_the_same_pattern():
    # The converter must NFD-normalise its input itself -- verified directly
    # against segments.Tokenizer, which normalises only its output form, not
    # the word it matches against the profile. A precomposed (NFC) input must
    # therefore give the same result as its NFD form. Schwa-plus-grave (used
    # in the worked examples above) has no precomposed form to test this
    # with, but nasalised a (ã) does.
    nfd_input = "t" + unicodedata.normalize("NFD", "ã") + "n"
    nfc_input = "t" + unicodedata.normalize("NFC", "ã") + "n"
    assert nfc_input != nfd_input
    assert Convert(nfc_input) == Convert(nfd_input) == "CVC"
