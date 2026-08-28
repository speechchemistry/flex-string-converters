# -*- coding: utf-8 -*-
#
#   Tests for the tone-diacritics-from-Chao-tone-letters conversion
#
#   These exercise convert() and chao_letters_to_tone_diacritics() directly:
#   both take and return a plain string and need no FLEx project, so they
#   run on any platform.
#

import unicodedata

import pytest

import diacritics2chao
from chao2diacritics import (
    CHAO_LETTERS_TO_TONE_DIACRITIC,
    TONE_BEARING_VOWELS,
    SYLLABIC_MARKS,
    chao_letters_to_tone_diacritics,
    convert,
    convert_with_warnings,
)


# ---------------------------------------------------------------
# Table guards: this file's copies must never drift from diacritics2chao.py's.


def test_chao_letters_to_tone_diacritic_is_the_exact_inverse_of_tone_diacritic_to_chao_letters():
    tone_diacritic_to_chao_letters = diacritics2chao.TONE_DIACRITIC_TO_CHAO_LETTERS
    assert len(CHAO_LETTERS_TO_TONE_DIACRITIC) == len(tone_diacritic_to_chao_letters) == 13
    inverse = {
        chao_letters: diacritic
        for diacritic, chao_letters in tone_diacritic_to_chao_letters.items()
    }
    assert CHAO_LETTERS_TO_TONE_DIACRITIC == inverse


def test_tone_bearing_vowels_matches_diacritics2chao():
    assert TONE_BEARING_VOWELS == diacritics2chao.TONE_BEARING_VOWELS


def test_syllabic_marks_matches_diacritics2chao():
    assert SYLLABIC_MARKS == diacritics2chao.SYLLABIC_MARKS


# ---------------------------------------------------------------
# One case per tone diacritic row, parametrized off the reverse table.


@pytest.mark.parametrize("tone_letters, expected", [
    ("˥", "ő"), ("˦", "ó"), ("˧", "ō"), ("˨", "ò"), ("˩", "ȍ"),
    ("˨˦", "ǒ"), ("˦˨", "ô"), ("˧˦", "o᷄"), ("˨˧", "o᷅"),
    ("˨˦˨", "o᷈"), ("˧˨", "o᷆"), ("˦˧", "o᷇"), ("˦˨˦", "o᷉"),
])
def test_chao_letters_to_tone_diacritics_one_case_per_row(tone_letters, expected):
    assert chao_letters_to_tone_diacritics("o", tone_letters) == unicodedata.normalize("NFC", expected)


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


def test_length_mark_keeps_the_diacritic_on_the_vowel():
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
    "o ˥˩",        # a contour with no tone diacritic among the 13
    "ka ˨˩",       # a contour with no tone diacritic among the 13
])
def test_mismatch_returns_the_input_unchanged(text):
    assert convert(text) == text


# ---------------------------------------------------------------
# Round trip: diacritics2chao.convert() followed by chao2diacritics.convert()
# returns the original word, for words where the forward conversion loses
# no information. A diphthong whose tone diacritic placement is ambiguous
# on the way back (e.g. kǎi, whose tone letters are indistinguishable from
# kàí's) is a documented exception and deliberately left out -- see this
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
    # Plateau examples (tests/fixtures/diacritics2chao/inputs/plateau_examples.txt)
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
    assert convert(diacritics2chao.convert(word)) == unicodedata.normalize("NFC", word)


# ---------------------------------------------------------------
# Where the tone letters sit does not matter: attached to the syllable,
# detached in a trailing section, pre-posed, or a mixture of those.

NFC = lambda text: unicodedata.normalize("NFC", text)


@pytest.mark.parametrize("text", [
    "ma ti \u02e6  \u02e6\u02e8",   # detached, the two-space word gap
    "ma ti \u02e6 \u02e6\u02e8",    # detached, single-spaced
    "ma ti \u02e6  \u02e6\u02e8 ",  # detached, with a trailing space
    "ma\u02e6 ti\u02e6\u02e8",      # attached
    "\u02e6ma \u02e6\u02e8ti",      # pre-posed
    "\u02e6  \u02e6\u02e8 ma ti",   # a leading rather than trailing section
    "ma\u02e6 ti \u02e6\u02e8",     # one attached, one detached
])
def test_every_arrangement_of_the_same_tone_letters_gives_the_same_result(text):
    assert convert(text) == NFC("m\u00e1 t\u00ee")


