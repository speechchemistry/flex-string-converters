# Add base text to `chao_tones.py`'s `convert()`

Status: proposed 2026-08-19, not yet implemented.

## Context

`converters/chao_tones.py`'s `convert()` currently returns *only* the Chao
tone letters extracted from accent notation (e.g. `nə̀jɛ᷅t` → `˨ ˨˧`),
discarding the original text entirely. The user wants `convert()` to instead
return the original string with its tone-accent diacritics stripped, followed
by the tone letters — e.g. `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧` — so the output shows both
the plain spelling and its tone letters together.

Since `convert()` is the converter's public entry point (used by the CLI, as
a FLEx Process, and by the FlexTools module), the existing tone-letters-only
logic is preserved intact under a new name, `extract_chao_letters()`, and
`convert()` becomes a thin composition on top of it.

Clarified with the user:

1. Format: `base_text` + one space + tone letters (when tone letters exist).
2. "Stripped of accents" means only the 13 recognised tone-accent combining
   marks are removed from the base text — other diacritics are left alone.
3. The preserved function is named `extract_chao_letters`.
4. `Extract_Chao_tone_letters_from_accent_notation.py` is **not** changed to
   call `extract_chao_letters()` at all, and keeps no special "no tone marks"
   skip logic. It keeps calling `convert()` exactly as it does today, and
   `Pitch` is simply overwritten with whatever `convert()` returns. The user
   chose this deliberately for simplicity after being shown the consequence
   below, and asked to keep the module as close to unchanged as possible.

**Consequence, confirmed with the user:** the module's existing "leave
`Pitch` alone when there are no tone marks" protection works today by
checking whether `convert()`'s result is empty. The new `convert()` returns
`base_text` even when there are no tone marks, so it is only empty when the
lexeme form itself is blank. Practically, this means: **every entry with a
non-empty lexeme form now gets its `Pitch` field overwritten** — with just
the (accent-stripped) spelled form when there are no tone marks, or spelled
form + tone letters when there are. Only a genuinely blank lexeme form still
leaves `Pitch` untouched. This removes the previous protection for
hand-entered `Pitch` values on entries that happen to have no tone marks. The
user accepted this trade-off explicitly in favour of a simpler module.
Because `converters/chao_tones.py`'s `convert()` is the only thing changing,
**no code changes to the module's import or control flow are needed** — it
already calls `convert()` and already skips only on an empty result. The one
necessary fix is the module's report wording, which currently says "no tone
marks found" for the skip reason; that phrase is no longer accurate (see
below) and must be corrected.

## Implementation

### `converters/chao_tones.py`

- Introduce a single module-level list `ACCENT_TO_TONE_LETTERS` of the 13
  `(combining mark, tone letters)` pairs (currently inlined in the `multisub`
  call). Both functions below derive from this one list, so the codepoint set
  is never duplicated:
  - `extract_chao_letters()` passes it to `multisub` exactly as `convert()`
    does today.
  - `convert()` derives `TONE_ACCENT_MARKS = frozenset(mark for mark, _ in
    ACCENT_TO_TONE_LETTERS)` for stripping.
- Rename the current `convert()` function body to `extract_chao_letters()`,
  unchanged otherwise (still the direct entry point for pure tone-letter
  extraction, still importable and testable on its own).
- Add the new `convert(input_string)`:
  1. NFD-normalize the input.
  2. Build `base_text` by removing only characters in `TONE_ACCENT_MARKS`
     from the decomposed form, then NFC-normalize the result back (so
     unrelated combining marks recompose normally and the base text reads
     naturally). Leave whitespace exactly as in the input — no trimming or
     collapsing (that collapsing behaviour is specific to
     `extract_chao_letters`'s tone-letter track and doesn't apply to the base
     text).
  3. Call `tone_letters = extract_chao_letters(input_string)`.
  4. Return `base_text` alone if `tone_letters` is empty, otherwise
     `f"{base_text} {tone_letters}"`.
