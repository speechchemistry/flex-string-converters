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
#   PROVISIONAL: this is the first converter in this repository that imports
#   another converter, since every other one is deliberately self-contained
#   so it can stand alone as a FLEx Process. The sys.path technique below
#   mirrors the one already proven for a FlexTools module reaching its
#   project's converters/ (see AGENTS.md's FlexTools Module Conventions),
#   but whether a raw FLEx Process resolves this import the same way has not
#   been verified against real FieldWorks. Smoke-test this against a real
#   FLEx Process before relying on it.
#
#   Tim Kempton
#   September 2026
#
#   Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)
#

import sys
import argparse
import os

# diacritics2chao.py lives in this same converters/ directory. A FLEx
# Process, like FlexTools, is expected to import a script by file path,
# which does not put the script's own folder on sys.path, so it is added
# explicitly here -- see the header comment above.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diacritics2chao


def Convert(input_string): # function is named "Convert" so it can be used as an SIL Flex Process
    return diacritics2chao.Convert(input_string, attached=True)


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Converts tone diacritics to Chao tone letters attached to their syllable"""
    parser = argparse.ArgumentParser(
        description="Convert tone diacritics to Chao tone letters attached "
                    "to the syllable they mark, e.g. nə̀jɛ᷅t -> nə˨jɛ˨˧t. "
                    "Equivalent to diacritics2chao.py --attached; see that "
                    "script for the trailing-section form.")
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
        print(Convert(line))

if __name__ == '__main__':
    main()
