# -*- coding: utf-8 -*-
#
#   Tests for the diacritics2chao_tone_letters_only.py wrapper
#
#   This file has no logic of its own -- its Convert() forwards to
#   diacritics2chao.tone_diacritics_to_chao_letters() -- so these tests pin
#   the delegation itself, not the extraction rules, which
#   test_diacritics2chao.py already covers directly.
#

import unicodedata

import pytest

import diacritics2chao
from diacritics2chao_tone_letters_only import Convert

NFC = lambda text: unicodedata.normalize("NFC", text)


@pytest.mark.parametrize("text", [
    "nə̀jɛ᷅t",  # the SPEC.md example
    "nə̀t nə̀t",             # a two-word input
    "cat",                           # toneless, so nothing to extract
])
def test_forwards_to_tone_diacritics_to_chao_letters(text):
    text = NFC(text)
    assert Convert(text) == diacritics2chao.tone_diacritics_to_chao_letters(text)


def test_is_not_reimplementing_the_rule_itself():
    # Guards against a future edit accidentally duplicating the extraction
    # logic here instead of delegating to it.
    text = NFC("nə̀jɛ᷅t")
    assert Convert(text) != diacritics2chao.Convert(text)  # not base text + tone letters
    assert Convert(text) == "˨ ˨˧"
