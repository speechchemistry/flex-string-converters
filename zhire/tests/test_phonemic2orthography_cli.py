# -*- coding: utf-8 -*-
#
#   Approval tests for the phonemic2orthography.py command line interface
#
#   tests/fixtures/phonemic2orthography/inputs/words.txt is 99 real phonemic
#   transcriptions supplied by the language consultant (from
#   sample_phonemic2orthographic_data.csv), fed to the converter's CLI a line
#   at a time via stdin. Its stdout must match byte-for-byte the corresponding
#   tests/fixtures/phonemic2orthography/approved/words.approved.txt (compared
#   as decoded UTF-8 text, so only real content differences count, not
#   platform line endings). No scrubbing and no Unicode normalisation are
#   applied to either side: NFC output is itself part of what Convert()
#   guarantees, so normalising the comparison would hide a real regression.
#
#   A fixture with no approved file yet is not a test failure in the usual
#   sense: it is a first approval. The proposed output is written to
#   tests/fixtures/phonemic2orthography/received/ either way, and the failure
#   message gives the exact command to promote it once it has been read and
#   found correct. Nothing is ever written into approved/ automatically.
#

import os
import pty
from pathlib import Path
import subprocess
import sys

import pytest

from approval import REPO_ROOT, assert_approved, input_fixtures

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
CONVERTER_NAME = "phonemic2orthography"
CONVERTER_PATH = PROJECT_ROOT / "converters" / "phonemic2orthography.py"


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


@pytest.mark.skipif(sys.platform.startswith("win"), reason="pty is POSIX-only")
def test_no_arguments_and_no_piped_input_prints_usage_instead_of_hanging():
    # A real pseudo-terminal, so sys.stdin.isatty() is genuinely true, unlike
    # a pipe or /dev/null. The timeout is a safety net: if the fix regresses,
    # this fails fast rather than hanging the test run.
    controller_fd, terminal_fd = pty.openpty()
    try:
        result = subprocess.run(
            [sys.executable, str(CONVERTER_PATH)],
            stdin=terminal_fd,
            capture_output=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            timeout=5,
        )
    finally:
        os.close(controller_fd)
        os.close(terminal_fd)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr
