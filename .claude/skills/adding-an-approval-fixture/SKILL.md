---
name: adding-an-approval-fixture
description: Add a new approval-test fixture, or approve a changed one, for a converter's CLI output. Use when adding test coverage for realistic or hard-to-assert-inline converter output, or when a converter's output has intentionally changed and existing approved fixtures now need updating.
license: MIT
compatibility: any Python 3 environment with pytest installed; no FieldWorks or flextoolslib dependency
---

# Adding an approval fixture

This repository's approval tests compare a converter's command line stdout against a checked-in
"approved" file. See [AGENTS.md's Testing Approach section](../../../AGENTS.md#testing-approach) for
the conventions this procedure follows, and `tests/test_chao_tones_cli.py` with
`tests/fixtures/chao_tones/` for the worked example.

## Adding a brand new fixture

1. Decide which converter's test file it belongs to (e.g. `tests/test_chao_tones_cli.py`) and its
   fixture directory (e.g. `tests/fixtures/chao_tones/`).
2. Write the input as a plain `.txt` file under that converter's `inputs/` directory, one line of
   real input per line. Do not add comment lines or labels — the filename is the label, and every
   line must be real input the converter will actually see. Prefer attested real-world examples;
   when none exist yet, a linguistically plausible constructed example is fine, but name the file to
   say so (e.g. a `_simulated` suffix) — see [AGENTS.md's Testing Approach
   section](../../../AGENTS.md#testing-approach).
3. Take care with anything invisible or fragile in the file:
   - Keep whitespace-sensitive content *internal* to a line, never trailing — editors and review
     tooling routinely strip trailing whitespace.
   - Don't let an editor "clean up" or re-save the file in a way that silently re-normalises Unicode
     (e.g. NFC/NFD). If the fixture exists specifically to test normalisation behaviour, verify the
     bytes are still what you intended after saving.
   - Keep the file's own final newline, since the converter's CLI always emits one per line.
4. Run `python -m pytest`. With no approved file yet, the matching test fails on purpose — this is
   the TDD "red" step, not a bug — and writes the proposed output to
   `tests/fixtures/<converter>/received/<stem>.received.txt`. The failure message prints the exact
   `cp` command to promote it.
5. **Open and read the received file.** This is the step that makes the fixture worth anything: an
   approved file nobody looked at asserts nothing. Check it against the converter's `SPEC.md` entry,
   not just against what the code happens to currently do.
6. If it's correct, run the promote command from the failure message. Do not write or copy the
   approved file any other way — it must be produced by this loop, never hand-crafted.
7. Re-run `python -m pytest` and confirm it's green and the received file is gone.
8. Check the new example isn't a duplicate. If it's illustrating a rule that already has a general
   unit test in `tests/test_<name>.py` (e.g. "an unrelated diacritic survives in the base text"), it
   belongs *only* in the fixture — don't also add a unit test asserting the identical input/output
   pair the fixture now checks. See [AGENTS.md's Testing Approach
   section](../../../AGENTS.md#testing-approach) for why: the two layers are meant to cover different
   ground, not mirror each other.

## Approving a changed fixture

Same loop: change the input (or leave it, if the converter's behaviour itself changed), run
`python -m pytest`, read the mismatch reported in the received file and the failure message's diff
line, and promote only once the new output is confirmed correct — never on trust, and never in bulk.

## Adding approval testing to a converter for the first time

If the converter has no `tests/test_<name>_cli.py` yet, create one following
`tests/test_chao_accents_cli.py`'s shape: import `input_fixtures()` and `assert_approved()` from the
shared `tests/approval.py` harness (lifted out of the original `chao_tones` CLI test so a second
converter's CLI test doesn't duplicate the same ~100-line harness) rather than re-implementing fixture
pairing or promotion. Keep the CLI subprocess call's `encoding="utf-8"` explicit — not `text=True` —
since the locale code page can otherwise mangle non-ASCII output, and compare the approved file and the
actual output exactly, with no scrubbing and no Unicode normalisation, unless the converter's own
`SPEC.md` entry says otherwise.