- Update the module header's one-line purpose comment, and the CLI's
  `argparse` description/example (currently "Extract Chao tone letters (only)
  from any accent notation, e.g. nə̀jɛ᷅t -> ˨ ˨˧.") to describe the new
  `convert()` output, e.g. `nə̀jɛ᷅t -> nəjɛt ˨ ˨˧`.

### `Extract_Chao_tone_letters_from_accent_notation.py`

- No change to the `from chao_tones import convert` import, and no change to
  `MainFunction`'s control flow: it keeps calling `convert(lexeme_form_itsstring)`
  and keeps the same `if not chao_letters: ... continue` skip check. Because
  `convert()`'s own behaviour changed, this is now "skip only when the lexeme
  form is blank" rather than "skip when there are no tone marks" — see the
  Context section above.
- The one required edit: the hard-coded report string in the final summary
  currently reads `"...left %d unchanged (no tone marks found)"`. That reason
  is no longer accurate (an entry can have no tone marks and still be
  written), so reword it to describe the real skip reason, e.g.
  `"...left %d unchanged (empty lexeme form)"`.
- Bump `FTM_Version` in `docs`, since `Pitch`'s written content changes for
  every entry (spelled form is now written even with no tone marks).
- Update `FTM_Description` to mention that `Pitch` now holds the spelled form
  alongside the tone letters (or the spelled form alone, with no tone marks),
  and that only a blank lexeme form is left untouched.

### `tests/test_chao_tones.py`

- Change the import to `from chao_tones import convert, extract_chao_letters`.
- Update all existing test bodies (which test the tone-letters-only
  behaviour) to call `extract_chao_letters(...)` instead of `convert(...)` —
  same assertions, since that behaviour is unchanged.
- Add a new set of tests for `convert()` covering: the worked example
  (`nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`), text with no tone accents (returns the text
  unchanged, no trailing space), an unrelated (non-tone) diacritic being left
  in the base text, and empty-string input.
- Follow the repo's TDD convention: write/extend these tests first and
  confirm they fail before implementing `convert()`.

### `tests/test_extract_chao_tone_letters_module.py`

Update assertions that hard-code the old tone-only value, since `Pitch` now
receives `convert()`'s output (`base_text`, plus tone letters when present):

- `test_writes_converted_text_in_the_vernacular_writing_system`: expected
  write becomes `(0, PITCH_FIELD, "nəjɛt ˨ ˨˧", VERN_WS)`.
- `test_dry_run_writes_nothing`: expected report line becomes
  `"nə̀jɛ᷅t -> nəjɛt ˨ ˨˧"`.
- `test_missing_pitch_field_reports_an_error_and_writes_nothing`: same report
  line update.
- `test_field_type_is_unknown_when_the_helpers_are_missing`: expected write
  becomes `(0, PITCH_FIELD, "nəjɛt ˨ ˨˧", VERN_WS)`.
- `test_entries_without_tone_marks_are_left_alone`: rename to something like
  `test_entries_with_a_blank_lexeme_form_are_left_alone`, since "no tone
  marks" no longer describes what's skipped. With `["cat", "nə̀jɛ᷅t", ""]`,
  the expected writes become `[(0, PITCH_FIELD, "cat", VERN_WS), (1,
  PITCH_FIELD, "nəjɛt ˨ ˨˧", VERN_WS)]` (both non-blank entries are now
  written — `"cat"` included, since it has no tone marks but is still a
  non-empty `convert()` result) and the summary assertion updates to `"Wrote
  Pitch for 2 of 3 entries"` / `"left 1 unchanged (empty lexeme form)"`,
  matching the module's reworded report string. This test is the one that
  most directly demonstrates the confirmed consequence from the Context
  section.
- Other tests (`test_does_not_use_the_broken_add_tag_helper`,
  `test_reports_the_pitch_field_type`, `test_reports_the_writing_system_it_writes_to`,
  `test_progress_is_reported_over_all_entries`) are unaffected.

### `SPEC.md`

- Keep the existing **Transform** steps 1–5 under the "Chao Tone Letters From
  Accent Notation" section, but attribute them explicitly to
  `extract_chao_letters()` rather than `convert()`.
- Add a new subsection describing `convert()`: NFD-normalizes, strips only the
  13 recognised tone-accent marks to produce a base text (other diacritics
  untouched, whitespace untouched), then appends a space and
  `extract_chao_letters()`'s result when non-empty. Include the worked
  example `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`.
- Update the "Extract Chao Tone Letters..." FlexTools module section:
  - **Transform**/**Writes**: now writes `convert()`'s output — the lexeme
    form with tone accents stripped, plus tone letters when present — to
    `Pitch`, not `extract_chao_letters()`'s output alone.
  - Correct the bullet that currently says entries with no tone marks are
    "left untouched...so a Pitch value entered by hand is never cleared by a
    lexeme form that carries no tone marks": that claim is no longer true.
    Replace it with: `Pitch` is overwritten with `convert()`'s result for
    every entry with a non-empty lexeme form (spelled form alone when there
    are no tone marks); only a genuinely blank lexeme form is left untouched.
    A hand-entered `Pitch` value is therefore no longer protected on entries
    lacking tone marks.

### `README.md`

- Update the `converters/chao_tones.py` section: mention both functions
  (`convert()` for base text + tone letters, `extract_chao_letters()` for
  tone-letters-only), and update the CLI example outputs to the new
  `convert()` results.
- Update the `Extract_Chao_tone_letters_from_accent_notation.py` section:
  `Pitch` now receives the spelled form plus tone letters (or just the
  spelled form when there are no tone marks); only entries with a blank
  lexeme form are left alone. Since this narrows the previous hand-entered-
  value protection, make sure this section still reads clearly alongside the
  standing "back up your project first" instruction (which stays as-is per
  `AGENTS.md`'s Data Safety section).

## Verification

- Run `python -m pytest` from the repo root — all existing and new/updated
  tests should pass, including the renamed `extract_chao_letters` tests and
  the updated module tests.
- Run the CLI directly to sanity-check the new output end-to-end:
  `python3 converters/chao_tones.py 'nə̀jɛ᷅t'` → expect `nəjɛt ˨ ˨˧`.
- Confirm `SPEC.md` and code agree per `AGENTS.md`'s rule that a mismatch
  between them is a bug.
