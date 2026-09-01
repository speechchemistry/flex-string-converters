# -*- coding: utf-8 -*-
#
#   CLI smoke tests for diacritics2chao_attached.py
#
#   No approval-fixture corpus here: this file has no transform logic of its
#   own, so a full fixture suite would only re-check diacritics2chao.py
#   --attached's own rules a second time. See test_diacritics2chao_attached.py
#   for the delegation tests and test_diacritics2chao.py for the rules
#   themselves.
#

import os
import pty
from pathlib import Path
import subprocess
import sys

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
REPO_ROOT = PROJECT_ROOT.parent
CONVERTER_PATH = PROJECT_ROOT / "converters" / "diacritics2chao_attached.py"


def test_stdin_line_converts_to_attached_output():
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH)],
        input="nə̀jɛ᷅t\n",
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
    )
    assert result.stderr == ""
    assert result.stdout == "nə˨jɛ˨˧t\n"


def test_argument_converts_to_attached_output():
    result = subprocess.run(
        [sys.executable, str(CONVERTER_PATH), "nə̀jɛ᷅t"],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
    )
    assert result.stderr == ""
    assert result.stdout == "nə˨jɛ˨˧t\n"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="pty is POSIX-only")
def test_no_arguments_and_no_piped_input_prints_usage_instead_of_hanging():
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
