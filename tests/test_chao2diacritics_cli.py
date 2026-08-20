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
#   applied to either side: NFC output is itself part of what convert()
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

import subprocess
import sys

import pytest

from approval import REPO_ROOT, assert_approved, input_fixtures

CONVERTER_NAME = "chao2diacritics"
CONVERTER_PATH = REPO_ROOT / "converters" / "chao2diacritics.py"


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
    assert_approved(CONVERTER_NAME, input_path, approved_path, result.stdout)
