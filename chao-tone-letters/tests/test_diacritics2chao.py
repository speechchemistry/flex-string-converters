# -*- coding: utf-8 -*-
#
#   Tests for the Chao tone letter conversion
#
#   These exercise convert() and tone_diacritics_to_chao_letters() directly:
#   both take and return a plain string and need no FLEx project, so they run
#   on any platform.
#

import unicodedata

import pytest

from diacritics2chao import convert, tone_diacritics_to_chao_letters


# One case per row of SPEC.md's tone diacritic table, so the mapping cannot
# drift silently. Each tone diacritic is applied to the same base letter.
TONE_DIACRITIC_CASES = [
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


@pytest.mark.parametrize("diacritic, tone_letters", TONE_DIACRITIC_CASES)
def test_each_diacritic_maps_to_its_tone_letters(diacritic, tone_letters):
    assert tone_diacritics_to_chao_letters("o" + diacritic) == tone_letters


def test_spec_example():
    # The example documented in both SPEC.md and README.md
    assert tone_diacritics_to_chao_letters("nə̀jɛ᷅t") == "˨ ˨˧"


def test_precomposed_input_matches_decomposed():
    precomposed = unicodedata.normalize("NFC", "mí")
    decomposed = unicodedata.normalize("NFD", "mí")
    assert precomposed != decomposed          # guard: the two forms really differ
    assert tone_diacritics_to_chao_letters(precomposed) == tone_diacritics_to_chao_letters(decomposed) == "˦"


def test_several_diacritics_in_one_word_keep_their_order():
    # sākpò "adult" (a Plateau language): mid tone on the first vowel, low on the second
    assert tone_diacritics_to_chao_letters("sākpò") == "˧ ˨"


def test_words_are_separated_by_two_spaces():
    # A coda after the last tone would otherwise leave a three-space gap
    assert tone_diacritics_to_chao_letters("nə̀t nə̀t") == "˨  ˨"


def test_no_leading_or_trailing_whitespace():
    result = tone_diacritics_to_chao_letters("  nə̀t  ")
    assert result == "˨"


@pytest.mark.parametrize("text", ["", "cat", "   "])
def test_text_without_tone_marks_converts_to_empty_string(text):
    assert tone_diacritics_to_chao_letters(text) == ""


def test_level_tone_over_a_diphthong_is_one_collapsed_group():
    # kāī: macron on both vowels of one syllable is one group, not two
    assert tone_diacritics_to_chao_letters("kāī") == "˧"


def test_contour_spread_over_a_diphthong_is_one_group():
    # kàí: grave then acute across one syllable's two vowels
    assert tone_diacritics_to_chao_letters("kàí") == "˨˦"


def test_same_contour_on_one_vowel_matches_the_diphthong_spelling():
    # kǎi and kàí notate the same rising tone over the same syllable; this
    # pair is the point of grouping by syllable rather than by diacritic.
    assert tone_diacritics_to_chao_letters("kǎi") == "˨˦"


def test_non_adjacent_duplicate_tone_letters_do_not_collapse():
    # kǎǐ: caron on both vowels concatenates without collapsing, since no
    # adjacent pair of tone letters repeats
    assert tone_diacritics_to_chao_letters("kǎǐ") == "˨˦˨˦"


def test_syllabic_consonant_is_its_own_syllable_even_with_no_following_consonant():
    # m̩̄ā: a syllabic nasal carrying its own tone is a syllable on its own,
    # never joining the following vowel
    assert tone_diacritics_to_chao_letters("m̩̄ā") == "˧ ˧"


def test_convert_diphthong_with_level_tone():
    assert convert("kāī") == "kai ˧"


def test_tone_letters_already_in_the_input_are_not_kept():
    # A tone letter that was already in the input, not derived from a tone
    # diacritic, is ordinary text as far as this function is concerned: it
    # collapses away like any other non-diacritic character rather than
    # being kept alongside (and indistinguishable from) an extracted one.
    assert tone_diacritics_to_chao_letters("˥") == ""


# ---------------------------------------------------------------
# convert(): base text (tone diacritics stripped) plus tone letters


def test_convert_spec_example():
    assert convert("nə̀jɛ᷅t") == "nəjɛt ˨ ˨˧"


def test_convert_text_with_no_tone_diacritics_is_returned_unchanged():
    assert convert("cat") == "cat"


def test_convert_leaves_unrelated_diacritics_in_the_base_text():
    # U+0308 (diaeresis, as in ë) is not one of the 13 recognised tone diacritics
    assert convert("ë") == "ë"


def test_convert_does_not_duplicate_a_tone_letter_already_in_the_input():
    # convert()'s base text keeps a tone letter unchanged (it's not one of
    # the 13 tone diacritics base_text strips), and
    # tone_diacritics_to_chao_letters() must not also treat it as something
    # it extracted, or it would appear twice.
    assert convert("˥") == "˥"


def test_convert_empty_string():
    assert convert("") == ""
