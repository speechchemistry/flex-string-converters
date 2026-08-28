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

import chao2diacritics
from diacritics2chao import (
    convert,
    tone_diacritics_to_attached,
    tone_diacritics_to_chao_letters,
)


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


# ---------------------------------------------------------------
# Attached output: the tone letters written after the syllable they mark,
# rather than gathered into a trailing section. Spacing then carries no
# meaning, so a pipeline or spreadsheet cannot destroy the reading.

NFC = lambda text: unicodedata.normalize("NFC", text)


def test_the_trailing_section_stays_the_default():
    assert convert(NFC("n\u0259\u0300j\u025b\u1dc5t")) == "n\u0259j\u025bt \u02e8 \u02e8\u02e7"


@pytest.mark.parametrize("diacritics,attached", [
    ("n\u0259\u0300j\u025b\u1dc5t", "n\u0259\u02e8j\u025b\u02e8\u02e7t"),
    ("m\u00e1 t\u00ee",               "ma\u02e6 ti\u02e6\u02e8"),
    ("\u01d2l\u014d",                 "o\u02e8\u02e6lo\u02e7"),
    ("s\u0101kp\u00f2",               "sa\u02e7kpo\u02e8"),
])
def test_attached_output(diacritics, attached):
    assert convert(NFC(diacritics), attached=True) == attached


def test_attached_output_leaves_a_toneless_word_alone():
    assert convert("cat", attached=True) == "cat"
    assert convert("ma\u0301 ti", attached=True) == "ma\u02e6 ti"


def test_tone_diacritics_to_attached_matches_convert():
    for text in ["n\u0259\u0300j\u025b\u1dc5t", "m\u00e1 t\u00ee", "cat"]:
        assert tone_diacritics_to_attached(NFC(text)) == convert(NFC(text), attached=True)


@pytest.mark.parametrize("word", [
    "n\u0259\u0300j\u025b\u1dc5t", "\u01d2l\u014d", "s\u0101kp\u00f2",
    "x\u025b\u0303\u0300\u027e\u012b", "kw\u014d\u02d0", "m\u00e1 t\u00ee",
])
def test_attached_output_round_trips_back_through_chao2diacritics(word):
    # The whole point of the attached form: it survives being read back.
    assert chao2diacritics.convert(convert(NFC(word), attached=True)) == NFC(word)


def test_attached_output_survives_whitespace_mangling():
    # Collapsing runs of spaces destroys the trailing section's meaning but
    # cannot touch the attached form, which is why it is the safer thing to
    # store in a spreadsheet column or a FLEx field.
    import regex
    attached = convert(NFC("bjo\u1dc6 s\u0101d\u00f9"), attached=True)
    assert chao2diacritics.convert(regex.sub(r" {2,}", " ", attached)) == NFC("bjo\u1dc6 s\u0101d\u00f9")
