# -*- coding: utf-8 -*-
#
#   Shared approval-testing harness for a converter's CLI
#
#   Lifted out of the diacritics2chao CLI test so a second converter's CLI
#   test doesn't duplicate the same harness. See AGENTS.md's Testing Approach
#   for what the approval-testing convention guarantees, and
#   tests/test_diacritics2chao_cli.py for the worked example that first
#   introduced it.
#
#   A fixture with no approved file yet is not a test failure in the usual
#   sense: it is a first approval. The proposed output is written to
#   tests/fixtures/<converter>/received/ either way, and the failure message
#   gives the exact command to promote it once it has been read and found
#   correct. Nothing is ever written into approved/ automatically.
#

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def fixtures_dir(converter_name):
    return REPO_ROOT / "tests" / "fixtures" / converter_name


def input_fixtures(converter_name):
    # A missing approved file is a first approval, not a collection error, so
    # pairing happens unconditionally; only a completely empty inputs
    # directory indicates a broken fixture set.
    fixtures = fixtures_dir(converter_name)
    input_files = sorted((fixtures / "inputs").glob("*.txt"))
    if not input_files:
        raise AssertionError(f"No input fixtures found in {fixtures / 'inputs'}")
    return [
        (input_path, fixtures / "approved" / f"{input_path.stem}.approved.txt")
        for input_path in input_files
    ]


def _promote_command(converter_name, input_path, received_path):
    approved_path = fixtures_dir(converter_name) / "approved" / f"{input_path.stem}.approved.txt"
    return (
        f"cp {received_path.relative_to(REPO_ROOT)} "
        f"{approved_path.relative_to(REPO_ROOT)}"
    )


def assert_approved(converter_name, input_path, approved_path, actual):
    received_dir = fixtures_dir(converter_name) / "received"
    received_dir.mkdir(parents=True, exist_ok=True)
    received_path = received_dir / f"{input_path.stem}.received.txt"

    if not approved_path.exists():
        received_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"No approved output yet for {input_path.name}. "
            f"Review {received_path}, then promote it once it's correct:\n"
            f"  {_promote_command(converter_name, input_path, received_path)}"
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
            f"  {_promote_command(converter_name, input_path, received_path)}"
        )

    if received_path.exists():
        received_path.unlink()
