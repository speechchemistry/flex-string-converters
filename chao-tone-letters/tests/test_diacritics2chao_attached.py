# -*- coding: utf-8 -*-
#
#   Tests for the diacritics2chao_attached.py wrapper
#
#   This file has no logic of its own -- its Convert() forwards to
#   diacritics2chao.Convert(input_string, attached=True) -- so these tests
#   pin the delegation itself, not the attached-output rules, which
#   test_diacritics2chao.py already covers directly.
#

import unicodedata

import pytest

import diacritics2chao
from diacritics2chao_attached import Convert

NFC = lambda text: unicodedata.normalize("NFC", text)


@pytest.mark.parametrize("text", [
    "nə̀jɛ᷅t",  # the SPEC.md example
    "má tî",              # a two-word input
    "cat",                          # toneless, so nothing to attach
])
def test_forwards_to_diacritics2chao_attached_output(text):
    text = NFC(text)
    assert Convert(text) == diacritics2chao.Convert(text, attached=True)


def test_is_not_reimplementing_the_rule_itself():
    # Guards against a future edit accidentally duplicating the attached-
    # output logic here instead of delegating to it.
    text = NFC("bjo᷆ sādù")
    assert Convert(text) != diacritics2chao.Convert(text)  # not the trailing form
    assert Convert(text) == diacritics2chao.tone_diacritics_to_attached(text)
