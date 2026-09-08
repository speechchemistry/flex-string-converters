#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   CV pattern from a phoneme string
#
#   Turns a phonemic or phonetic transcription into its CV pattern, e.g.
#   nə̀jɛt -> CVCVC. Language-universal: no per-language configuration. See
#   cv-patterns/SPEC.md for the full transform rules and their derivation from
#   CLTS's BIPA transcription system.
#
#   Tim Kempton
#   September 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import argparse
import unicodedata
import copy
from pathlib import Path

from csvw import TableGroup
from segments.tokenizer import Profile, Tokenizer

PROFILE_PATH = Path(__file__).resolve().parent / "cv_profile.tsv"

# The two special-value tokens the post-pass below acts on; every other
# non-space, non-"#" token in the tokenizer's output is already a plain "C" or
# "V" straight from the profile. See cv-patterns/SPEC.md's "The profile's
# three special values".
TIE = "TIE"
SYL = "SYL"

# The tokenizer's own word-boundary marker (Tokenizer.__call__'s default
# separator=' # ' joins per-word results with this), which the post-pass
# below turns back into a literal space -- see cv-patterns/SPEC.md's Verified
# mechanics.
WORD_BOUNDARY = "#"

REPLACEMENT_MARKER = "�"  # what segments' default error handler returns
UNKNOWN_SYMBOL = "?"


def _load_profile(path):
    # Profile.from_file() has no way to skip a leading comment block, since
    # its own default metadata sets no commentPrefix -- verified directly
    # against csvw's Table.iterdicts(), which does honour one. This replicates
    # Profile.from_file()'s own logic (including its NULL-to-None mapping)
    # with that one addition, so cv_profile.tsv can carry its own licence and
    # provenance header per AGENTS.md's External Specifications.
    metadata = copy.deepcopy(Profile.default_metadata(path))
    metadata["tables"][0]["dialect"]["commentPrefix"] = "#"
    # Declare the CV column too, so csvw doesn't warn about an "unspecified
    # column" on every load -- Profile.MD only declares Grapheme itself.
    metadata["tables"][0]["tableSchema"]["columns"].append(
        {"name": "CV", "datatype": "string"}
    )
    table_group = TableGroup.fromvalue(metadata)
    rows = [
        {
            key: (None if (key != Profile.GRAPHEME_COL and value == Profile.NULL) else value)
            for key, value in row.items()
        }
        for row in table_group.tables[0].iterdicts(fname=path)
    ]
    return Profile(*rows, fname=path, form="NFD")


_PROFILE = _load_profile(PROFILE_PATH)


def _reduce_word(tokens):
    # The post-pass a flat profile can't express by itself: a tie bar merges
    # the classes either side of it into one, and a syllabic mark promotes the
    # preceding C to V. Runs on one word's tokens (already NULL-filtered) at a
    # time, since a tie bar or syllabic mark never crosses a word boundary.
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == TIE:
            if result:
                result.pop()
            i += 1
            if i < len(tokens):
                result.append(tokens[i])
                i += 1
            continue
        if token == SYL:
            if result and result[-1] == "C":
                result[-1] = "V"
            i += 1
            continue
        result.append(token)
        i += 1
    return result


def Convert(input_string):  # function is named "Convert" so it can be used as an SIL Flex Process
    unrecognized = []

    def record_unrecognized(char):
        # Called by the tokenizer once per unmatched character (segments'
        # default replace() is called a second time on its own U+FFFD
        # placeholder while resolving the CV column -- see
        # cv-patterns/SPEC.md -- so only the first call, with a real input
        # character, is worth recording).
        if char != REPLACEMENT_MARKER:
            unrecognized.append(char)
        return REPLACEMENT_MARKER

    tokenizer = Tokenizer(_PROFILE, errors_replace=record_unrecognized)
    # The tokenizer's own form= parameter normalizes only its *output*, not
    # the word it matches against the (NFD) profile -- verified directly
    # against Tokenizer.__call__, which never normalizes its input. So the
    # input has to be NFD-normalised here, the same way diacritics2chao.py
    # already does.
    normalized = unicodedata.normalize("NFD", input_string)
    raw = tokenizer(normalized, column="CV")

    words = []
    current_word = []
    for token in raw.split():
        if token == WORD_BOUNDARY:
            words.append(current_word)
            current_word = []
        else:
            current_word.append(token)
    words.append(current_word)

    for char in unrecognized:
        print(
            f"phonemes2cv: unrecognized symbol {char!r} in {input_string!r}",
            file=sys.stderr,
        )

    patterns = []
    for tokens in words:
        reduced = _reduce_word(tokens)
        symbols = [
            UNKNOWN_SYMBOL if token == REPLACEMENT_MARKER else token
            for token in reduced
        ]
        if symbols:
            patterns.append("".join(symbols))
    return " ".join(patterns)


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Turns a phonemic or phonetic transcription into its CV pattern"""
    parser = argparse.ArgumentParser(
        description="Turn a phonemic or phonetic transcription into its CV "
                    "pattern, e.g. nə̀jɛt -> CVCVC.")
    parser.add_argument("text", nargs="*",
                        help="the text to convert; with no text given, lines "
                             "are read from standard input instead")
    args = parser.parse_args()
    if not args.text and sys.stdin.isatty():
        # Otherwise this looks like a hang: no arguments and no piped input
        # means there is nothing to read, so fail the way argparse already
        # fails a bad argument, rather than blocking on an interactive read.
        parser.error("no text given and standard input is a terminal; "
                     "pass text as arguments, or pipe/redirect input instead")
    return args

def use_utf8(*streams):
    # The input is IPA and the output is a CV pattern, so don't leave the
    # encoding to the console code page (which is not UTF-8 by default on
    # Windows)
    for stream in streams:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

def main():
    args = parse_arguments()
    use_utf8(sys.stdin, sys.stdout, sys.stderr)
    if args.text:
        lines = args.text
    else:
        lines = (line.rstrip("\n") for line in sys.stdin)
    for line in lines:
        print(Convert(line))

if __name__ == '__main__':
    main()
