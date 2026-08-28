# -*- coding: utf-8 -*-
#
#   Template converter module
#
#   A starting point for a FlexTools module that runs one converter over the
#   lexeme form of every entry and reports what it would produce. It writes
#   nothing and needs no custom field, so a fresh copy runs immediately
#   against any project. Copy it to <What_it_does>.py, change the marked
#   places, and delete this paragraph.
#
#   To write the result back into a custom field, see the "Writing the result
#   back" block below MainFunction and the worked example in
#   Extract_Chao_tone_letters_from_tone_diacritics.py.
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
# replace my_converter with your converter's module name e.g. from diacritics2chao import Convert
from my_converter import Convert

#----------------------------------------------------------------
# Documentation for the user:

docs = {FTM_Name       : "<What the module does>",
        FTM_Version    : 0.1,
        FTM_ModifiesDB : False,
        FTM_Synopsis   : "<One line shown in the module list>",
        FTM_Help       : None,
        FTM_Description:
"""
<What the module does.> Reports what <your converter> would produce for the
lexeme form of every entry. Writes nothing.
""" }

#----------------------------------------------------------------
# The main processing function

def MainFunction(project, report, modifyAllowed):
    """
    This is the main processing function.

    Read-only: modifyAllowed is unused because nothing is written.
    """
    # Report the writing system the lexeme forms are read from: a lexeme form
    # in the wrong writing system is the failure that looks most like a no-op
    vernWS, vernWSName = project.GetDefaultVernacularWS()
    report.Info("Reading lexeme forms in the %s writing system" % vernWSName)

    numberEntries = project.LexiconNumberOfEntries()
    report.Info("Lexicon contains %d entries" % numberEntries)
    report.ProgressStart(numberEntries)

    converted = 0
    for entryNumber, entry in enumerate(project.LexiconAllEntries()):
        report.ProgressUpdate(entryNumber)
        source = project.LexiconGetLexemeForm(entry)
        result = Convert(source)
        report.Info(source + " -> " + result)
        if result:
            converted += 1

    report.Info("Would produce a result for %d of %d entries"
                % (converted, numberEntries))

#----------------------------------------------------------------
# Writing the result back
#
# Uncomment and adapt this once the read-only report above looks right. See
# Extract_Chao_tone_letters_from_tone_diacritics.py for the full worked
# example. Three traps to know about, since each one fails silently:
#
# - LexiconSetFieldText defaults to the default *analysis* writing system, so
#   pass the writing system explicitly or the text lands where a vernacular
#   field never displays it.
# - LexiconAddTagToField reads the field back with no writing system and
#   raises AttributeError on a multi-string custom field, so don't use it.
# - Skip empty results, or a value the user typed into the field by hand gets
#   cleared.
#
# TARGET_FIELD_NAME = "<Custom field to write>"
#
# def MainFunction(project, report, modifyAllowed):
#     writeAllowed = modifyAllowed
#     targetField = project.LexiconGetEntryCustomFieldNamed(TARGET_FIELD_NAME)
#     if writeAllowed and not targetField:
#         report.Error("The entry-level %s field is missing" % TARGET_FIELD_NAME)
#         writeAllowed = False
#
#     targetWS, targetWSName = project.GetDefaultVernacularWS()
#     dryRun = "" if writeAllowed else "[DRY RUN] "
#     report.Info("%sWriting %s in the %s writing system"
#                 % (dryRun, TARGET_FIELD_NAME, targetWSName))
#
#     numberEntries = project.LexiconNumberOfEntries()
#     report.ProgressStart(numberEntries)
#
#     converted = 0
#     unchanged = 0
#     for entryNumber, entry in enumerate(project.LexiconAllEntries()):
#         report.ProgressUpdate(entryNumber)
#         source = project.LexiconGetLexemeForm(entry)
#         result = Convert(source)
#         report.Info(source + " -> " + result)
#         if not result:
#             unchanged += 1
#             continue
#         converted += 1
#         if writeAllowed:
#             project.LexiconSetFieldText(entry, targetField, result, targetWS)
#
#     report.Info("%s%s %s for %d of %d entries; left %d unchanged"
#                 % (dryRun, "Wrote" if writeAllowed else "Would write",
#                    TARGET_FIELD_NAME, converted, numberEntries, unchanged))
#
# Also set FTM_ModifiesDB to True in docs above once this is live.

#----------------------------------------------------------------
# The name 'FlexToolsModule' must be defined like this:

FlexToolsModule = FlexToolsModuleClass(runFunction = MainFunction,
                                       docs = docs)
