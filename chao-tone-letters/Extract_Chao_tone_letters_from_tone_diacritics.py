# -*- coding: utf-8 -*-
#
#   Extract Chao tone letters from tone diacritics
#
#   Goes through all the lexeme forms and extracts Chao tone letters (only)
#   from any tone diacritics and puts it into a Custom Pitch field
#
#   Tim Kempton
#   August 2024
#
#   Platforms: Python .NET and IronPython
#

from flextoolslib import *

# FlexTools imports this file by path, which doesn't put its folder on
# sys.path, so point Python at converters/ before importing the conversion
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "converters"))
from diacritics2chao import Convert

#----------------------------------------------------------------
# Documentation for the user:

docs = {FTM_Name       : "Extract Chao tone letters from tone diacritics and put in pitch field",
        FTM_Version    : 0.9,
        FTM_ModifiesDB : True,
        FTM_Synopsis   : "Extracts Chao tone letters (only) from any tone diacritics",
        FTM_Help       : None,
        FTM_Description:
"""
Goes through all the lexeme forms and puts the spelled form (with tone
diacritics stripped), followed by its Chao tone letters when it has any, into
a Custom Pitch field. You can use Bulk Edit Entries in Flex to move these to
the desired field.

Re-running replaces the Pitch value rather than adding to it. Only an entry
with a genuinely blank lexeme form is left alone; every other entry has its
Pitch value overwritten, including a Pitch value entered by hand.
""" }

#----------------------------------------------------------------
# Configuration

PITCH_FIELD_NAME = "Pitch"

# Pitch is a vernacular writing system field, but LexiconSetFieldText defaults
# to the analysis writing system, which would store text that the field never
# displays. None means the project's default vernacular writing system, which
# is also the one the lexeme form is read from; set a language tag here for a
# project whose Pitch field uses a different writing system.
PITCH_WS = None


def pitchWritingSystem(project):
    """
    Returns the (language tag, name) of the writing system to write Pitch in.
    """
    if PITCH_WS is None:
        return project.GetDefaultVernacularWS()
    return (PITCH_WS, PITCH_WS)


def describeFieldType(project, fieldID):
    """
    Returns a description of the custom field's type, for the report.

    The type decides how flexlibs can reach the field: LexiconAddTagToField
    reads the field back without a writing system, which raises AttributeError
    on a multi-string field, so this module writes with LexiconSetFieldText.

    LexiconFieldIsMultiType() is deliberately not used. In flexlibs 1.2.8 and
    flexlibs2 2.3.1 it reads FLExLCM.CellarMultiTypes, a name FLExLCM never
    defines, so it raises AttributeError for every field. Any field that is a
    string type but not a String is one of the multi-string types.
    """
    try:
        if project.LexiconFieldIsStringType(fieldID):
            return "The Pitch field is a String field"
        if project.LexiconFieldIsAnyStringType(fieldID):
            return "The Pitch field is a MultiUnicode or MultiString field"
        return "The Pitch field is not a text field"
    except AttributeError:
        # Older versions of flexlibs don't offer these helpers
        return "The type of the Pitch field could not be determined"


#----------------------------------------------------------------
# The main processing function

# contains code fragments by C D Farrow

def MainFunction(project, report, modifyAllowed):
    """
    This is the main processing function.

    """
    AddReportToField = modifyAllowed
    flagsField = project.LexiconGetEntryCustomFieldNamed(PITCH_FIELD_NAME)
    if AddReportToField and not flagsField:
        report.Error("The entry-level Pitch field is missing")
        AddReportToField = False

    if flagsField:
        report.Info(describeFieldType(project, flagsField))

    # Report the writing system: writing to the wrong one stores text that the
    # field never displays, which otherwise looks exactly like doing nothing
    pitchWS, pitchWSName = pitchWritingSystem(project)
    dryRun = "" if AddReportToField else "[DRY RUN] "
    report.Info("%sWriting Pitch in the %s writing system" % (dryRun, pitchWSName))

    report.Info("Lexicon contains:")
    numberEntries = project.LexiconNumberOfEntries()
    report.Info("    %d entries" % numberEntries)
    report.ProgressStart(numberEntries)

    converted = 0
    unchanged = 0
    for entryNumber, entry in enumerate(project.LexiconAllEntries()):
        report.ProgressUpdate(entryNumber)
        lexeme_form_itsstring = project.LexiconGetLexemeForm(entry)
        chao_letters = Convert(lexeme_form_itsstring)
        report.Info(lexeme_form_itsstring + " -> " + chao_letters)
        if not chao_letters:
            # Writing the empty result would clear a value entered by hand
            unchanged += 1
            continue
        converted += 1
        if AddReportToField:
            project.LexiconSetFieldText(entry, flagsField, chao_letters, pitchWS)

    # Say what was written as well as what was skipped: a large skipped count
    # on its own reads as though nothing was converted
    report.Info("%s%s Pitch for %d of %d entries; left %d unchanged "
                "(empty lexeme form)"
                % (dryRun,
                   "Wrote" if AddReportToField else "Would write",
                   converted, numberEntries, unchanged))

#----------------------------------------------------------------
# The name 'FlexToolsModule' must be defined like this:

FlexToolsModule = FlexToolsModuleClass(runFunction = MainFunction,
                                       docs = docs)
