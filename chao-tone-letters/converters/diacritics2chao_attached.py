#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Chao tone letters from tone diacritics, attached to their syllable
#
#   Identical to diacritics2chao.py, except attached output is always on:
#   each tone-bearing unit's Chao tone letters are written immediately after
#   that unit (nə̀jɛ᷅t -> nə˨jɛ˨˧t) instead of gathered into a trailing
#   section. Exists only because an SIL FLEx Process always calls a bare
#   Convert(input_string) with no keyword arguments, so diacritics2chao.py's
#   --attached flag has no way to reach it; pointing a FLEx Process at this
#   file instead selects that same output. See diacritics2chao.py for the
#   full transform rules -- Convert() here forwards to its
#   Convert(input_string, attached=True) and has no rules of its own.
#
#   Verified against a real FLEx Process (2026-09-01): a raw Process can be
#   pointed directly at this file and resolves its import of diacritics2chao
#   correctly.
#
#   No command line interface: python3 diacritics2chao.py --attached already
#   does exactly this from the command line, so a second CLI here would only
#   duplicate it. This file's only reason to exist is to give FLEx's Process
#   dialog a file to point at -- see AGENTS.md's Converter Conventions for
#   the carve-out this relies on.
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
    return diacritics2chao.Convert(input_string, attached=True)
