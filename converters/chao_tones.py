#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Chao tone letters from accent notation
#
#   Extracts Chao tone letters (only) from any accent notation. Shared by the
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
import re
import unicodedata
import regex


# The following find and replace function is by Darius Bacon
# from: https://stackoverflow.com/a/765835 CC-BY-SA
def multisub(subs, subject):
    "Simultaneously perform all substitutions on the subject string."
    pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
    substs = [s for p, s in subs]
    replace = lambda m: substs[m.lastindex - 1]
    return re.sub(pattern, replace, subject)

def convert(input_string): # function is named "convert" so it can be used as an SIL Flex Process
    # ensure string is decomposed into separate code points
    input_decomposed = unicodedata.normalize('NFD',input_string)
    # replace all possible accents with chao tone letters
    chao_in_text = multisub([('\u030B','˥'), # ő
                       ('\u0301','˦'), # ó
                       ('\u0304','˧'), # ō
                       ('\u0300','˨'), # ò
                       ('\u030F','˩'), # ȍ
                       ('\u030C','˨˦'), # ǒ trying to be more consistent than IPA chart
                       ('\u0302','˦˨'), # ô trying to be more consistent than IPA chart
                       ('\u1DC4','˧˦'), # o᷄ trying to be more consistent than IPA chart
                       ('\u1DC5','˨˧'), # o᷅ trying to be more consistent than IPA chart
                       ('\u1DC8','˨˦˨'), # o᷈ trying to be more consistent than IPA chart
                       ('\u1DC6','˧˨'), # o᷆
                       ('\u1DC7','˦˧'), # o᷇
                       ('\u1DC9','˦˨˦')], # o᷉
                       input_decomposed)
    # find any run of items that aren't a space or tone letter and replace it with a space
    # the six characters in the first part were suggested by ChatGPT
    chao_in_spaces = regex.sub(r'[^\s˥˦˧˨˩]+',' ',chao_in_text)
    # convert any three space runs between words to two space runs
    # (three spaces occur after any codas and before another word)
    chao_two_space_gaps = regex.sub(r'   ','  ',chao_in_spaces)
    # then just remove any initial whitespace
    no_leading_spaces = regex.sub(r'^\s+','',chao_two_space_gaps)
    # remove any leading whitespace
    output = regex.sub(r'\s+$','',no_leading_spaces)
    return output


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Extracts Chao tone letters (only) from any accent notation"""
    parser = argparse.ArgumentParser(
        description="Extract Chao tone letters (only) from any accent "
                    "notation, e.g. nə̀jɛ᷅t -> ˨ ˨˧.")
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
