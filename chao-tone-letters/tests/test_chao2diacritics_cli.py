# -*- coding: utf-8 -*-
#
#   Approval tests for the chao2diacritics.py command line interface
#
#   Each file in tests/fixtures/chao2diacritics/inputs/ is fed to the
#   converter's CLI a line at a time via stdin, and its stdout must match
#   byte-for-byte the corresponding
#   tests/fixtures/chao2diacritics/approved/<stem>.approved.txt (compared as
#   decoded UTF-8 text, so only real content differences count, not
#   platform line endings). No scrubbing and no Unicode normalisation are
#   applied to either side: NFC output is itself part of what Convert()
#   guarantees, so normalising the comparison would hide a real regression.
#
#   Most of these input files are exactly diacritics2chao.py's own approved
#   outputs (see tests/fixtures/diacritics2chao/approved/), which makes this
#   a genuine round-trip regression net rather than a fresh set of guesses.
#
#   A fixture with no approved file yet is not a test failure in the usual
#   sense: it is a first approval. The proposed output is written to
#   tests/fixtures/chao2diacritics/received/ either way, and the failure
#   message gives the exact command to promote it once it has been read and
#   found correct. Nothing is ever written into approved/ automatically.
#

from pathlib import Path
import subprocess
import sys

import regex

import pytest

from approval import REPO_ROOT, assert_approved, input_fixtures

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
CONVERTER_NAME = "chao2diacritics"
CONVERTER_PATH = PROJECT_ROOT / "converters" / "chao2diacritics.py"


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

    # stderr carries the warnings, so it is no longer expected to be empty.
    # The approval artifact stays the stdout one; every stderr line must
    # still be a warning naming a line of this fixture, so a stray traceback
    # or debugging print cannot hide among them.
    for line in result.stderr.splitlines():
        assert regex.match(r"^chao2diacritics: line \d+: .+: '.*'$", line), line
    assert_approved(TESTS_DIR, CONVERTER_NAME, input_path, approved_path, result.stdout)


def test_stdout_carries_every_input_line_even_when_it_warns():
    # A table's column keeps all of its rows: a line that could not be placed
    # is written through unchanged rather than dropped.
    lines = ["ma\u02e6 ti\u02e6\u02e8", "ka\u02e8\u02e9", "cat"]
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH)],
        input="\n".join(lines) + "\n",
        capture_output=True, check=True, cwd=REPO_ROOT, encoding="utf-8",
    )
    assert len(result.stdout.splitlines()) == len(lines)
    assert result.stdout.splitlines()[1] == "ka\u02e8\u02e9"


def test_warnings_name_the_line_number_and_the_reason():
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH)],
        input="cat\nbjo sadu  \u02e7 \u02e8\nka\u02e8\u02e9\n",
        capture_output=True, check=True, cwd=REPO_ROOT, encoding="utf-8",
    )
    assert result.stderr.splitlines() == [
        "chao2diacritics: line 2: not converted: 2 detached tone letter groups "
        "for 3 unmarked syllables: 'bjo sadu  \u02e7 \u02e8'",
        "chao2diacritics: line 3: not converted: no tone diacritic for "
        "\u02e8\u02e9: 'ka\u02e8\u02e9'",
    ]


def test_exit_status_stays_zero_when_lines_warn():
    # Warnings are diagnostics, not failures: an existing pipeline that pipes
    # this converter must not start breaking because a line did not convert.
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH)],
        input="ka\u02e8\u02e9\n",
        capture_output=True, cwd=REPO_ROOT, encoding="utf-8",
    )
    assert result.returncode == 0
