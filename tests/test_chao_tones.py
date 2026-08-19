# -*- coding: utf-8 -*-
#
#   Tests for the Chao tone letter conversion
#
#   These exercise convert() and extract_chao_letters() directly: both take
#   and return a plain string and need no FLEx project, so they run on any
#   platform.
#

import unicodedata

import pytest

from chao_tones import convert, extract_chao_letters


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
    assert extract_chao_letters("o" + accent) == tone_letters


def test_spec_example():
    # The example documented in both SPEC.md and README.md
    assert extract_chao_letters("nə̀jɛ᷅t") == "˨ ˨˧"


def test_precomposed_input_matches_decomposed():
    precomposed = unicodedata.normalize("NFC", "ǹ")
    decomposed = unicodedata.normalize("NFD", "ǹ")
    assert precomposed != decomposed          # guard: the two forms really differ
    assert extract_chao_letters(precomposed) == extract_chao_letters(decomposed) == "˨"


def test_several_accents_in_one_word_keep_their_order():
    assert extract_chao_letters("ńj̀") == "˦ ˨"


def test_words_are_separated_by_two_spaces():
    # A coda after the last tone would otherwise leave a three-space gap
    assert extract_chao_letters("nə̀t nə̀t") == "˨  ˨"


def test_no_leading_or_trailing_whitespace():
    result = extract_chao_letters("  nə̀t  ")
    assert result == "˨"


@pytest.mark.parametrize("text", ["", "cat", "   "])
def test_text_without_tone_marks_converts_to_empty_string(text):
    assert extract_chao_letters(text) == ""


def test_tone_letters_already_in_the_input_are_kept():
    assert extract_chao_letters("˥") == "˥"


# ---------------------------------------------------------------
# convert(): base text (tone accents stripped) plus tone letters


def test_convert_spec_example():
    assert convert("nə̀jɛ᷅t") == "nəjɛt ˨ ˨˧"


def test_convert_text_with_no_tone_accents_is_returned_unchanged():
    assert convert("cat") == "cat"


def test_convert_leaves_unrelated_diacritics_in_the_base_text():
    # U+0308 (diaeresis, as in ë) is not one of the 13 recognised tone accents
    assert convert("ë") == "ë"


def test_convert_empty_string():
    assert convert("") == ""