def test_an_attached_group_reaches_back_over_a_coda_consonant():
    assert convert("mat\u02e6") == NFC("m\u00e1t")


def test_attached_marking_may_leave_a_syllable_toneless():
    # Each attached letter says which syllable it belongs to, so an unmarked
    # syllable is unambiguously untoned -- no count check applies.
    assert convert("ma\u02e6 ti") == NFC("m\u00e1 ti")


def test_a_detached_group_fills_a_syllable_an_attached_one_did_not_claim():
    assert convert("pa ta\u02e7 ka\u02e8 \u02e9") == NFC("p\u0201 t\u0101 k\u00e0")


def test_whitespace_orphaned_by_removing_a_tone_section_is_dropped():
    assert convert("bjo sadu  \u02e7\u02e8  \u02e7 \u02e8") == NFC("bjo\u1dc6 s\u0101d\u00f9")


def test_whitespace_between_attached_words_is_kept():
    assert convert("ma\u02e6 ti\u02e6\u02e8") == NFC("m\u00e1 t\u00ee")


def test_detached_groups_must_fill_the_unmarked_syllables_exactly():
    # Position is a detached letter's only clue, so a partial fill would have
    # to guess that the missing tones are the trailing ones. Dropping the
    # *first* letter here would otherwise shift every tone one syllable left
    # and still look plausible.
    short = "bjo sadu  \u02e7 \u02e8"
    assert convert(short) == short


# ---------------------------------------------------------------
# Warnings. convert() stays a plain string-to-string function, so the reasons
# come from convert_with_warnings(); only the CLI writes them to stderr.


def test_convert_is_the_first_element_of_convert_with_warnings():
    for text in ["ma\u02e6 ti\u02e6\u02e8", "ka\u02e8\u02e9", "cat"]:
        assert convert(text) == convert_with_warnings(text)[0]


@pytest.mark.parametrize("text", ["ma ti", "cat", "", "cat   dog"])
def test_a_line_with_no_tone_letters_warns_nothing(text):
    assert convert_with_warnings(text)[1] == []


def test_warns_when_detached_groups_do_not_match_the_unmarked_syllables():
    _, warnings = convert_with_warnings("bjo sadu  \u02e7 \u02e8")
    assert warnings == [
        "not converted: 2 detached tone letter groups for 3 unmarked syllables"
    ]


def test_warns_when_a_contour_has_no_tone_diacritic():
    _, warnings = convert_with_warnings("ka\u02e8\u02e9")
    assert warnings == ["not converted: no tone diacritic for \u02e8\u02e9"]


def test_warns_when_two_groups_bind_to_one_syllable():
    _, warnings = convert_with_warnings("ma\u02e6t\u02e8")
    assert warnings == ["not converted: two tone letter groups on one syllable"]


def test_warns_when_the_base_text_already_carries_a_tone_diacritic():
    # Converts, but to a doubly marked vowel -- the data is half converted.
    result, warnings = convert_with_warnings(NFC("m\u00e1") + "\u02e8")
    assert result == NFC("ma\u0301\u0300")
    assert "base text already carries a tone diacritic" in warnings


def test_warns_when_a_line_mixes_attached_and_detached_tone_letters():
    _, warnings = convert_with_warnings("pa ta\u02e7 ka\u02e8 \u02e9")
    assert "line mixes attached and detached tone letters" in warnings


def test_warns_when_attached_marking_leaves_some_syllables_unmarked():
    _, warnings = convert_with_warnings("ma\u02e6 ti")
    assert "1 of 2 syllables not marked by an attached tone letter" in warnings


def test_a_fully_attached_line_warns_nothing():
    result, warnings = convert_with_warnings("ma\u02e6 ti\u02e8 ka\u02e7")
    assert result == NFC("m\u00e1 t\u00ec k\u0101")
    assert warnings == []
