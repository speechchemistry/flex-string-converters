# -*- coding: utf-8 -*-
#
#   Approval tests for the chao_tones.py command line interface
#
#   Each file in tests/fixtures/chao_tones/inputs/ is fed to the converter's
#   CLI a line at a time via stdin, and its stdout must match byte-for-byte
#   the corresponding tests/fixtures/chao_tones/approved/<stem>.approved.txt
#   (compared as decoded UTF-8 text, so only real content differences count,
#   not platform line endings). No scrubbing and no Unicode normalisation are
#   applied to either side: NFC/NFD handling is itself part of what convert()
#   guarantees, so normalising the comparison would hide a real regression.
#
#   A fixture with no approved file yet is not a test failure in the usual
#   sense: it is a first approval. The proposed output is written to
#   tests/fixtures/chao_tones/received/ either way, and the failure message
#   gives the exact command to promote it once it has been read and found
#   correct. Nothing is ever written into approved/ automatically.
#

import subprocess
import sys

import pytest

from approval import REPO_ROOT, assert_approved, input_fixtures

CONVERTER_NAME = "chao_tones"
CONVERTER_PATH = REPO_ROOT / "converters" / "chao_tones.py"
INPUTS_DIR = REPO_ROOT / "tests" / "fixtures" / CONVERTER_NAME / "inputs"
APPROVED_DIR = REPO_ROOT / "tests" / "fixtures" / CONVERTER_NAME / "approved"


def _assert_approved(input_path, approved_path, actual):
    assert_approved(CONVERTER_NAME, input_path, approved_path, actual)


@pytest.mark.parametrize("input_path,approved_path", input_fixtures(CONVERTER_NAME))
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


def test_arguments_convert_in_the_order_given():
    # Pins the argument-mode guarantee in SPEC.md's Command line paragraph,
    # reusing words.txt rather than adding a second artifact. words.txt must
    # stay free of blank lines: a blank argument converts to a blank line,
    # but argv can't carry a literal blank line the way stdin can.
    input_path = INPUTS_DIR / "words.txt"
    approved_path = APPROVED_DIR / "words.approved.txt"
    lines = input_path.read_text(encoding="utf-8").splitlines()

    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH), *lines],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
    )

    assert result.stderr == ""
    _assert_approved(input_path, approved_path, result.stdout)
