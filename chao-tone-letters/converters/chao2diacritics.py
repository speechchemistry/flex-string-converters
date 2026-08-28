#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Tone diacritics from Chao tone letters
#
#   Reverses converters/diacritics2chao.py: given text carrying Chao tone
#   letters, places tone diacritics back onto the tone-bearing units they
#   belong to. Where the tone letters sit does not matter -- attached to
#   their syllable (ma˦ ti˦˨), gathered into a trailing section
#   (ma ti ˦  ˦˨), pre-posed, or a mixture -- so a spreadsheet or shell
#   pipeline that mangles the spacing cannot change the reading.
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

# The five level tone letters (U+02E5-U+02E9) a contour is written from, and
# the 13 tone diacritics they map to -- the latter only so that base text
# which is already half converted can be reported rather than doubly marked.
TONE_LETTERS = frozenset('˥˦˧˨˩')
TONE_DIACRITICS = frozenset(CHAO_LETTERS_TO_TONE_DIACRITIC.values())


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
    clusters, units, _, _ = _scan(word)
    return clusters, units


def _scan(text):
    # Walk the whole (NFD-normalised) text once by grapheme cluster. Returns:
    #   clusters     -- every cluster's code points, as a mutable list
    #   units        -- one list of cluster indices per tone-bearing unit
    #   groups       -- one [letters, unit_or_None] per run of adjacent tone
    #                   letters: the unit it is attached to, or None if it
    #                   stands free
    #   tone_indices -- the cluster indices holding those tone letters
    #
    # A tone letter run is *attached* when it immediately follows a unit in
    # the same word, reaching back over a coda consonant so that mat˦ marks
    # the a; it is *free* when whitespace or the start of a word precedes it.
    # Chao tone letters are Unicode category Sk rather than Lm, so the
    # segmentation rules below already treat one as breaking a vowel run.
    clusters, units, groups, tone_indices = [], [], [], []
    current_run = None
    last_unit = None      # the unit an attached group could still bind to
    open_group = None     # index into groups, while a run of tone letters is open

    def close_run():
        nonlocal current_run, last_unit
        if current_run is not None:
            units.append(current_run)
            last_unit = len(units) - 1
            current_run = None

    for cluster in regex.findall(r'\X', text):
        index = len(clusters)
        clusters.append(list(cluster))
        base = cluster[0]
        if base in TONE_LETTERS:
            close_run()
            if open_group is not None:
                groups[open_group][0] += base   # still the same contour
            else:
                groups.append([base, last_unit])
                open_group = len(groups) - 1
            tone_indices.append(index)
            continue
        open_group = None                       # any other cluster ends the run
        if base.isspace():
            close_run()
            last_unit = None                    # no attaching across whitespace
        elif any(mark in SYLLABIC_MARKS for mark in cluster[1:]):
            close_run()
            units.append([index])
            last_unit = len(units) - 1
        elif base in TONE_BEARING_VOWELS:
            if current_run is None:
                current_run = []
                last_unit = None                # a new unit has opened
            current_run.append(index)
        elif unicodedata.category(base) == 'Lm':
            pass
        else:
            close_run()
    close_run()
    return clusters, units, groups, tone_indices


def _place(clusters, unit_indices, letters):
    # Places one tone-letter group onto one tone-bearing unit of unit_indices
    # clusters. Returns False if the group fits none of the three rules.
    unit_size = len(unit_indices)
    if unit_size == 1 and letters in CHAO_LETTERS_TO_TONE_DIACRITIC:
        # A single tone-bearing cluster: the whole group is one diacritic.
        clusters[unit_indices[0]].append(CHAO_LETTERS_TO_TONE_DIACRITIC[letters])
    elif len(letters) == 1:
        # A level tone spread over several vowels repeats on each.
        if letters not in CHAO_LETTERS_TO_TONE_DIACRITIC:
            return False
        diacritic = CHAO_LETTERS_TO_TONE_DIACRITIC[letters]
        for index in unit_indices:
            clusters[index].append(diacritic)
    elif len(letters) == unit_size:
        # One tone letter per vowel: one diacritic per cluster, in order.
        diacritics = []
        for letter in letters:
            if letter not in CHAO_LETTERS_TO_TONE_DIACRITIC:
                return False
            diacritics.append(CHAO_LETTERS_TO_TONE_DIACRITIC[letter])
        for index, diacritic in zip(unit_indices, diacritics):
            clusters[index].append(diacritic)
    else:
        return False
    return True


