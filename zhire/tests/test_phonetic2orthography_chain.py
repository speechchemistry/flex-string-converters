# -*- coding: utf-8 -*-
#
#   End-to-end test of the phonetic -> phonemic -> orthography chain
#
#   The phonology sketch's own orthography charts give both ends of the
#   chain for the same 47 rows that
#   tests/fixtures/phonetic2phonemic/phonology_sketch_examples.txt already
#   checks at the phonemic level: a phonetic example word and its
#   orthographic spelling. Running the phonetic form through
#   phonetic2phonemic.convert() and then phonemic2orthography.convert() and
#   comparing to the orthography column is therefore the strongest test
#   available for the composition, since it needs no separately-authored
#   expectation.
#
#   3 of the 47 rows are held out -- each contradicts another row of the
#   same source chart, and is a source error rather than a gap in either
#   converter (see plans/old/zhire-phonetic-to-phonemic-fst.md's Prototype
#   results section):
#
# 'door': [ndɛ̀n] -> `nden` -- source error, contradicts another row of the same chart
# 'branch': [ŋɡēj] -> `nggei` -- source error, contradicts another row of the same chart
# 'chin': [nzo᷇ɾ] -> `nzor` -- source error, contradicts another row of the same chart
#
#   Excluded here rather than asserted against, pending correction upstream
#   in the phonology sketch.
#
#   Each phonetic example is transliterated to plain notation where the
#   sketch writes ʷ/ʲ/ᵐ/ⁿ/ᵑ, since phonetic2phonemic.convert() rejects that
#   notation outright -- see the plan's "Modifier letters rejected, not
#   transliterated" section. Generated mechanically from the sketch's own
#   chart rows rather than transcribed by hand, per
#   AGENTS.md's External Specifications section on treating a copy from a
#   source document as a migration rather than as reading comprehension.
#

import unicodedata

import pytest

from phonetic2phonemic import convert as phonetic_to_phonemic
from phonemic2orthography import convert as phonemic_to_orthography

# (phonetic example, orthographic spelling), one row per phoneme in the
# sketch's three orthography charts, in chart order.
CHART_ROWS = [
    ('ba᷆m', 'bam'),
    ('tʃi᷆', 'ci'),
    ('da᷆ɾ', 'dar'),
    ('dza᷆ŋ', 'dzang'),
    ('fa᷆b', 'fab'),
    ('ɡa᷆b', 'gab'),
    ('ɡbàk', 'gbak'),
    ('ɣɨ᷅ɾ', 'ghər'),
    ('hɔ̃̄', 'hɔ̃'),
    ('dʒa᷆m', 'jam'),
    ('kàm', 'kam'),
    ('xák', 'khak'),
    ('kpàŋ', 'kpang'),
    ('mɛ᷆k', 'mɛk'),
    ('mba᷄ŋ', 'mbang'),
    ('nāŋ', 'nang'),
    ('àŋā', 'anga'),
    ('ŋmɡba᷆n', 'ngban'),
    ('pə᷄ɾ', 'pər'),
    ('ɾa᷆ŋ', 'rang'),
    ('sób', 'sob'),
    ('ʃi᷆', 'shi'),
    ('tám', 'tam'),
    ('tsʼēn', 'tsen'),
    ('vīni᷆', 'vini'),
    ('wōk', 'wok'),
    ('jòbō', 'yobo'),
    ('zàkī', 'zaki'),
    ('ʒǐ', 'zhi'),
    ('hā', 'ha'),
    ('fé', 'fe'),
    ('bɛ̀', 'bɛ'),
    ('kə́', 'kə'),
    ('kí', 'ki'),
    ('só', 'so'),
    ('fɔ̄', 'fɔ'),
    ('tʃū', 'cu'),
    ('twɔ᷅ŋ', 'twɔng'),
    ('tjɛ᷅ɾ', 'tyɛr'),
    ('sã̀', 'sã'),
    ('kpi᷆ː', 'kpii'),
    ('hwók', 'whok'),
    ('ɕwè', 'whye'),
    ('ʑwú', 'yhu'),
]


@pytest.mark.parametrize("phonetic, orthographic", CHART_ROWS)
def test_composed_converters_match_the_sketchs_own_orthography_chart(phonetic, orthographic):
    phonemic = phonetic_to_phonemic(phonetic)
    result = phonemic_to_orthography(phonemic)
    assert unicodedata.normalize("NFC", result) == unicodedata.normalize("NFC", orthographic)
