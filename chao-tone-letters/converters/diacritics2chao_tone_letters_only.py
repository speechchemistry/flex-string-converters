#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Chao tone letters only, from tone diacritics
#
#   Identical to diacritics2chao.py's tone_diacritics_to_chao_letters(): the
#   Chao tone letters extracted from the input's tone diacritics, with no
#   base text (nə̀jɛ᷅t -> ˨ ˨˧). diacritics2chao.py's own Convert() always
#   returns base text plus tone letters together; this file exists so an SIL
#   FLEx Process, which always calls a bare Convert(input_string) with no
#   keyword arguments and can only choose *which file* to point at, can
#   select the tone-letters-only extraction instead. Convert() here forwards
#   to diacritics2chao.tone_diacritics_to_chao_letters() and has no rules of
#   its own.
#
#   No command line interface: tone_diacritics_to_chao_letters() is already
#   directly importable from diacritics2chao.py for any Python use outside
#   FlexTools, so a CLI here would add nothing beyond what plain Python
#   import already gives. This file's only reason to exist is to give FLEx's
#   Process dialog a file to point at -- see AGENTS.md's Converter
#   Conventions for the carve-out this relies on (also used by
#   diacritics2chao_attached.py).
#
#   Tim Kempton
#   September 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import os

# diacritics2chao.py lives in this same converters/ directory. A FLEx
# Process, like FlexTools, is expected to import a script by file path,
# which does not put the script's own folder on sys.path, so it is added
# explicitly here -- see the header comment above.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diacritics2chao


def Convert(input_string): # function is named "Convert" so it can be used as an SIL Flex Process
    return diacritics2chao.tone_diacritics_to_chao_letters(input_string)
