#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Zhire phonetic transcription to phonemic transcription
#
#   Turns a Zhire phonetic transcription into the phonemic transcription
#   that phonemic2orthography.convert() already accepts, so the two compose:
#   phonetic -> phonemic -> orthography. Implements the allophony and
#   notation rules of the Zhire phonology sketch (draft), checked against
#   246 real phonetic/phonemic word pairs. See
#   plans/old/zhire-phonetic-to-phonemic-fst.md for the design and the
#   evidence behind each rule.
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


# The sketch's 10 tone marks, kept as identity arcs -- tone stays in the
# phonemic form; stripping it is phonemic2orthography.py's job. Written as
# \uXXXX escapes rather than the bare combining characters, which render as
# invisible or unclear without a base letter to attach to.
TONE_MARKS = [
    '\u0300',  # grave
    '\u0301',  # acute
    '\u0302',  # circumflex
    '\u0304',  # macron
    '\u030C',  # caron
    '\u1DC4',  # macron-acute
    '\u1DC5',  # grave-macron
    '\u1DC6',  # macron-grave
    '\u1DC7',  # acute-macron
    '\u1DC8',  # grave-acute-grave
]
NASAL_TILDE = '\u0303'  # combining tilde
LENGTH_MARK = 'ː'  # U+02D0 -- a spacing modifier letter, not combining, so it renders fine on its own

VOWELS = ['a', 'e', 'ɛ', 'ə', 'i', 'o', 'ɔ', 'u']

# Atomic consonants: kept as themselves. Includes /l/ (a loanword phoneme,
# per phonemic2orthography.py) and /ɕ/, /ʑ/ (only ever preceding /w/ in
# attested data, but not decomposable further themselves).
ATOMIC_CONSONANTS = [
    'p', 'b', 't', 'd', 'k', 'ɡ', 'm', 'n', 'ŋ',
    'f', 'v', 's', 'z', 'ʃ', 'ʒ', 'x', 'ɣ', 'h', 'j', 'w',
    'ɕ', 'ʑ', 'l', 'r',
]

# Sequences that need their own entry rather than falling out of
# concatenating the atomic units above.
OVERRIDES = {
    'ɾ': 'r',      # variant assertion 1: [ɾ] and [r] are the same phoneme
    'ɲ': 'nj',     # variant assertion 5
    'nz': 'ndz',   # variant assertion 3, plain form, any position
    'ndʒ': 'ndz',  # variant assertion 4, plain form, any position
    'ɨ': 'ə',      # demonstrated by the sketch's own orthography chart
}

# Marks the phonemic level doesn't carry -- release detail, not structure.
# Deleted by name in a pre-pass, never by a Unicode-category rule, so
# raise-on-unknown still catches anything else. Deleting them in the FST
# itself as epsilon arcs was tried and rejected: a mark sitting inside a
# multi-character token (e.g. a combining tie bar, U+0361, between n and z
# as in a tie-barred "nz") blocks that token from matching, so the
# surrounding rule silently fails to fire.
RELEASE_MARKS = ('ʼ', '\u0361', 'ʰ')  # ejective, tie bar (U+0361), aspiration


def _strip_release_marks(input_string):
    for mark in RELEASE_MARKS:
        input_string = input_string.replace(mark, '')
    return input_string


def _build_token_pairs():
    # No weights: maximal munch (nz/ndʒ beating their single-character
    # parts) falls out of pynini.shortestpath on unweighted arcs -- see
    # zhire/converters/phonemic2orthography.py's build function for the
    # fuller explanation, which applies identically here.
    pairs = [(phoneme, phoneme) for phoneme in VOWELS]
    pairs += [(consonant, consonant) for consonant in ATOMIC_CONSONANTS]
    pairs += list(OVERRIDES.items())
    pairs.append((' ', ' '))
    for mark in TONE_MARKS:
        pairs.append((mark, mark))
    pairs.append((NASAL_TILDE, NASAL_TILDE))
    pairs.append((LENGTH_MARK, LENGTH_MARK))
    return pairs


_TOKEN_STAR = pynini.string_map(
    _build_token_pairs(), input_token_type="utf8", output_token_type="utf8"
).closure()


def convert(input_string): # function is named "convert" so it can be used as an SIL Flex Process
    decomposed = unicodedata.normalize('NFD', input_string)
    stripped = _strip_release_marks(decomposed)
    lattice = pynini.accep(stripped, token_type="utf8") @ _TOKEN_STAR
    if lattice.start() == pynini.NO_STATE_ID or lattice.num_states() == 0:
        raise ValueError(f"no valid phonemic transcription for: {input_string!r}")
    output = pynini.shortestpath(lattice).string(token_type="utf8")
    return unicodedata.normalize('NFC', output)


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Converts a Zhire phonetic transcription to its phonemic transcription"""
    parser = argparse.ArgumentParser(
        description="Convert a Zhire phonetic transcription to its "
                    "phonemic transcription, e.g. hwōrì -> hwōrì (unchanged) "
                    "or ɲápsə́ -> njápsə́.")
    parser.add_argument("text", nargs="*",
                        help="the text to convert; with no text given, lines "
                             "are read from standard input instead")
    args = parser.parse_args()
    return args

def use_utf8(*streams):
    # Both input and output are IPA, so don't leave the encoding to the
    # console code page (which is not UTF-8 by default on Windows)
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
