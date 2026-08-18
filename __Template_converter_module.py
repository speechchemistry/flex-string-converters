# -*- coding: utf-8 -*-
#
#   Template converter module
#
#   A starting point for a FlexTools module that runs one converter over a
#   field of every entry. Copy it to <What_it_does>.py, change the marked
#   places, and delete this paragraph.
#
#   The leading __ keeps FlexTools from importing this file as a module of its
#   own: the scanner skips __-prefixed files before importing them. Copies must
#   therefore NOT start with __.
#
#   <Your name>
#   <Month Year>
#
#   Platforms: Python .NET and IronPython
#

from flextoolslib import *

# FlexTools imports this file by path, which doesn't put its folder on
# sys.path, so point Python at converters/ before importing the conversion
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "converters"))
from my_converter import convert        # <- your converters/my_converter.py

#----------------------------------------------------------------
# Documentation for the user:

docs = {FTM_Name       : "<What the module does>",
        FTM_Version    : 0.1,
        FTM_ModifiesDB : True,
        FTM_Synopsis   : "<One line shown in the module list>",
        FTM_Help       : None,
        FTM_Description:
"""
<What the module does, what it reads, what it writes, and what re-running it
does. Say plainly whether a second run replaces or accumulates.>
""" }

#----------------------------------------------------------------
# Configuration

TARGET_FIELD_NAME = "<Custom field to write>"

# LexiconSetFieldText defaults to the analysis writing system, which would
# store text that a vernacular field never displays. None means the project's
# default vernacular writing system, which is also the one the lexeme form is
# read from; set a language tag here for a field that uses another one.
TARGET_WS = None


def targetWritingSystem(project):
    """
    Returns the (language tag, name) of the writing system to write in.
    """
    if TARGET_WS is None:
        return project.GetDefaultVernacularWS()
    return (TARGET_WS, TARGET_WS)


#----------------------------------------------------------------
# The main processing function

def MainFunction(project, report, modifyAllowed):
    """
    This is the main processing function.
    """
    writeAllowed = modifyAllowed
    targetField = project.LexiconGetEntryCustomFieldNamed(TARGET_FIELD_NAME)
    if writeAllowed and not targetField:
        report.Error("The entry-level %s field is missing" % TARGET_FIELD_NAME)
        # Degrade to read-only rather than raising, so the run still reports
        writeAllowed = False

    # Report the writing system: writing to the wrong one stores text that the
    # field never displays, which otherwise looks exactly like doing nothing
    targetWS, targetWSName = targetWritingSystem(project)
    dryRun = "" if writeAllowed else "[DRY RUN] "
    report.Info("%sWriting %s in the %s writing system"
                % (dryRun, TARGET_FIELD_NAME, targetWSName))

    numberEntries = project.LexiconNumberOfEntries()
    report.Info("Lexicon contains %d entries" % numberEntries)
    report.ProgressStart(numberEntries)

    converted = 0
    unchanged = 0
    for entryNumber, entry in enumerate(project.LexiconAllEntries()):
        report.ProgressUpdate(entryNumber)
        source = project.LexiconGetLexemeForm(entry)
        result = convert(source)
        report.Info(source + " -> " + result)
        if not result:
            # Writing an empty result would clear a value entered by hand
            unchanged += 1
            continue
        converted += 1
        if writeAllowed:
            # LexiconSetFieldText, not LexiconAddTagToField: the latter reads
            # the field back with no writing system, which raises
            # AttributeError on a multi-string custom field
            project.LexiconSetFieldText(entry, targetField, result, targetWS)

    # Say what was written as well as what was skipped: a large skipped count
    # on its own reads as though nothing was converted
    report.Info("%s%s %s for %d of %d entries; left %d unchanged"
                % (dryRun,
                   "Wrote" if writeAllowed else "Would write",
                   TARGET_FIELD_NAME, converted, numberEntries, unchanged))

#----------------------------------------------------------------
# The name 'FlexToolsModule' must be defined like this:

FlexToolsModule = FlexToolsModuleClass(runFunction = MainFunction,
                                       docs = docs)
