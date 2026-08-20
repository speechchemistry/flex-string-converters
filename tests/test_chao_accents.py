# -*- coding: utf-8 -*-
#
#   Tests for the accent-notation-from-Chao-tone-letters conversion
#
#   These exercise convert() and apply_chao_letters() directly: both take
#   and return a plain string and need no FLEx project, so they run on any
#   platform.
#

import unicodedata

import pytest

import chao_tones
from chao_accents import (
    TONE_LETTERS_TO_ACCENT,
    TONE_BEARING_VOWELS,
    SYLLABIC_MARKS,
    apply_chao_letters,
    convert,
)


# ---------------------------------------------------------------
# Table guards: this file's copies must never drift from chao_tones.py's.


def test_tone_letters_to_accent_is_the_exact_inverse_of_accent_to_tone_letters():
    accent_to_tone_letters = chao_tones.ACCENT_TO_TONE_LETTERS
    assert len(TONE_LETTERS_TO_ACCENT) == len(accent_to_tone_letters) == 13
    inverse = {
        tone_letters: accent
        for accent, tone_letters in accent_to_tone_letters.items()
    }
    assert TONE_LETTERS_TO_ACCENT == inverse


def test_tone_bearing_vowels_matches_chao_tones():
    assert TONE_BEARING_VOWELS == chao_tones.TONE_BEARING_VOWELS


def test_syllabic_marks_matches_chao_tones():
    assert SYLLABIC_MARKS == chao_tones.SYLLABIC_MARKS


# ---------------------------------------------------------------
# One case per accent row, parametrized off the reverse table.


@pytest.mark.parametrize("tone_letters, expected", [
    ("˥", "ő"), ("˦", "ó"), ("˧", "ō"), ("˨", "ò"), ("˩", "ȍ"),
    ("˨˦", "ǒ"), ("˦˨", "ô"), ("˧˦", "o᷄"), ("˨˧", "o᷅"),
    ("˨˦˨", "o᷈"), ("˧˨", "o᷆"), ("˦˧", "o᷇"), ("˦˨˦", "o᷉"),
])
def test_apply_chao_letters_one_case_per_accent_row(tone_letters, expected):
    assert apply_chao_letters("o", tone_letters) == unicodedata.normalize("NFC", expected)


# ---------------------------------------------------------------
# convert()


def test_convert_spec_example():
    assert convert("nəjɛt ˨ ˨˧") == unicodedata.normalize("NFC", "nə̀jɛ᷅t")


def test_convert_output_is_nfc():
    decomposed = unicodedata.normalize("NFD", "mí")
    precomposed = unicodedata.normalize("NFC", "mí")
    assert decomposed != precomposed          # guard: the two forms really differ
    assert convert("mi ˦") == precomposed


def test_syllabic_consonant_carries_its_own_tone():
    assert convert("m̩ ˧") == unicodedata.normalize("NFC", "m̩̄")


def test_plain_consonant_cannot_carry_a_tone():
    assert convert("n ˧") == "n ˧"


def test_length_mark_keeps_the_accent_on_the_vowel():
    assert convert("oː ˧") == unicodedata.normalize("NFC", "ōː")


def test_existing_diacritic_is_stacked_under_not_replaced():
    assert convert("ɛ̃ ˨") == unicodedata.normalize("NFC", "ɛ̃̀")


def test_level_tone_over_a_diphthong_repeats_on_both_vowels():
    assert convert("kai ˧") == unicodedata.normalize("NFC", "kāī")


def test_contour_over_a_diphthong_distributes_one_letter_per_vowel():
    assert convert("kai ˨˦") == unicodedata.normalize("NFC", "kàí")


def test_same_contour_on_one_vowel():
    assert convert("ka ˨˦") == unicodedata.normalize("NFC", "kǎ")


def test_words_are_separated_by_the_two_space_word_gap():
    assert convert("nət nət ˨  ˨") == unicodedata.normalize("NFC", "nə̀t nə̀t")


@pytest.mark.parametrize("text", ["", "cat", "cat   dog", "˥"])
def test_passthrough(text):
    assert convert(text) == text


@pytest.mark.parametrize("text", [
    "cat ˨ ˧ ˦",   # more groups than units
    "nət nət ˨",   # a toneless word leaves the group count short of the word count
    "o ˥˩",        # a contour with no accent among the 13
    "ka ˨˩",       # a contour with no accent among the 13
])
def test_mismatch_returns_the_input_unchanged(text):
    assert convert(text) == text


# ---------------------------------------------------------------
# Round trip: chao_tones.convert() followed by chao_accents.convert()
# returns the original word, for words where the forward conversion loses
# no information. A diphthong whose accent placement is ambiguous on the
# way back (e.g. kǎi, whose tone letters are indistinguishable from kàí's)
# is a documented exception and deliberately left out -- see this
# converter's SPEC.md entry.

ROUND_TRIP_WORDS = [
    "nə̀jɛ᷅t",
    "sākpò",
    "nə̀t",
    "nə̀t nə̀t",
    "mí",
    "kāī",
    "kàí",
    "m̩̄ā",
    # Plateau examples (tests/fixtures/chao_tones/inputs/plateau_examples.txt)
    "m̩̄pa᷆d",
    "xɛ̃̀ɾī",
    "sākpō",
    "kwōː",
    "kwóː",
    "ɡʲa᷆n",
    "ɡʲa᷇n",
]


@pytest.mark.parametrize("word", ROUND_TRIP_WORDS)
def test_round_trip(word):
    assert convert(chao_tones.convert(word)) == unicodedata.normalize("NFC", word)