def _drop_orphaned_space(clusters):
    # A whitespace run that separated tone letters from the rest is noise once
    # they are gone. Drop a run only where the removal leaves no surviving
    # text on one side of it, so the space inside "ma˦ ti˦˨" is kept but the
    # one before a trailing tone section is not.
    surviving = [bool(cluster) and not ''.join(cluster).isspace()
                 for cluster in clusters]
    text_follows = [False] * (len(clusters) + 1)
    for index in range(len(clusters) - 1, -1, -1):
        text_follows[index] = text_follows[index + 1] or surviving[index]
    text_precedes = False
    for index, cluster in enumerate(clusters):
        if surviving[index]:
            text_precedes = True
        elif cluster and ''.join(cluster).isspace():
            if not text_precedes or not text_follows[index + 1]:
                clusters[index] = []


def _plural(count, noun):
    return '%d %s%s' % (count, noun, '' if count == 1 else 's')


def _engine(text):
    # The placement engine. Returns (result, warnings), where result is None
    # when the line could not be placed and the caller should leave it alone.
    decomposed = unicodedata.normalize('NFD', text)
    clusters, units, groups, tone_indices = _scan(decomposed)
    if not groups:
        return decomposed, []                   # nothing to re-attach

    warnings = []
    attached = [group for group in groups if group[1] is not None]
    free = [group for group in groups if group[1] is None]

    if any(mark in TONE_DIACRITICS for mark in decomposed):
        # Placing on top of an existing diacritic gives a doubly marked vowel.
        warnings.append('base text already carries a tone diacritic')
    if attached and free:
        # A free group can reach back past a syllable an attached one claimed.
        warnings.append('line mixes attached and detached tone letters')

    marked = set()
    for letters, unit in attached:
        if unit in marked:
            warnings.append('not converted: two tone letter groups on one syllable')
            return None, warnings
        marked.add(unit)

    unmarked = [unit for unit in range(len(units)) if unit not in marked]
    if free:
        # Position is a detached group's only clue to which syllable it means,
        # so a partial fill would have to guess. Require an exact match.
        if len(free) != len(unmarked):
            warnings.append('not converted: %s for %s'
                            % (_plural(len(free), 'detached tone letter group'),
                               _plural(len(unmarked), 'unmarked syllable')))
            return None, warnings
        for group, unit in zip(free, unmarked):
            group[1] = unit
    elif unmarked:
        # Attached marking may be partial, but a dropped tone letter looks the
        # same as a genuinely toneless syllable, so say so.
        warnings.append('%d of %s not marked by an attached tone letter'
                        % (len(unmarked), _plural(len(units), 'syllable')))

    for letters, unit in groups:
        if not _place(clusters, units[unit], letters):
            warnings.append('not converted: no tone diacritic for ' + letters)
            return None, warnings

    for index in tone_indices:
        clusters[index] = []
    _drop_orphaned_space(clusters)
    return ''.join(''.join(cluster) for cluster in clusters), warnings


def chao_letters_to_tone_diacritics(base_text, tone_letters):
    # Places tone_letters onto base_text's tone-bearing units. Returns None
    # if they don't correspond -- useful on its own when spelling and tone
    # letters already come from two separate fields (e.g. a FlexTools module
    # reading spelling and Pitch).
    combined = base_text + '  ' + tone_letters if tone_letters else base_text
    result, _ = _engine(combined)
    return None if result is None else unicodedata.normalize('NFC', result)


def convert_with_warnings(input_string):
    # Convert(), plus the reasons a line was left alone or is suspicious.
    # Kept separate so that Convert() itself writes nothing anywhere: it runs
    # unchanged as an SIL FLEx Process, and a FlexTools module wrapping it
    # must report through the report object rather than print.
    result, warnings = _engine(input_string)
    if result is None:
        return input_string, warnings
    return unicodedata.normalize('NFC', result), warnings

def Convert(input_string): # function is named "Convert" so it can be used as an SIL Flex Process
    return convert_with_warnings(input_string)[0]


#----------------------------------------------------------------
# Command line interface

def parse_arguments():
    """Places Chao tone letters back onto their base text as tone diacritics"""
    parser = argparse.ArgumentParser(
        description="Place Chao tone letters back onto their base text as "
                    "tone diacritics, e.g. nəjɛt ˨ ˨˧ -> nə̀jɛ᷅t. The tone "
                    "letters may be attached to their syllable, gathered "
                    "into a section before or after the text, or a mixture.")
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
    use_utf8(sys.stdin, sys.stdout, sys.stderr)
    if args.text:
        lines = args.text
    else:
        lines = (line.rstrip("\n") for line in sys.stdin)
    for number, line in enumerate(lines, start=1):
        # Results go to stdout and diagnostics to stderr, and every line is
        # written whether or not it converted, so a column of a table keeps
        # all of its rows.
        converted, warnings = convert_with_warnings(line)
        print(converted)
        for warning in warnings:
            print("chao2diacritics: line %d: %s: %r" % (number, warning, line),
                  file=sys.stderr)

if __name__ == '__main__':
    main()
