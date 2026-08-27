# -*- coding: utf-8 -*-
#
#   Approval tests for the phonetic2phonemic.py command line interface
#
#   Two of the fixtures are specification-derived, so the promote loop is
#   wrong for them -- their approved sides come from independent sources,
#   not from running the converter -- and one is an ordinary promote-loop
#   fixture:
#
#   - tests/fixtures/phonetic2phonemic/inputs/phonology_sketch_examples.txt
#     is the phonetic example word from each row of the phonology sketch's
#     three orthography charts (47 rows), with the sketch's own modifier
#     letters (ʷ ʲ ᵐ ⁿ ᵑ) transliterated to plain notation since convert()
#     rejects that notation outright. Its approved file is derived directly
#     from the plan's rule table, independently of the converter.
#
#   - tests/fixtures/phonetic2phonemic/inputs/real_flex_export.txt is all
#     246 rows of a real FLEx export (phonetic2phonemic_public_test.csv,
#     columns 3-4), with the one annotation-noise row's "**" stripped.
#     Its approved file is the export's own phonemic ("emic") column --
#     independently elicited ground truth, not the converter's own output.
#     6 rows are known mismatches (kept deliberately, not held out -- see
#     the plan) and will always fail until their FLEx entries are corrected.
#
#   - tests/fixtures/phonetic2phonemic/inputs/phonology_sketch_words.txt is
#     a breadth net: the sketch's other bracketed example forms, an
#     ordinary promote-loop fixture with no independent ground truth.
#
#   tests/fixtures/phonetic2phonemic/inputs/*.txt are fed to the converter's
#   CLI a line at a time via stdin. Its stdout must match byte-for-byte the
#   corresponding approved/*.approved.txt (compared as decoded UTF-8 text,
#   so only real content differences count, not platform line endings). No
#   scrubbing and no Unicode normalisation are applied to either side: NFC
#   output is itself part of what convert() guarantees, so normalising the
#   comparison would hide a real regression.
#
#   A fixture with no approved file yet is not a test failure in the usual
#   sense: it is a first approval. The proposed output is written to
#   tests/fixtures/phonetic2phonemic/received/ either way, and the failure
#   message gives the exact command to promote it once it has been read and
#   found correct. Nothing is ever written into approved/ automatically.
#

from pathlib import Path
import subprocess
import sys

import pytest

from approval import REPO_ROOT, assert_approved, input_fixtures

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
CONVERTER_NAME = "phonetic2phonemic"
CONVERTER_PATH = PROJECT_ROOT / "converters" / "phonetic2phonemic.py"


def _assert_approved(input_path, approved_path, actual):
    assert_approved(TESTS_DIR, CONVERTER_NAME, input_path, approved_path, actual)


@pytest.mark.parametrize("input_path,approved_path", input_fixtures(TESTS_DIR, CONVERTER_NAME))
def test_stdin_lines_convert_to_approved_output(input_path, approved_path):
    # End-to-end CLI test: feed the fixture via stdin and assert stdout
    # matches the approved file, one converted line per input line.
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH)],
        input=input_path.read_text(encoding="utf-8"),
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
    )

    assert result.stderr == ""
    _assert_approved(input_path, approved_path, result.stdout)
