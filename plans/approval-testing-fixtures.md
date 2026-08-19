# Approval testing with input/output fixture files for `converters/chao_tones.py`

Status: proposed 2026-08-19, implemented 2026-08-19.

## Context

Today the only tests for the Chao tone converter are inline parametrized assertions in
[tests/test_chao_tones.py](../tests/test_chao_tones.py) against `convert()` and
`extract_chao_letters()`. Two things are untested:

- **The command line interface.** `SPEC.md` guarantees stdin-filter behaviour, argument order, and
  UTF-8 I/O regardless of console encoding; nothing exercises any of it.
- **A corpus.** Adding a realistic multi-line sample today means hand-writing expected strings full
  of invisible combining marks — exactly the case [AGENTS.md's Testing
  Approach](../AGENTS.md#testing-approach) says to switch to approval testing for.

The user asked to explore the approval-testing setup used in
[audio_label_file_conversions](https://github.com/speechchemistry/audio_label_file_conversions),
which pairs `tests/fixtures/<conversion>/inputs/*` with `approved/*.approved.*` and writes
`received/*.received.*` on mismatch (Emily Bache style). This plan brings that layout and workflow
here, adapted from XML to line-based text — and, because plain text has no volatile metadata,
**without any of that repo's scrubbing or normalising**: the approved file and the converter's stdout
must match exactly.

Intended outcome: a growable corpus of `.txt` in/out pairs that reviewers read as data rather than as
Python string literals, covering the CLI end to end, with the existing inline tests kept as-is.

## Decisions taken

1. **Exact comparison, no scrubbing.** The reference repo scrubs `DATE`, `AUTHOR`, `URN` and
   annotation ids because EAF carries them; this converter's output is deterministic, so there is
   nothing to placeholder out and no canonicalisation step. In particular there is **no Unicode
   normalisation** in the comparison: NFC/NFD handling *is* the specified behaviour (`convert()`
   normalises to NFD, then recomposes to NFC), so normalising both sides would hide real regressions.
2. **No comment or label lines in the fixtures.** Every line is real input. The filename carries the
   label instead, so the corpus is split into several small, well-named files rather than one big one.
3. **The approved artifact is the converter's stdout**, so line N of the approved file is the result
   for line N of the input file. No side-by-side `input<TAB>output` table — that would stop being a
   golden master of the documented CLI.
4. **Compared as decoded UTF-8 text, not raw bytes.** `print()` emits `\r\n` on Windows, where
   FlexTools users are, and line endings are not specified behaviour in `SPEC.md`; a literal
   `read_bytes()` comparison would therefore pass on Linux and fail on Windows. Reading both sides as
   text with `encoding="utf-8"` needs no scrub code at all — Python's ordinary text mode handles it —
   and every character the converter is responsible for is still compared exactly.
5. **A new fixture with no approved file is a first approval, not an error.** Drop a `.txt` into
   `inputs/`, run pytest, and the test writes the proposed output to `received/` and fails with the
   exact command to promote it. So pytest is the only generator of approved files — nobody hand-runs a
   shell redirect, and an approved file is by construction literally what the test compares against.
   The run still fails until a human promotes the file, so nothing is ever auto-accepted.
6. **The promote command is the explicit accept step**, playing the role `testthat::snapshot_accept()`
   plays in `lexicon_file_conversions`. Review first, then promote — no `APPROVE=1` bulk switch, since
   per-file promotion keeps the received file in front of the reviewer, which is the point of the rule
   in both sibling repos.
7. **The existing inline tests stay.** `AGENTS.md` prefers small parametrized assertions while output
   is short strings; the approval layer covers the corpus and the CLI, not the unit rules.

## Alignment with the sibling repos

Two repos already do approval testing:
[audio_label_file_conversions](https://github.com/speechchemistry/audio_label_file_conversions)
(Python, hand-rolled `inputs/` + `approved/` + `received/`) and
[lexicon_file_conversions](https://github.com/speechchemistry/lexicon_file_conversions) (R, native
`testthat` snapshots). This plan follows the principles both share: fixtures grouped per script or
converter, approved artifacts stored as raw files with their real extension rather than wrapped in a
markdown fence, Emily Bache naming (the checked-in file is approved, the generated one is for review),
review before accepting, deterministic human-reviewable artifacts, and a README section documenting
the loop.

Where they differ, the choices here are deliberate:

- **Hand-rolled rather than framework-native.** The R repo delegates to `testthat::expect_snapshot_file()`
  because `testthat` ships snapshots; pytest ships nothing equivalent, so the Python sibling hand-rolls
  the loop and this repo follows it. That also keeps `inputs/` + `approved/` identical across the two
  Python repos, and adds no dependency to a repo that has no `pyproject.toml` and is installed by
  copying a checkout. A library (`syrupy`, `pytest-regressions`, `approvaltests`) would own the
  approved artifacts' location instead, diverging from that convention.
- **A missing approved file fails rather than warns.** `expect_snapshot_file()` auto-creates a snapshot
  on first run with a WARN, which is why the R repo's `AGENTS.md` has to caution that such a file "is
  just whatever the current code happens to output, not a vetted-correct baseline". Here nothing is
  ever written into `approved/` automatically: the run fails with the proposed output in `received/`,
  so the only way into `approved/` is a human promoting a file.
- **Record the traps, as the R repo does.** Its `AGENTS.md` documents `NOT_CRAN`, testthat's 3rd
  edition and the trailing-slash `snapshot_accept()` that silently no-ops — all cases where a run looks
  green while testing nothing. The equivalents here go in `AGENTS.md` too (see *Docs and gitignore*).

## Files

New:

```
tests/test_chao_tones_cli.py
.claude/skills/adding-an-approval-fixture/SKILL.md
tests/fixtures/chao_tones/inputs/accent_table.txt
tests/fixtures/chao_tones/inputs/words.txt
tests/fixtures/chao_tones/inputs/unicode_forms.txt
tests/fixtures/chao_tones/inputs/whitespace_and_passthrough.txt
tests/fixtures/chao_tones/approved/accent_table.approved.txt
tests/fixtures/chao_tones/approved/words.approved.txt
tests/fixtures/chao_tones/approved/unicode_forms.approved.txt
tests/fixtures/chao_tones/approved/whitespace_and_passthrough.approved.txt
```

`tests/fixtures/chao_tones/received/` is created by the test only on mismatch and is gitignored.

The helpers live in `tests/test_chao_tones_cli.py`, not a shared `tests/approval.py` — there is one
converter, and with no scrubbing there is little to share. Extract the module when a second converter
needs the same loop.

Modified: [.gitignore](../.gitignore), [AGENTS.md](../AGENTS.md), [README.md](../README.md).
No change to [SPEC.md](../SPEC.md) — no specified behaviour changes.

## Implementation

### `tests/test_chao_tones_cli.py`

Header comment block in the style of the other test files, saying what the fixtures are and how to
approve a change. Path constants derived from `__file__` the way `tests/conftest.py` already derives
`REPO_ROOT`.

- `_input_fixtures()` — `sorted(INPUTS_DIR.glob("*.txt"))`, paired with
  `approved/<stem>.approved.txt` whether or not that file exists yet; `AssertionError` only if
  `inputs/` itself holds no `.txt` at all. This differs deliberately from the reference repo's
  `_get_input_fixtures()`, which errors at collection time on a missing approved file: here a missing
  approved file is the first-approval case handled below, so a new fixture needs no setup beyond
  dropping it in.
- `_assert_approved(input_path, approved_path, actual)` — `actual == approved_path.read_text(
  encoding="utf-8")`, no transformation of either side. Two failure paths, both writing the proposed
  output so it can be reviewed:
  - **Approved file missing** (first approval): `mkdir` `received/`, write `<stem>.received.txt`, and
    `pytest.fail` saying this fixture has no approved output yet, followed by the copy command that
    promotes it.
  - **Mismatch**: same received file, and `pytest.fail` naming both paths, the first differing line
    number with both lines shown via `ascii()` so combining marks and stray spaces are visible in the
    terminal, and the same promote command for when the change is intended.

  On success, unlink a stale received file. The promote command is spelled out repo-relative so it can
  be pasted straight from the terminal:

  ```
  cp tests/fixtures/chao_tones/received/words.received.txt \
     tests/fixtures/chao_tones/approved/words.approved.txt
  ```
- `test_stdin_lines_convert_to_approved_output`, parametrized over `_input_fixtures()`:
  `subprocess.run([sys.executable, str(CONVERTER_PATH)], input=input_path.read_text(
  encoding="utf-8"), capture_output=True, check=True, cwd=REPO_ROOT, encoding="utf-8")`. Pass
  `encoding="utf-8"` explicitly rather than `text=True`: the converter reconfigures its own streams to
  UTF-8, so the test must decode the same way instead of falling back to the locale code page. Assert
  `result.stderr == ""`, then `_assert_approved(...)`.
- `test_arguments_convert_in_the_order_given`, over the `words.txt` fixture only: pass its lines as
  argv and assert stdout equals that fixture's approved file. This pins the argument-mode guarantee in
  `SPEC.md`'s **Command line** paragraph while reusing the fixture instead of adding another artifact.
  (Fixtures with blank lines can't be used this way — argv drops nothing but a blank argument is
  converted to a blank line, so keep `words.txt` free of blank lines.)

### Fixtures

Create each pair through the workflow itself: write the input file, run `python -m pytest`, **read the
received file**, then paste the promote command from the failure message. An approved file nobody
looked at asserts nothing, so the reading step is the point of the whole exercise.

- `accent_table.txt` — `o` plus each of the 13 accents, one per line, in `SPEC.md` table order, so the
  table and the corpus stay in step.
- `words.txt` — realistic material, no blank lines: `nə̀jɛ᷅t`, `ǒlō`, a two-word line (`nə̀t nə̀t`,
  exercising the two-space word gap), and several accents in one word (`ńj̀`).
- `unicode_forms.txt` — precomposed and decomposed `ǹ` on adjacent lines (they must produce identical
  output), an unrelated diacritic (`ë`, U+0308, which must survive into the base text), and a tone
  letter already present in the input (`˥`).
- `whitespace_and_passthrough.txt` — internal extra whitespace, a plain ASCII line returned unchanged,
  and a blank line.

Three hazards to respect while authoring these, all of which matter more now that the comparison is
exact: keep whitespace cases *internal* rather than trailing, because editors and review tooling strip
trailing whitespace; keep the final newline on every fixture, since `print()` always emits one; and do
not let an editor "tidy" the files by re-normalising Unicode, which would silently rewrite the
precomposed/decomposed pair in `unicode_forms.txt`.

### Docs and gitignore

- `.gitignore`: add `*.received.*` (the same line the reference repo uses).
- `AGENTS.md`, Testing Approach: keep the existing "prefer small parametrized assertions… switch to
  approval testing when output becomes large" wording, and add the concrete convention beneath it —
  the `tests/fixtures/<converter>/{inputs,approved,received}` layout, the `.approved.txt` /
  `.received.txt` suffixes, add-input-then-review-then-promote as the way both new and changed
  approvals are made (never auto-accept), and the rule that a text approval compares exactly: no
  scrubbing, no Unicode normalisation, no label lines in fixtures.
- `AGENTS.md`, Testing Approach: also record the traps, the way `lexicon_file_conversions` records its
  `NOT_CRAN` and 3rd-edition ones — each is a case where a run can look green or a diff can look clean
  while nothing is really being checked:
  - An input file with no approved counterpart must **fail**, never silently pass.
  - `*.received.*` is gitignored, so a received file can't be committed as though it were approved.
  - Drive subprocesses with `encoding="utf-8"`, not `text=True`: the locale code page mangles IPA.
  - Editors strip trailing whitespace and can re-normalise Unicode, both of which quietly rewrite an
    exact-comparison fixture.
- `AGENTS.md`, Testing Approach: state how approval testing satisfies the repo's existing TDD rule —
  add the fixture line first and confirm the received output is *wrong* (red), implement, then promote
  the received file (green). This is the same order the R repo's TDD bullet describes, and it is the
  reason a first approval must be read rather than accepted.
- `README.md`, Tests section: the same layout, plus the add-a-fixture and approve-a-change loops
  written out, mirroring both reference repos' READMEs. Add "add fixtures under
  `tests/fixtures/<name>/`" as a step in *Writing a new converter*.
- New skill `.claude/skills/adding-an-approval-fixture/SKILL.md`, listed in
  [AGENTS.md's Skills section](../AGENTS.md#skills) (currently `_(none yet)_`): the occasional,
  task-triggered procedure for adding a fixture and promoting its first approval — the same role
  `adding-a-lift-field` plays in `lexicon_file_conversions`. Written to the Agent Skills format with
  only the six standard frontmatter fields, per that section's rules.

## Verification

1. `python -m pytest` from the repo root — all existing and new tests pass on Linux (no FLEx needed).
2. Confirm the approval loop fails usefully: temporarily change one character in an approved file,
   re-run, and check the failure names the received path and shows the differing line escaped; then
   `git checkout` the approved file and confirm the run is green and the received file is gone.
3. Walk the add-a-fixture loop end to end, since it is the feature: create a new input file, run
   `python -m pytest`, confirm the failure says there is no approved output yet and points at a
   received file holding the proposed output, paste the promote command, re-run and confirm green with
   the received file gone. Do this with a throwaway fixture and remove it, or keep it if it earns a
   place in the corpus.
4. Confirm the fixtures really are exact: `git diff --check` reports no whitespace damage, and
   `python3 -c` printing `ascii()` of `unicode_forms.txt` shows the precomposed and decomposed lines
   still differing.
5. Spot-check one approved file by eye against the `SPEC.md` accent table, and confirm `git diff
   --stat` shows no unrelated files touched.
6. Confirm a received file can't slip in as approved: after step 2 leaves one behind, check
   `git status --porcelain` doesn't list it.
