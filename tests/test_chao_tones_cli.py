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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONVERTER_PATH = REPO_ROOT / "converters" / "chao_tones.py"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "chao_tones"
INPUTS_DIR = FIXTURES_DIR / "inputs"
APPROVED_DIR = FIXTURES_DIR / "approved"
RECEIVED_DIR = FIXTURES_DIR / "received"


def _input_fixtures():
    # A missing approved file is a first approval, not a collection error, so
    # pairing happens unconditionally; only a completely empty inputs
    # directory indicates a broken fixture set.
    input_files = sorted(INPUTS_DIR.glob("*.txt"))
    if not input_files:
        raise AssertionError(f"No input fixtures found in {INPUTS_DIR}")
    return [
        (input_path, APPROVED_DIR / f"{input_path.stem}.approved.txt")
        for input_path in input_files
    ]


def _promote_command(input_path, received_path):
    approved_path = APPROVED_DIR / f"{input_path.stem}.approved.txt"
    return (
        f"cp {received_path.relative_to(REPO_ROOT)} "
        f"{approved_path.relative_to(REPO_ROOT)}"
    )


def _assert_approved(input_path, approved_path, actual):
    RECEIVED_DIR.mkdir(parents=True, exist_ok=True)
    received_path = RECEIVED_DIR / f"{input_path.stem}.received.txt"

    if not approved_path.exists():
        received_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"No approved output yet for {input_path.name}. "
            f"Review {received_path}, then promote it once it's correct:\n"
            f"  {_promote_command(input_path, received_path)}"
        )

    approved_text = approved_path.read_text(encoding="utf-8")
    if actual != approved_text:
        received_path.write_text(actual, encoding="utf-8")
        approved_lines = approved_text.splitlines()
        actual_lines = actual.splitlines()
        first_diff = next(
            (
                i
                for i in range(max(len(approved_lines), len(actual_lines)))
                if i >= len(approved_lines)
                or i >= len(actual_lines)
                or approved_lines[i] != actual_lines[i]
            ),
            0,
        )
        approved_line = (
            approved_lines[first_diff] if first_diff < len(approved_lines) else "<no line>"
        )
        actual_line = (
            actual_lines[first_diff] if first_diff < len(actual_lines) else "<no line>"
        )
        pytest.fail(
            f"Approval mismatch for {input_path.name} at line {first_diff + 1}.\n"
            f"  approved: {ascii(approved_line)}\n"
            f"  actual:   {ascii(actual_line)}\n"
            f"Approved file: {approved_path}. Review {received_path}, "
            f"then promote it if the change is intended:\n"
            f"  {_promote_command(input_path, received_path)}"
        )

    if received_path.exists():
        received_path.unlink()


@pytest.mark.parametrize("input_path,approved_path", _input_fixtures())
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
