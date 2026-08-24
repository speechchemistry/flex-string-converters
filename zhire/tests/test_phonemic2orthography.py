# -*- coding: utf-8 -*-
#
#   Tests for the Zhire phonemic-to-orthography conversion
#
#   These exercise convert() directly: it takes and returns a plain string
#   and needs no FLEx project, so it runs on any platform.
#
#   Each test here pins one general rule with a minimal, deliberately
#   synthetic example that isolates the mechanism. Real-word coverage lives
#   in the approval corpus (tests/fixtures/phonemic2orthography/), built from
#   99 real phonemic/orthographic pairs supplied by the language consultant
#   (sample_phonemic2orthographic_data.csv) — see
#   plans/zhire-phonemic-to-orthography-fst.md. A rule already demonstrated
#   by a real word there isn't re-asserted here with the same word.
#

import pytest

from phonemic2orthography import convert


def test_strips_a_tone_diacritic():
    # Every vowel's tone diacritics come off on the way to orthography;
    # none of the orthography statement's own spellings carry one.
    assert convert("pá") == "pa"


def test_keeps_the_nasalisation_tilde():
    # /ã/ -> ã is the orthography statement's own worked example (the word
    # for 'frog'); unlike a tone diacritic, the combining tilde survives.
    assert convert("sã") == "sã"


def test_doubles_a_lengthened_vowel():
    # /iː/ -> ii is the orthography statement's own worked example (the
    # word for 'flock of birds'), generalised to every vowel per your
    # confirmation.
    assert convert("kpiː") == "kpii"


def test_doubles_a_nasalised_and_lengthened_vowel_keeping_the_tilde_on_each_copy():
    # No attested example exists for this combination yet; this pins the
    # assumption you confirmed rather than a real word.
    assert convert("ɔ̃ː") == "ɔ̃ɔ̃"


@pytest.mark.parametrize("phonemic, orthographic", [
    ("dʒa", "ja"),    # dʒ -> j: plain d+ʒ would wrongly give "dzh"
    ("hwa", "wha"),   # hw -> wh: letter order flips
    ("ɕwa", "whya"),  # ɕw -> why: ɕ has no meaning on its own
    ("ʑwa", "yha"),   # ʑw -> yh: ʑ has no meaning on its own
])
def test_override_sequences_that_cant_fall_out_of_plain_concatenation(phonemic, orthographic):
    assert convert(phonemic) == orthographic


def test_space_is_kept_as_a_word_divider():
    assert convert("a b") == "a b"


def test_unmapped_input_raises_rather_than_passing_through_or_dropping_silently():
    # ɲ (and the other IPA modifier-letter notation the orthography statement
    # documents) isn't supported yet: real phonemic data currently spells
    # this and similar sounds with plain letter sequences only (e.g. "nj"),
    # per your confirmation. A bare ɲ is therefore unmapped, not an
    # alternate spelling.
    with pytest.raises(ValueError):
        convert("ɲ")
