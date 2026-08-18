# -*- coding: utf-8 -*-
#
#   Tests for the Chao tone letter conversion
#
#   These exercise convert() directly: it takes and returns a plain string and
#   needs no FLEx project, so they run on any platform.
#

import unicodedata

import pytest

from chao_tones import convert


# One case per row of SPEC.md's accent table, so the mapping cannot drift
# silently. Each combining accent is applied to the same base letter.
ACCENT_CASES = [
    ("̋", "˥"),                  # ő -> ˥
    ("́", "˦"),                  # ó -> ˦
    ("̄", "˧"),                  # ō -> ˧
    ("̀", "˨"),                  # ò -> ˨
    ("̏", "˩"),                  # ȍ -> ˩
    ("̌", "˨˦"),            # ǒ -> ˨˦
    ("̂", "˦˨"),            # ô -> ˦˨
    ("᷄", "˧˦"),            # o᷄ -> ˧˦
    ("᷅", "˨˧"),            # o᷅ -> ˨˧
    ("᷈", "˨˦˨"),      # o᷈ -> ˨˦˨
    ("᷆", "˧˨"),            # o᷆ -> ˧˨
    ("᷇", "˦˧"),            # o᷇ -> ˦˧
    ("᷉", "˦˨˦"),      # o᷉ -> ˦˨˦
]


@pytest.mark.parametrize("accent, tone_letters", ACCENT_CASES)
def test_each_accent_maps_to_its_tone_letters(accent, tone_letters):
    assert convert("o" + accent) == tone_letters


def test_spec_example():
    # The example documented in both SPEC.md and README.md
    assert convert("nə̀jɛ᷅t") == "˨ ˨˧"


def test_precomposed_input_matches_decomposed():
    precomposed = unicodedata.normalize("NFC", "ǹ")
    decomposed = unicodedata.normalize("NFD", "ǹ")
    assert precomposed != decomposed          # guard: the two forms really differ
    assert convert(precomposed) == convert(decomposed) == "˨"


def test_several_accents_in_one_word_keep_their_order():
    assert convert("ńj̀") == "˦ ˨"


def test_words_are_separated_by_two_spaces():
    # A coda after the last tone would otherwise leave a three-space gap
    assert convert("nə̀t nə̀t") == "˨  ˨"


def test_no_leading_or_trailing_whitespace():
    result = convert("  nə̀t  ")
    assert result == "˨"


@pytest.mark.parametrize("text", ["", "cat", "   "])
def test_text_without_tone_marks_converts_to_empty_string(text):
    assert convert(text) == ""


def test_tone_letters_already_in_the_input_are_kept():
    assert convert("˥") == "˥"
