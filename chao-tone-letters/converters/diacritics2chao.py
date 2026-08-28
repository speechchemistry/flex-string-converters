#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Chao tone letters from tone diacritics
#
#   Returns the input with tone diacritics stripped, followed by the
#   Chao tone letters extracted from those tone diacritics. Shared by the
#   FlexTools module Extract_Chao_tone_letters_from_tone_diacritics.py, usable
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


# The 13 recognised tone diacritics and the Chao tone letters each maps to.
# Both tone_diacritics_to_chao_letters() and Convert() derive from this one
# table, so the codepoint set is never duplicated.
TONE_DIACRITIC_TO_CHAO_LETTERS = {'̋':'˥', # ő
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

TONE_DIACRITICS = frozenset(TONE_DIACRITIC_TO_CHAO_LETTERS)

# Tone-bearing vowels: the base letter of a grapheme cluster counts as a
# vowel for grouping tone diacritics into syllables. The reverse converter
# (converters/chao2diacritics.py) keeps its own copy rather than importing
# this one, since a converter must stand alone as a FLEx Process.
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
        marks = [mark for mark in cluster[1:] if mark in TONE_DIACRITICS]
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

def tone_diacritics_to_chao_letters(input_string):
    # ensure string is decomposed into separate code points, so a cluster's
    # base letter and its combining tone diacritics are separate code points
    input_decomposed = unicodedata.normalize('NFD',input_string)
    word_groups = []
    for word in input_decomposed.split():
        groups = []
        for marks in _tone_bearing_units(word):
            if not marks:
                continue
            tone_letters = ''.join(TONE_DIACRITIC_TO_CHAO_LETTERS[mark] for mark in marks)
            groups.append(_collapse_adjacent_duplicates(tone_letters))
        if groups:
            word_groups.append(' '.join(groups))
    return '  '.join(word_groups)

def _attached_word(word):
    # Rewrites one (NFD-normalised) word with each unit's tone letters written
    # immediately after the unit, instead of gathered into a trailing section.
    # Segments exactly as _tone_bearing_units() does, but keeps the clusters so
    # the tone letters can be put back in place.
    pieces = []
    current_run = None          # [piece indices, marks] of the open vowel run

    def close_run():
        nonlocal current_run
        if current_run is not None:
            indices, marks = current_run
            if marks:
                letters = ''.join(TONE_DIACRITIC_TO_CHAO_LETTERS[mark] for mark in marks)
                pieces[indices[-1]] += _collapse_adjacent_duplicates(letters)
            current_run = None

    for cluster in regex.findall(r'\X', word):
        base = cluster[0]
        marks = [mark for mark in cluster[1:] if mark in TONE_DIACRITICS]
        kept = ''.join(ch for ch in cluster if ch not in TONE_DIACRITICS)
        index = len(pieces)
        pieces.append(kept)
        if any(mark in SYLLABIC_MARKS for mark in cluster[1:]):
            close_run()
            if marks:
                letters = ''.join(TONE_DIACRITIC_TO_CHAO_LETTERS[mark] for mark in marks)
                pieces[index] += _collapse_adjacent_duplicates(letters)
        elif base in TONE_BEARING_VOWELS:
            if current_run is None:
                current_run = [[], []]
            current_run[0].append(index)
            current_run[1].extend(marks)
        elif unicodedata.category(base) == 'Lm':
            pass
        else:
            close_run()
    close_run()
    return ''.join(pieces)

def tone_diacritics_to_attached(input_string):
    # The counterpart of tone_diacritics_to_chao_letters(): the same tone
    # letters, but written after the syllable each one marks rather than
    # gathered into a section. Spacing then carries no meaning at all, so a
    # shell pipeline or spreadsheet that collapses runs of spaces or adds a
    # trailing one cannot change how the result reads back.
    input_decomposed = unicodedata.normalize('NFD', input_string)
    tokens = regex.split(r'(\s+)', input_decomposed)
    rewritten = [
        token if token == '' or token.isspace() else _attached_word(token)
        for token in tokens
    ]
    return unicodedata.normalize('NFC', ''.join(rewritten))

def Convert(input_string, attached=False): # function is named "Convert" so it can be used as an SIL Flex Process
    # attached=True writes each unit's tone letters after the unit instead of
    # in a trailing section. It is off by default so that the FLEx Process and
    # every existing caller keep the output they already have.
    if attached:
        return tone_diacritics_to_attached(input_string)
    # ensure string is decomposed into separate code points, so the 13
    # recognised tone diacritics can be removed without disturbing others
    input_decomposed = unicodedata.normalize('NFD',input_string)
    base_decomposed = ''.join(
        ch for ch in input_decomposed if ch not in TONE_DIACRITICS)
    # recompose so unrelated combining marks combine normally
    base_text = unicodedata.normalize('NFC',base_decomposed)
    tone_letters = tone_diacritics_to_chao_letters(input_string)
    if not tone_letters:
        return base_text
    return f"{base_text} {tone_letters}"


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Strips tone diacritics to base text and appends its Chao tone letters"""
    parser = argparse.ArgumentParser(
        description="Strip tone diacritics to base text and append its "
                    "Chao tone letters, e.g. nə̀jɛ᷅t -> nəjɛt ˨ ˨˧.")
    parser.add_argument("--attached", action="store_true",
                        help="write each tone letter after the syllable it "
                             "marks (ma\u02e6 ti\u02e6\u02e8) instead of in a "
                             "trailing section (ma ti \u02e6  \u02e6\u02e8); the "
                             "result carries no meaning in its spacing, so a "
                             "pipeline or spreadsheet cannot destroy it")
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
        print(Convert(line, attached=args.attached))

if __name__ == '__main__':
    main()
