# flex-string-converters

String converters for linguistic data, each usable three ways: from the command line, as an SIL FieldWorks Language Explorer (FLEx) Process, and as a [FlexTools](https://github.com/cdfarrow/flextools) module that runs it over a whole lexicon.

The converters in `converters/` are the product. Each is a plain Python 3 file with a `convert()` function that takes a string and returns a string, with no FieldWorks dependency, so it runs and can be tested anywhere. The `.py` files at the top level of this repository are thin FlexTools modules that call one.

These modules are in development. **Please back up your FLEx project before running any of them** — FLEx has no undo across a FlexTools run.

## Converters

### `converters/diacritics2chao.py`

`convert()` strips tone diacritics from the input and appends its Chao tone letters. For example `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`. The tone-letters-only extraction is also available on its own as `tone_diacritics_to_chao_letters()`, e.g. `nə̀jɛ᷅t` → `˨ ˨˧`.

Run it on its own to convert text given as arguments, or lines read from standard input:

```
$ echo 'nə̀jɛ᷅t' | python3 converters/diacritics2chao.py
nəjɛt ˨ ˨˧

$ python3 converters/diacritics2chao.py 'nə̀jɛ᷅t' 'ǒlō'
nəjɛt ˨ ˨˧
olo ˨˦ ˧
```

It needs Python 3 and the `regex` package (`pip install regex`); FieldWorks is not required.

It should also work as a FLEx Process once FLEx allows Python 3 processes (at the time of writing it only allows Python 2 processes, but the developers are working on upgrading this).

### `converters/chao2diacritics.py`

Reverses `diacritics2chao.py`: `convert()` places Chao tone letters back onto their base text as tone diacritics. For example `nəjɛt ˨ ˨˧` → `nə̀jɛ᷅t`. A line that doesn't correspond 1:1 to its tone letters — a word not accounted for, or a contour with no tone diacritic equivalent — is returned unchanged rather than partially converted, so it stays visibly unconverted for review.

```
$ echo 'nəjɛt ˨ ˨˧' | python3 converters/chao2diacritics.py
nə̀jɛ᷅t

$ python3 converters/chao2diacritics.py 'nəjɛt ˨ ˨˧' 'olo ˨˦ ˧'
nə̀jɛ᷅t
ǒlō
```

It needs the same `regex` package as `diacritics2chao.py`; FieldWorks is not required. There is no FlexTools module for this direction yet — see [SPEC.md's Not Yet Specified section](SPEC.md#not-yet-specified).

## FlexTools modules

To install, copy this whole folder into your FlexTools `Modules` folder, keeping its structure. FlexTools only looks one folder deep for modules, so `converters/`, `tests/` and `plans/` are left alone, and `__Template_converter_module.py` is skipped because its name starts with `__`.

### `Extract_Chao_tone_letters_from_tone_diacritics.py`

Goes through all the lexeme forms, runs `converters/diacritics2chao.py`'s `convert()` over each one, and puts the result — the spelled form with tone diacritics stripped, plus its Chao tone letters when it has any — into a custom `Pitch` field. You can use Bulk Edit Entries in FLEx to move these to the desired field.

This module was previously named `Extract_Chao_tone_letters_from_accent_notation.py`. If you have an older copy installed in your FlexTools `Modules` folder, delete it before copying in this one — FlexTools will otherwise try to load both, and the old file's import of the since-renamed converter will fail.

Running it again replaces the `Pitch` value rather than adding to it, so a second run over the same entries leaves the same result as the first. Only entries with a genuinely blank lexeme form are left alone — every other entry has its `Pitch` value overwritten, including a `Pitch` value you typed in yourself, if its lexeme form has no tone marks. **Back up your project first** (see above): this module no longer protects hand-entered `Pitch` values on entries that carry no tone marks.

It requires that you set the source lexeme field writing system as the default vernacular language. To do this in FLEx use the menu item Format > Set up vernacular writing systems… then ensure that the writing system in the top right is the desired one (using the up and down arrow buttons). It also requires that you create an entry level custom field called "Pitch" (Tools > Configure > Custom Fields…).

The `Pitch` field should show that same default vernacular writing system, because that is the one the module writes to. Each run reports which writing system it used and what type the `Pitch` field is, so you can check. If your `Pitch` field uses a different writing system, set the `PITCH_WS` constant near the top of the module to its language tag.

### `__Template_converter_module.py`

A starting point for a new module: copy it to a name without the leading `__`, point it at your converter, and change the marked places. It reads the lexeme form of every entry and reports what your converter would produce; it writes nothing and needs no custom field, so a fresh copy runs immediately against any project. Writing the result back into a field is a commented-out block below `MainFunction` that you uncomment once the read-only report looks right — see `Extract_Chao_tone_letters_from_tone_diacritics.py` above for the worked example.

## Writing a new converter

1. Add `converters/<what_it_converts>.py` with a `convert(input_string)` function and a command line interface, and no `flextoolslib` or FieldWorks import.
2. Add `tests/test_<what_it_converts>.py` covering `convert()` directly.
3. Once the CLI has realistic or awkward-to-assert-inline output, add approval fixtures under `tests/fixtures/<what_it_converts>/` — see [Approval testing](#approval-testing) below.
4. If it should run over a whole lexicon, copy `__Template_converter_module.py` to a module file at the repository root.
5. Update [SPEC.md](SPEC.md) and this README in the same change.

See [AGENTS.md](AGENTS.md) for the full contributor conventions and [SPEC.md](SPEC.md) for what each converter and module guarantees.

## Tests

```
python -m pytest
```

from the repository root. The converter tests run on any platform; so do the module tests, which stub `flextoolslib` and drive `MainFunction` with a fake project.

### Approval testing

`diacritics2chao.py`'s and `chao2diacritics.py`'s CLIs are each covered end to end by an approval-testing suite, following the same Emily Bache workflow used by the sibling [audio_label_file_conversions](https://github.com/speechchemistry/audio_label_file_conversions) and [lexicon_file_conversions](https://github.com/speechchemistry/lexicon_file_conversions) repositories:

- Input fixtures are in `tests/fixtures/<converter>/inputs/*.txt`.
- Approved outputs are in `tests/fixtures/<converter>/approved/*.approved.txt`.
- On a mismatch — or on a brand new fixture that has no approved output yet — the proposed output is written to `tests/fixtures/<converter>/received/*.received.txt`, and the test failure prints the exact command to promote it.

Unlike the EAF/XML fixtures in those sibling repos, comparison here is exact: no scrubbing and no Unicode normalisation, since NFC/NFD handling is itself part of what each `convert()` guarantees.

Most of `chao2diacritics.py`'s input fixtures are `diacritics2chao.py`'s own approved outputs, copied over as-is: that makes its approval suite a genuine round-trip regression net against real converter output, rather than a fresh set of guesses.

To add a fixture or approve a changed one: drop or edit a `.txt` file under `inputs/`, run the tests, **read** the resulting `.received.txt` file, and only once it looks correct, run the `cp` command the failure prints to promote it into `approved/`. See the [`adding-an-approval-fixture`](.claude/skills/adding-an-approval-fixture/SKILL.md) skill for the full procedure.

## Related

`Extract_Chao_tone_letters_from_tone_diacritics.py` was extracted from [flextools_modules](https://github.com/speechchemistry/flextools_modules), which keeps a mirrored copy for now (still under this module's old name). **This repository is the canonical one.** Modules that walk the FLEx model rather than transform a string — such as `Fix_Pronunciation_Media_Paths.py` — stay there.

Attributions: This repository includes code from C D Farrows (licensed under LGPL 2.1) in `Extract_Chao_tone_letters_from_tone_diacritics.py`, so that file's licence is LGPL 2.1. Please see the source code for more attribution information.
