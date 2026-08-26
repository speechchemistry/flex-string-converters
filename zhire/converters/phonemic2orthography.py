#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Zhire phonemic transcription to orthography
#
#   Turns a phonemic transcription into its Zhire orthographic spelling, per
#   the Zhire orthography statement's phoneme-to-grapheme correspondence
#   tables. Tone diacritics are stripped on the way, since the orthography
#   has no tone-marking convention yet. The segmental mapping itself is a
#   finite-state transducer built with pynini. See
#   plans/old/zhire-phonemic-to-orthography-fst.md for the design.
#
#   Tim Kempton
#   August 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import argparse
import unicodedata

import pynini


LENGTH_MARK = 'ː'  # ː
NASAL_TILDE = '̃'  # combining tilde

VOWELS = ['a', 'e', 'ɛ', 'ə', 'i', 'o', 'ɔ', 'u']

# Atomic consonants: one grapheme per phoneme, none decomposable further.
ATOMIC_CONSONANTS = {
    'b': 'b', 'd': 'd', 'f': 'f', 'ɡ': 'g', 'ɣ': 'gh', 'h': 'h', 'k': 'k',
    'x': 'kh', 'l': 'l', 'm': 'm', 'n': 'n', 'ŋ': 'ng',
    'p': 'p', 'r': 'r', 's': 's', 'ʃ': 'sh', 't': 't', 'v': 'v', 'w': 'w',
    'j': 'y', 'z': 'z', 'ʒ': 'zh',
}

# Sequences that can't be produced by concatenating the atomic consonants
# above -- see plans/old/zhire-phonemic-to-orthography-fst.md's "Overrides"
# section for why each one needs its own entry.
OVERRIDES = {
    'tʃ': 'c',
    'dʒ': 'j',
    # The prenasalised labial-velar. Its grapheme is ng + b, not ng + gb, so
    # unlike the other prenasalised consonants (mb, nd, ngg) it can't fall out
    # of concatenating its parts, which would give "ngmgb".
    'ŋmɡb': 'ngb',
    'hw': 'wh',
    'ɕw': 'why',
    'ʑw': 'yh',
}

# Alternate input notations accepted for a phoneme already in the tables
# above -- not distinct phonemes. [r] and [ɾ] are allophones and the data
# writes /r/, but the orthography statement's phoneme column uses /ɾ/, so
# both are accepted rather than erroring on the statement's own notation.
INPUT_VARIANTS = {
    'ɾ': 'r',
}


def _build_token_pairs():
    # The pairs deliberately carry no weight. Maximal munch -- preferring
    # dʒ -> j over d + ʒ -> dzh -- falls out of pynini.shortestpath on its
    # own: with every arc weighted equally it reaches the fewest-arc path
    # first, and fewest tokens across a fixed input length means longest
    # tokens. Weighting by token length would not help, and is the tempting
    # wrong fix: the input's length is the same however it is tokenised, so
    # every tokenisation would sum to the same weight.
    pairs = [(phoneme, phoneme) for phoneme in VOWELS]
    pairs += list(ATOMIC_CONSONANTS.items())
    pairs += list(OVERRIDES.items())
    pairs += list(INPUT_VARIANTS.items())
    pairs.append((' ', ' '))
    for vowel in VOWELS:
        pairs.append((vowel + NASAL_TILDE, vowel + NASAL_TILDE))
        pairs.append((vowel + LENGTH_MARK, vowel + vowel))
        pairs.append((vowel + NASAL_TILDE + LENGTH_MARK,
                      vowel + NASAL_TILDE + vowel + NASAL_TILDE))
    return pairs


_TOKEN_STAR = pynini.string_map(
    _build_token_pairs(), input_token_type="utf8", output_token_type="utf8"
).closure()


def _strip_tone_diacritics(input_string):
    # Delete every combining mark (Unicode category Mn) except the
    # nasalisation tilde, which orthography keeps. Operates on NFD so a
    # cluster's base letter and its combining marks are separate code
    # points. General by design: any tone diacritic, not just an
    # enumerated list, is stripped this way.
    decomposed = unicodedata.normalize('NFD', input_string)
    return ''.join(
        ch for ch in decomposed
        if ch == NASAL_TILDE or unicodedata.category(ch) != 'Mn'
    )


def convert(input_string): # function is named "convert" so it can be used as an SIL Flex Process
    tone_stripped = _strip_tone_diacritics(input_string)
    lattice = pynini.accep(tone_stripped, token_type="utf8") @ _TOKEN_STAR
    if lattice.start() == pynini.NO_STATE_ID or lattice.num_states() == 0:
        raise ValueError(f"no valid orthographic spelling for: {input_string!r}")
    output = pynini.shortestpath(lattice).string(token_type="utf8")
    return unicodedata.normalize('NFC', output)


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Converts a Zhire phonemic transcription to its orthographic spelling"""
    parser = argparse.ArgumentParser(
        description="Convert a Zhire phonemic transcription to its "
                    "orthographic spelling, e.g. hwōrì -> whori.")
    parser.add_argument("text", nargs="*",
                        help="the text to convert; with no text given, lines "
                             "are read from standard input instead")
    args = parser.parse_args()
    return args

def use_utf8(*streams):
    # The input is IPA and the output is Zhire orthography, so don't leave
    # the encoding to the console code page (which is not UTF-8 by default
    # on Windows)
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
