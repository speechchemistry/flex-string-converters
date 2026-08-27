# -*- coding: utf-8 -*-
#
#   Tests for the Zhire phonetic-to-phonemic conversion
#
#   These exercise convert() directly: it takes and returns a plain string
#   and needs no FLEx project, so it runs on any platform.
#
#   Each test here pins one general rule with a minimal, deliberately
#   synthetic example that isolates the mechanism. Real-word coverage lives
#   in the approval corpus (tests/fixtures/phonetic2phonemic/), built from
#   the phonology sketch's own examples and 246 real phonetic/phonemic
#   pairs from a FLEx export — see plans/old/zhire-phonetic-to-phonemic-fst.md.
#   A rule already demonstrated by a real word there isn't re-asserted here
#   with the same word.
#

import unicodedata

import pytest

from phonetic2phonemic import convert


def test_r_and_the_flap_notation_both_give_r():
    # Variant assertion 1: [ɾ] and [r] are the same phoneme. Real data
    # writes /r/, but the phonology sketch's own notation is /ɾ/, so both
    # must convert.
    assert convert("ɾa") == "ra"
    assert convert("ra") == "ra"


def test_ejective_mark_is_deleted():
    # Variant assertion 2: /ts/ is realised [ts] or [tsʼ] -- the ejective
    # release is notation, not a separate phoneme.
    assert convert("tsʼēn") == "tsēn"


def test_plain_nz_becomes_ndz():
    # Variant assertion 3, applied to the plain (not superscript) form in
    # any position, per your confirmation that the phonemic field
    # currently inherits whatever the phonetic transcription had.
    assert convert("nzoɾ") == "ndzor"


def test_plain_ndz_is_left_alone():
    # The other half of the same rule: ndz must fall through unchanged,
    # since it's already the target spelling -- only ndʒ gets rewritten.
    assert convert("ndza") == "ndza"


def test_plain_ndʒ_becomes_ndz():
    # Variant assertion 4, plain form, any position.
    assert convert("ndʒa") == "ndza"


def test_dʒ_with_no_preceding_nasal_is_not_collapsed_into_dz():
    # Guards against over-application of the ndʒ->ndz rule: without a
    # preceding nasal, /dʒ/ is a distinct phoneme and must stay /dʒ/.
    assert convert("dʒa") == "dʒa"


def test_ɲ_becomes_nj():
    # Variant assertion 5, implemented as the sketch states it even though
    # it conflicts with some real data -- see the plan's Decisions.
    assert convert("ɲo") == "njo"


def test_barred_i_becomes_schwa():
    # Demonstrated by the phonology sketch's own orthography chart
    # (/ɣ/ [ɣɨɾ] -> ghər), not stated anywhere in its prose.
    assert convert("ɣɨɾ") == "ɣər"


def test_near_close_near_front_i_becomes_i():
    # [ɪ] and [i] are not distinguished at the phonemic level -- not
    # stated anywhere in the phonology sketch's prose or charts, found
    # only from the hidden test data. rɪ̄xí 'head' is a real attested
    # word from that data, not a constructed example.
    assert convert("rɪ̄xí") == "rīxí"


def test_tie_bar_deletion_does_not_block_a_multi_character_token():
    # The bug an earlier draft of this plan shipped: putting the release-
    # mark deletions inside the FST as epsilon arcs let a tie bar sitting
    # inside "nz" or "ndʒ" block that token from matching, so the
    # surrounding rule silently failed to fire. This is the case a
    # Python pre-pass (stripping the marks before tokenisation) exists to
    # cover -- ordinary IPA writes a tie-barred affricate this way, and
    # the phonology sketch itself does too (k͡pōtòŋ, k͡pɔ̄ɾí).
    assert convert("nd͡ʒa") == "ndza"
    assert convert("n͡za") == "ndza"


def test_aspiration_mark_is_deleted():
    # Not stated anywhere in the phonology sketch -- found only by
    # checking against the real FLEx export (sīsʰip 'sweat').
    assert convert("sīsʰi᷆p") == "sīsi᷆p"


def test_tone_marks_are_preserved():
    # The phonemic form stays tonal: stripping tone is
    # phonemic2orthography.py's job, at the end of the chain.
    assert convert("pá") == "pá"


@pytest.mark.parametrize("mark", [
    "\u030B",  # ő
    "\u0301",  # ó
    "\u0304",  # ō
    "\u0300",  # ò
    "\u030F",  # ȍ
    "\u030C",  # ǒ
    "\u0302",  # ô
    "\u1DC4",  # o᷄
    "\u1DC5",  # o᷅
    "\u1DC8",  # o᷈
    "\u1DC6",  # o᷆
    "\u1DC7",  # o᷇
    "\u1DC9",  # o᷉
])
def test_every_ipa_tone_diacritic_is_preserved(mark):
    # The full IPA set of 13, not only the 10 the phonology sketch happens
    # to use -- the same table chao-tone-letters/converters/diacritics2chao.py
    # carries. A mark the draft sketch hasn't needed yet is a gap in the
    # sketch, not a tone the phonemic level can't represent, so accepting it
    # costs nothing and raising on it would reject valid IPA.
    assert convert("po" + mark) == unicodedata.normalize("NFC", "po" + mark)


def test_nasalisation_tilde_is_preserved():
    assert convert("sã̀") == "sã̀"


def test_length_mark_is_preserved():
    assert convert("kpiː") == "kpiː"


def test_space_is_kept_as_a_word_divider():
    assert convert("a b") == "a b"


@pytest.mark.parametrize("phonetic", [
    "hʷók",   # a modifier letter -- rejected, not transliterated, since
              # it asserts a syllable-structure interpretation that hasn't
              # been settled for Zhire (see the plan's Decisions)
    "q",      # not a Zhire phoneme at all
    "dzu᷈:ŋ",  # the sketch's own ASCII-colon typo for the length mark --
              # corrected in the fixture, not accepted by convert()
])
def test_unmapped_input_raises_rather_than_passing_through_or_dropping_silently(phonetic):
    with pytest.raises(ValueError):
        convert(phonetic)
