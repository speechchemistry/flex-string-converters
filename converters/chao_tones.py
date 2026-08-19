#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Chao tone letters from accent notation
#
#   Returns the input with tone-accent diacritics stripped, followed by the
#   Chao tone letters extracted from that accent notation. Shared by the
#   FlexTools module Extract_Chao_tone_letters_from_accent_notation.py, usable
#   as an SIL Flex Process, and runnable as the command line tool below.
#
#   Tim Kempton
#   August 2024
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import argparse
import unicodedata
import regex


# The 13 recognised tone-accent combining marks and the Chao tone letters
# each maps to. Both extract_chao_letters() and convert() derive from this
# one table, so the codepoint set is never duplicated.
ACCENT_TO_TONE_LETTERS = {'̋':'˥', # ő
                   '́':'˦', # ó
                   '̄':'˧', # ō
                   '̀':'˨', # ò
                   '̏':'˩', # ȍ
                   '̌':'˨˦', # ǒ trying to be more consistent than IPA chart
                   '̂':'˦˨', # ô trying to be more consistent than IPA chart
                   '᷄':'˧˦', # o᷄ trying to be more consistent than IPA chart
                   '᷅':'˨˧', # o᷅ trying to be more consistent than IPA chart
                   '᷈':'˨˦˨', # o᷈ trying to be more consistent than IPA chart
                   '᷆':'˧˨', # o᷆
                   '᷇':'˦˧', # o᷇
                   '᷉':'˦˨˦'} # o᷉

TONE_ACCENT_MARKS = frozenset(ACCENT_TO_TONE_LETTERS)

# Tone-bearing vowels: the base letter of a grapheme cluster counts as a
# vowel for grouping tone accents into syllables. Change 2
# (converters/chao_accents.py) keeps its own copy rather than importing this
# one, since a converter must stand alone as a FLEx Process.
TONE_BEARING_VOWELS = frozenset(
    'a e i o u y ɨ ʉ ɯ ɪ ʏ ʊ ø ɘ ɵ ɤ ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ ɶ ɑ ɒ ɚ ɝ'.split(' '))

# A cluster carrying one of these is its own tone-bearing unit, even when
# its base letter is a consonant, and it never joins a following vowel.
SYLLABIC_MARKS = frozenset({'̩', '̍'})


def _tone_bearing_units(word):
    # Walk word (already NFD-normalised) by grapheme cluster, grouping
    # consecutive vowel clusters into one unit (a diphthong is one
    # syllable), splitting out a syllabic-marked cluster as its own unit,
    # and treating a modifier letter (category Lm, e.g. the length mark ː)
    # as transparent: it neither starts a unit nor breaks a vowel run.
    # Anything else (a consonant, punctuation, a digit) breaks a vowel run
    # without starting a unit of its own.
    units = []
    current_run = None
    for cluster in regex.findall(r'\X', word):
        base = cluster[0]
        marks = [mark for mark in cluster[1:] if mark in TONE_ACCENT_MARKS]
        if any(mark in SYLLABIC_MARKS for mark in cluster[1:]):
            if current_run is not None:
                units.append(current_run)
                current_run = None
            units.append(marks)
        elif base in TONE_BEARING_VOWELS:
            if current_run is None:
                current_run = []
            current_run.extend(marks)
        elif unicodedata.category(base) == 'Lm':
            pass
        elif current_run is not None:
            units.append(current_run)
            current_run = None
    if current_run is not None:
        units.append(current_run)
    return units

def _collapse_adjacent_duplicates(tone_letters):
    collapsed = []
    for letter in tone_letters:
        if not collapsed or collapsed[-1] != letter:
            collapsed.append(letter)
    return ''.join(collapsed)

def extract_chao_letters(input_string):
    # ensure string is decomposed into separate code points, so a cluster's
    # base letter and its combining accent marks are separate code points
    input_decomposed = unicodedata.normalize('NFD',input_string)
    word_groups = []
    for word in input_decomposed.split():
        groups = []
        for marks in _tone_bearing_units(word):
            if not marks:
                continue
            tone_letters = ''.join(ACCENT_TO_TONE_LETTERS[mark] for mark in marks)
            groups.append(_collapse_adjacent_duplicates(tone_letters))
        if groups:
            word_groups.append(' '.join(groups))
    return '  '.join(word_groups)

def convert(input_string): # function is named "convert" so it can be used as an SIL Flex Process
    # ensure string is decomposed into separate code points, so tone-accent
    # marks can be removed individually without disturbing other diacritics
    input_decomposed = unicodedata.normalize('NFD',input_string)
    base_decomposed = ''.join(
        ch for ch in input_decomposed if ch not in TONE_ACCENT_MARKS)
    # recompose so unrelated combining marks combine normally
    base_text = unicodedata.normalize('NFC',base_decomposed)
    tone_letters = extract_chao_letters(input_string)
    if not tone_letters:
        return base_text
    return f"{base_text} {tone_letters}"


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Strips tone-accent notation to base text and appends its Chao tone letters"""
    parser = argparse.ArgumentParser(
        description="Strip tone-accent notation to base text and append its "
                    "Chao tone letters, e.g. nə̀jɛ᷅t -> nəjɛt ˨ ˨˧.")
    parser.add_argument("text", nargs="*",
                        help="the text to convert; with no text given, lines "
                             "are read from standard input instead")
    args = parser.parse_args()
    return args

def use_utf8(*streams):
    # The output is IPA and Chao tone letters, so don't leave the encoding to
    # the console code page (which is not UTF-8 by default on Windows)
    for stream in streams:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

def main():
    args = parse_arguments()
    use_utf8(sys.stdin, sys.stdout)
    if args.text:
        lines = args.text
    else:
        lines = (line.rstrip("\n") for line in sys.stdin)
    for line in lines:
        print(convert(line))

if __name__ == '__main__':
    main()
