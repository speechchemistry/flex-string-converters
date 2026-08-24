#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Tone diacritics from Chao tone letters
#
#   Reverses converters/diacritics2chao.py: given base text followed by the
#   Chao tone letters extracted from it, places tone diacritics back onto
#   the tone-bearing units they belong to, e.g. nəjɛt ˨ ˨˧ -> nə̀jɛ᷅t.
#
#   Tim Kempton
#   August 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import argparse
import unicodedata
import regex


# The inverse of converters/diacritics2chao.py's TONE_DIACRITIC_TO_CHAO_LETTERS.
# Kept as its own copy rather than an import, since a converter must stand
# alone as a FLEx Process; guarded against drift from that file's table by a
# test.
CHAO_LETTERS_TO_TONE_DIACRITIC = {'˥':'̋', # ő
                   '˦':'́', # ó
                   '˧':'̄', # ō
                   '˨':'̀', # ò
                   '˩':'̏', # ȍ
                   '˨˦':'̌', # ǒ
                   '˦˨':'̂', # ô
                   '˧˦':'᷄', # o᷄
                   '˨˧':'᷅', # o᷅
                   '˨˦˨':'᷈', # o᷈
                   '˧˨':'᷆', # o᷆
                   '˦˧':'᷇', # o᷇
                   '˦˨˦':'᷉'} # o᷉

# Tone-bearing vowels and syllabic marks: copies of diacritics2chao.py's
# tables, guarded against drift by a test that checks them against that
# file's.
TONE_BEARING_VOWELS = frozenset(
    'a e i o u y ɨ ʉ ɯ ɪ ʏ ʊ ø ɘ ɵ ɤ ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ ɶ ɑ ɒ ɚ ɝ'.split(' '))
SYLLABIC_MARKS = frozenset({'̩', '̍'})

# A trailing tone-letters section: one or more level tone letters
# (U+02E5-U+02E9), with any run of spaces in between (a single space
# between groups of one word, a run of two or more between words).
_SPLIT_RE = regex.compile(r'^(?P<base>.*?)\s+(?P<tones>[˥-˩][˥-˩ ]*)$')


def _word_units(word):
    # Walk word (NFD-normalised) by grapheme cluster. Returns:
    #   clusters -- every cluster's code points, as a mutable list, in order
    #   units    -- one list of cluster indices per tone-bearing unit, in
    #               order
    # A maximal run of adjacent vowel clusters is one unit (a diphthong is
    # one syllable); a cluster carrying a syllabic mark is its own unit; a
    # modifier letter (category Lm, e.g. the length mark ː) is transparent,
    # neither starting a unit nor breaking a vowel run; anything else breaks
    # a vowel run without starting a unit. Mirrors diacritics2chao.py's
    # _tone_bearing_units(), but keeps cluster positions so a tone diacritic
    # can be placed back onto them.
    clusters = []
    units = []
    current_run = None
    for cluster in regex.findall(r'\X', word):
        index = len(clusters)
        clusters.append(list(cluster))
        base = cluster[0]
        if any(mark in SYLLABIC_MARKS for mark in cluster[1:]):
            if current_run is not None:
                units.append(current_run)
                current_run = None
            units.append([index])
        elif base in TONE_BEARING_VOWELS:
            if current_run is None:
                current_run = []
            current_run.append(index)
        elif unicodedata.category(base) == 'Lm':
            pass
        elif current_run is not None:
            units.append(current_run)
            current_run = None
    if current_run is not None:
        units.append(current_run)
    return clusters, units


def _place_word(word, tone_group_string):
    # Places tone_group_string's space-separated groups onto word's
    # tone-bearing units, one group per unit in order. Returns None if the
    # group count doesn't match the unit count, or a group doesn't fit any
    # of the placement rules below.
    clusters, units = _word_units(word)
    groups = tone_group_string.split(' ')
    if len(groups) != len(units):
        return None
    for unit_indices, group in zip(units, groups):
        unit_size = len(unit_indices)
        if unit_size == 1 and group in CHAO_LETTERS_TO_TONE_DIACRITIC:
            # A single tone-bearing cluster: the whole group is one diacritic.
            clusters[unit_indices[0]].append(CHAO_LETTERS_TO_TONE_DIACRITIC[group])
        elif len(group) == 1:
            # A level tone spread over several vowels repeats on each.
            diacritic = CHAO_LETTERS_TO_TONE_DIACRITIC[group]
            for index in unit_indices:
                clusters[index].append(diacritic)
        elif len(group) == unit_size:
            # One tone letter per vowel: one diacritic per cluster, in order.
            diacritics = []
            for letter in group:
                if letter not in CHAO_LETTERS_TO_TONE_DIACRITIC:
                    return None
                diacritics.append(CHAO_LETTERS_TO_TONE_DIACRITIC[letter])
            for index, diacritic in zip(unit_indices, diacritics):
                clusters[index].append(diacritic)
        else:
            return None
    return ''.join(''.join(cluster) for cluster in clusters)


def chao_letters_to_tone_diacritics(base_text, tone_letters):
    # The placement engine, counterpart of diacritics2chao.py's
    # tone_diacritics_to_chao_letters(): places tone_letters back onto
    # base_text's tone-bearing units, word by word. Returns None if the
    # words and tone groups don't correspond 1:1, or a word's groups don't
    # fit its units -- useful on its own when spelling and tone letters
    # already come from two separate fields (e.g. a FlexTools module reading
    # spelling and Pitch).
    tone_word_groups = regex.split(r' {2,}', tone_letters) if tone_letters else []
    base_decomposed = unicodedata.normalize('NFD', base_text)
    tokens = regex.split(r'(\s+)', base_decomposed)
    word_indices = [
        index for index, token in enumerate(tokens)
        if token != '' and not token.isspace()
    ]
    if len(word_indices) != len(tone_word_groups):
        return None
    for token_index, tone_group in zip(word_indices, tone_word_groups):
        placed = _place_word(tokens[token_index], tone_group)
        if placed is None:
            return None
        tokens[token_index] = placed
    return unicodedata.normalize('NFC', ''.join(tokens))

def convert(input_string): # function is named "convert" so it can be used as an SIL Flex Process
    match = _SPLIT_RE.match(input_string)
    if not match:
        return input_string
    placed = chao_letters_to_tone_diacritics(match.group('base'), match.group('tones'))
    if placed is None:
        return input_string
    return placed


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Places Chao tone letters back onto their base text as tone diacritics"""
    parser = argparse.ArgumentParser(
        description="Place Chao tone letters back onto their base text as "
                    "tone diacritics, e.g. nəjɛt ˨ ˨˧ -> nə̀jɛ᷅t.")
    parser.add_argument("text", nargs="*",
                        help="the text to convert; with no text given, lines "
                             "are read from standard input instead")
    args = parser.parse_args()
    return args

def use_utf8(*streams):
    # The output is IPA text with tone diacritics, so don't leave the
    # encoding to the console code page (which is not UTF-8 by default on
    # Windows)
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
