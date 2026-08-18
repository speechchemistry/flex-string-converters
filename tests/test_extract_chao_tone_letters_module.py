# -*- coding: utf-8 -*-
#
#   Tests for the Extract Chao tone letters FlexTools module
#
#   MainFunction needs a live FLEx project, so these drive it with fake
#   project and report objects instead. That covers the decisions the module
#   makes around the write -- which is where LexiconAddTagToField failed.
#

import pytest


VERN_WS = "qaa-x-test"
VERN_WS_NAME = "Test Vernacular"
PITCH_FIELD = 12345          # flexlibs field IDs are integers


class FakeReport(object):
    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []
        self.progress = []

    def Info(self, message):
        self.infos.append(message)

    def Warning(self, message):
        self.warnings.append(message)

    def Error(self, message):
        self.errors.append(message)

    def ProgressStart(self, total):
        self.progress.append(("start", total))

    def ProgressUpdate(self, value):
        self.progress.append(("update", value))

    @property
    def text(self):
        return "\n".join(self.infos)


class FakeProject(object):
    def __init__(self, forms, pitchField=PITCH_FIELD, fieldType="multi"):
        self._forms = list(forms)
        self._pitchField = pitchField
        self._fieldType = fieldType      # "string", "multi" or "other"
        self.writes = []             # (entry, field, text, ws)
        self.tagCalls = []           # LexiconAddTagToField must stay unused

    # --- the helpers the module reads through ---

    def LexiconGetEntryCustomFieldNamed(self, fieldName):
        return self._pitchField if fieldName == "Pitch" else None

    def LexiconNumberOfEntries(self):
        return len(self._forms)

    def LexiconAllEntries(self):
        # Entries are opaque to the module; their index stands in for one
        return list(range(len(self._forms)))

    def LexiconGetLexemeForm(self, entry):
        return self._forms[entry]

    def GetDefaultVernacularWS(self):
        return (VERN_WS, VERN_WS_NAME)

    def LexiconFieldIsStringType(self, fieldID):
        return self._fieldType == "string"

    def LexiconFieldIsAnyStringType(self, fieldID):
        return self._fieldType in ("string", "multi")

    def LexiconFieldIsMultiType(self, fieldID):
        # Reproduces the flexlibs bug: this helper reads FLExLCM.CellarMultiTypes,
        # which FLExLCM never defines, so it raises for every field
        raise AttributeError(
            "module 'flexlibs.code.FLExLCM' has no attribute 'CellarMultiTypes'")

    # --- the helpers the module writes through ---

    def LexiconSetFieldText(self, entry, fieldID, text, languageTagOrHandle=None):
        self.writes.append((entry, fieldID, text, languageTagOrHandle))

    def LexiconAddTagToField(self, entry, fieldID, tag):
        self.tagCalls.append((entry, fieldID, tag))


def run(chao_module, project, modifyAllowed=True):
    report = FakeReport()
    chao_module.MainFunction(project, report, modifyAllowed)
    return report


def test_dry_run_writes_nothing(chao_module):
    project = FakeProject(["nə̀jɛ᷅t", "ǒlō"])

    report = run(chao_module, project, modifyAllowed=False)

    assert project.writes == []
    # ...but the conversions are still reported, so a preview stays useful
    assert "nə̀jɛ᷅t -> ˨ ˨˧" in report.text
    # and the run says plainly that it wrote nothing
    assert "[DRY RUN] Writing Pitch in the %s writing system" % VERN_WS_NAME in report.text
    assert "[DRY RUN] Would write Pitch for 2 of 2 entries" in report.text


def test_writes_converted_text_in_the_vernacular_writing_system(chao_module):
    project = FakeProject(["nə̀jɛ᷅t"])

    run(chao_module, project, modifyAllowed=True)

    assert project.writes == [(0, PITCH_FIELD, "˨ ˨˧", VERN_WS)]


def test_does_not_use_the_broken_add_tag_helper(chao_module):
    # LexiconAddTagToField reads the field back with no writing system, which
    # raises AttributeError on a MultiUnicode custom field such as Pitch
    project = FakeProject(["nə̀jɛ᷅t", "ǒlō"])

    run(chao_module, project, modifyAllowed=True)

    assert project.tagCalls == []


def test_entries_without_tone_marks_are_left_alone(chao_module):
    # Overwriting with an empty string would wipe a Pitch value entered by hand
    project = FakeProject(["cat", "nə̀jɛ᷅t", ""])

    report = run(chao_module, project, modifyAllowed=True)

    assert project.writes == [(1, PITCH_FIELD, "˨ ˨˧", VERN_WS)]
    # the summary has to say what *was* written, not only what was skipped
    assert "Wrote Pitch for 1 of 3 entries" in report.text
    assert "left 2 unchanged (no tone marks found)" in report.text


def test_missing_pitch_field_reports_an_error_and_writes_nothing(chao_module):
    project = FakeProject(["nə̀jɛ᷅t"], pitchField=None)

    report = run(chao_module, project, modifyAllowed=True)

    assert report.errors == ["The entry-level Pitch field is missing"]
    assert project.writes == []
    # degraded to read-only, not aborted: conversions are still reported
    assert "nə̀jɛ᷅t -> ˨ ˨˧" in report.text


def test_reports_the_writing_system_it_writes_to(chao_module):
    # A wrong writing system stores text the field never displays, which looks
    # exactly like a no-op, so the run has to say which one it used
    project = FakeProject(["nə̀jɛ᷅t"])

    report = run(chao_module, project, modifyAllowed=True)

    assert VERN_WS_NAME in report.text


@pytest.mark.parametrize("fieldType, expected", [
    ("multi", "The Pitch field is a MultiUnicode or MultiString field"),
    ("string", "The Pitch field is a String field"),
    ("other", "The Pitch field is not a text field"),
])
def test_reports_the_pitch_field_type(chao_module, fieldType, expected):
    # The field's type decides whether LexiconAddTagToField would have worked
    project = FakeProject(["nə̀jɛ᷅t"], fieldType=fieldType)

    report = run(chao_module, project, modifyAllowed=True)

    assert expected in report.text


def test_field_type_is_unknown_when_the_helpers_are_missing(chao_module):
    # Older versions of flexlibs have no field type helpers at all
    class OlderFlexlibsProject(FakeProject):
        def LexiconFieldIsStringType(self, fieldID):
            raise AttributeError("LexiconFieldIsStringType")

        def LexiconFieldIsAnyStringType(self, fieldID):
            raise AttributeError("LexiconFieldIsAnyStringType")

    project = OlderFlexlibsProject(["nə̀jɛ᷅t"])

    report = run(chao_module, project, modifyAllowed=True)

    assert "The type of the Pitch field could not be determined" in report.text
    # a missing diagnostic must not stop the real work
    assert project.writes == [(0, PITCH_FIELD, "˨ ˨˧", VERN_WS)]


def test_progress_is_reported_over_all_entries(chao_module):
    project = FakeProject(["nə̀jɛ᷅t", "ǒlō", "cat"])

    report = run(chao_module, project, modifyAllowed=True)

    assert ("start", 3) in report.progress
    assert len([p for p in report.progress if p[0] == "update"]) == 3
