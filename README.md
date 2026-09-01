# flex-string-converters

String converters for linguistic data, each usable three ways: from the command line, as an SIL FieldWorks Language Explorer (FLEx) Process, and as a [FlexTools](https://github.com/cdfarrow/flextools) module that runs it over a whole lexicon.

Converters are grouped into **project folders** at the repository root, one per topic or language community. Each converter is a plain Python 3 file with a `Convert()` function that takes a string and returns a string, with no FieldWorks dependency, so it runs and can be tested anywhere. A project folder's own top-level `.py` files, if any, are thin FlexTools modules that call one of its converters.

These modules are in development. **Please back up your FLEx project before running any of them** — FLEx has no undo across a FlexTools run.

## Running as a FLEx Process

FLEx's Bulk Edit → ... → Process feature can run one of these converters directly on a field's text, with no FlexTools module involved — it calls the converter's `Convert()` function by name (see [AGENTS.md's Converter Conventions](AGENTS.md#converter-conventions)). This runs your system's own Python 3, not one bundled with FLEx, so it needs Python 3 installed and reachable from FLEx, and any third-party package the chosen converter needs — `regex` for the `chao-tone-letters` converters, `pynini` for the `zhire` ones — installed into that same Python 3 with `pip install <package>` first. Each converter's section below names the packages it needs.

## `chao-tone-letters/`

Converting between tone diacritics and Chao tone letters. Not specific to any one language.

### `chao-tone-letters/converters/diacritics2chao.py`

`Convert()` strips tone diacritics from the input and appends its Chao tone letters. For example `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`. The tone-letters-only extraction is also available on its own as `tone_diacritics_to_chao_letters()`, e.g. `nə̀jɛ᷅t` → `˨ ˨˧`.

Run it on its own to convert text given as arguments, or lines read from standard input:

```
$ echo 'nə̀jɛ᷅t' | python3 chao-tone-letters/converters/diacritics2chao.py
nəjɛt ˨ ˨˧

$ python3 chao-tone-letters/converters/diacritics2chao.py 'nə̀jɛ᷅t' 'ǒlō'
nəjɛt ˨ ˨˧
olo ˨˦ ˧
```

`--attached` writes each tone letter after the syllable it marks instead of in a trailing section. That form carries no meaning in its spacing, so unlike the default it survives a pipeline, spreadsheet or copy-paste that collapses runs of spaces — see the round-trip example under [`chao2diacritics.py`](#chao-tone-lettersconverterschao2diacriticspy) below.

```
$ python3 chao-tone-letters/converters/diacritics2chao.py --attached 'nə̀jɛ᷅t' 'ǒlō'
nə˨jɛ˨˧t
o˨˦lo˧
```

It needs Python 3 and the `regex` package (`pip install regex`); FieldWorks is not required.

It also works as a FLEx Process — see [Running as a FLEx Process](#running-as-a-flex-process) above. A raw FLEx Process always calls a bare `Convert(input_string)`, so it can't pass `--attached` or reach `tone_diacritics_to_chao_letters()` directly; point it at `chao-tone-letters/converters/diacritics2chao_attached.py` or `diacritics2chao_tone_letters_only.py` instead to get either of those, respectively — both thin wrappers with no rules of their own.

### `chao-tone-letters/converters/chao2diacritics.py`

Reverses `diacritics2chao.py`: `Convert()` places Chao tone letters back onto their base text as tone diacritics. For example `nəjɛt ˨ ˨˧` → `nə̀jɛ᷅t`.

**Where the tone letters sit doesn't matter.** They can be attached to their syllable, gathered into a section before or after the text, or a mixture, and all give the same result — so a spreadsheet, a shell pipeline or a copy-paste that collapses runs of spaces or adds a trailing one can't change the reading:

```
$ python3 chao-tone-letters/converters/chao2diacritics.py \
    'ma ti ˦  ˦˨'  'ma ti ˦ ˦˨'  'ma˦ ti˦˨'  '˦ma ˦˨ti'
má tî
má tî
má tî
má tî
```

An attached tone letter names its own syllable, so it may mark only some of them: `ma˦ ti` → `má ti`. Detached tone letters have only their position to go on, so they must match the unmarked syllables exactly; a line that doesn't correspond — a syllable not accounted for, or a contour with no tone diacritic equivalent — is returned unchanged rather than partially converted, so it stays visibly unconverted for review.

Mixing the two styles in one line works too (`ma˦ ti ˦˨` → `má tî`), but warns, because a detached group can then reach back past a syllable an attached one already claimed.

Warnings go to stderr with the line number, while every line is still written to stdout so a table keeps all of its rows:

```
$ printf '%s\n' 'nəjɛt ˨ ˨˧' 'ka˨˩' | python3 chao-tone-letters/converters/chao2diacritics.py 2>warnings.txt
nə̀jɛ᷅t
ka˨˩

$ cat warnings.txt
chao2diacritics: line 2: not converted: no tone diacritic for ˨˩: 'ka˨˩'
```

The exit status stays 0 when lines warn, so an existing pipeline doesn't start breaking. `convert_with_warnings()` returns those same strings alongside the result for callers that want them, leaving `Convert()` a plain string-to-string function.

`diacritics2chao.py --attached` writes the tone letters in this form, which is the safer one to store precisely because its spacing means nothing:

```
$ python3 chao-tone-letters/converters/diacritics2chao.py --attached 'bjo᷆ sādù'
bjo˧˨ sa˧du˨

$ python3 chao-tone-letters/converters/diacritics2chao.py --attached 'bjo᷆ sādù' \
    | tr -s ' ' | python3 chao-tone-letters/converters/chao2diacritics.py
bjo᷆ sādù
```

It needs the same `regex` package as `diacritics2chao.py`; FieldWorks is not required, though it also works as a FLEx Process — see [Running as a FLEx Process](#running-as-a-flex-process) above. There is no FlexTools module for this direction yet — see [chao-tone-letters/SPEC.md's Not Yet Specified section](chao-tone-letters/SPEC.md#not-yet-specified).

### `chao-tone-letters/Extract_Chao_tone_letters_from_tone_diacritics.py`

A FlexTools module. To install, copy the `chao-tone-letters/` folder alone into your FlexTools `Modules` folder — not the whole repository checkout, since FlexTools only looks one folder deep for modules, and the module files live inside the project folder, not at the repository root. `converters/` and `tests/` inside it are left alone either way.

Goes through all the lexeme forms, runs `diacritics2chao.py`'s `Convert()` over each one, and puts the result — the spelled form with tone diacritics stripped, plus its Chao tone letters when it has any — into a custom `Pitch` field. You can use Bulk Edit Entries in FLEx to move these to the desired field.

This module was previously named `Extract_Chao_tone_letters_from_accent_notation.py`. If you have an older copy installed in your FlexTools `Modules` folder, delete it before copying in this one — FlexTools will otherwise try to load both, and the old file's import of the since-renamed converter will fail.

Running it again replaces the `Pitch` value rather than adding to it, so a second run over the same entries leaves the same result as the first. Only entries with a genuinely blank lexeme form are left alone — every other entry has its `Pitch` value overwritten, including a `Pitch` value you typed in yourself, if its lexeme form has no tone marks. **Back up your project first** (see above): this module no longer protects hand-entered `Pitch` values on entries that carry no tone marks.

It requires that you set the source lexeme field writing system as the default vernacular language. To do this in FLEx use the menu item Format > Set up vernacular writing systems… then ensure that the writing system in the top right is the desired one (using the up and down arrow buttons). It also requires that you create an entry level custom field called "Pitch" (Tools > Configure > Custom Fields…).

The `Pitch` field should show that same default vernacular writing system, because that is the one the module writes to. Each run reports which writing system it used and what type the `Pitch` field is, so you can check. If your `Pitch` field uses a different writing system, set the `PITCH_WS` constant near the top of the module to its language tag.

## `zhire/`

Converting a Zhire `[zhi]` phonetic or phonemic transcription to its orthographic spelling. The two
converters compose: phonetic → phonemic → orthography.

### `zhire/converters/phonetic2phonemic.py`

`Convert()` applies the Zhire phonology sketch's allophony and notation rules to turn a phonetic
transcription into the phonemic transcription `phonemic2orthography.py` accepts, using a finite-state
transducer, e.g. `ɲápsə́` → `njápsə́`.

```
$ echo 'ɲápsə́' | python3 zhire/converters/phonetic2phonemic.py
njápsə́

$ python3 zhire/converters/phonetic2phonemic.py 'ɲápsə́' 'nd͡ʒa'
njápsə́
ndza
```

An input symbol or sequence the mapping doesn't cover raises an error naming the offending input,
rather than passing it through unchanged or dropping it silently — this includes the phonology
sketch's own `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, which is rejected outright since it
asserts a syllable-structure interpretation that hasn't been settled for Zhire.

### `zhire/converters/phonemic2orthography.py`

`Convert()` strips tone diacritics (the orthography has no tone-marking convention yet) and maps the
remaining phonemic string to its orthographic spelling using a finite-state transducer, e.g. `hwōrì`
→ `whori`.

```
$ echo 'hwōrì' | python3 zhire/converters/phonemic2orthography.py
whori

$ python3 zhire/converters/phonemic2orthography.py 'hwōrì' 'ɔ̃ː'
whori
ɔ̃ɔ̃
```

An input symbol or sequence the mapping doesn't cover raises an error naming the offending input,
rather than passing it through unchanged or dropping it silently.

Both converters need Python 3 and the `pynini` package (`pip install pynini`). `pynini` has prebuilt
wheels for Linux; macOS and Windows need conda-forge instead, and Windows has no native wheel at all —
install via WSL there. There is no FlexTools module for either converter: FlexTools modules run under
Python .NET/IronPython on Windows, which `pynini` does not support. Both also work as a FLEx Process
(see [Running as a FLEx Process](#running-as-a-flex-process) above), where the same platform caveats on
`pynini` apply, since a FLEx Process runs a real Python 3 rather than FlexTools' bundled one.

## `__Template_converter_module.py`

Kept at the repository root, since it isn't specific to any one project folder. A starting point for a new module: copy it into the target project folder under a name without the leading `__`, point it at your converter, and change the marked places. It reads the lexeme form of every entry and reports what your converter would produce; it writes nothing and needs no custom field, so a fresh copy runs immediately against any project. Writing the result back into a field is a commented-out block below `MainFunction` that you uncomment once the read-only report looks right — see `chao-tone-letters/Extract_Chao_tone_letters_from_tone_diacritics.py` above for the worked example, and the [`adding-a-flextools-module`](.claude/skills/adding-a-flextools-module/SKILL.md) skill for the full procedure.

## Adding a new converter

1. Decide whether it belongs in an existing project folder or needs a new one. For a new project folder, see the [`adding-a-project`](.claude/skills/adding-a-project/SKILL.md) skill, which scaffolds `<project>/{SPEC.md, converters/, tests/}`.
2. Add `<project>/converters/<what_it_converts>.py` with a `Convert(input_string)` function and a command line interface, and no `flextoolslib` or FieldWorks import.
3. Add `<project>/tests/test_<what_it_converts>.py` covering `Convert()` directly.
4. Once the CLI has realistic or awkward-to-assert-inline output, add approval fixtures under `<project>/tests/fixtures/<what_it_converts>/` — see [Approval testing](#approval-testing) below.
5. If it should run over a whole lexicon, follow the [`adding-a-flextools-module`](.claude/skills/adding-a-flextools-module/SKILL.md) skill to wrap it starting from `__Template_converter_module.py`.
6. Update the project's `SPEC.md` (and the root [SPEC.md](SPEC.md) index, if it's a new project) and this README in the same change.

See [AGENTS.md](AGENTS.md) for the full contributor conventions and [SPEC.md](SPEC.md) for the index of what each project's converters and modules guarantee.

## Tests

```
python -m pytest
```

from the repository root, which discovers every project's tests in one run — each project keeps its own `tests/` folder, alongside a repository-wide `tests/` holding only the shared approval-testing harness (`tests/approval.py`). The converter tests run on any platform; so do the module tests, which stub `flextoolslib` and drive `MainFunction` with a fake project.

### Approval testing

`diacritics2chao.py`'s and `chao2diacritics.py`'s CLIs are each covered end to end by an approval-testing suite, following the same Emily Bache workflow used by the sibling [audio_label_file_conversions](https://github.com/speechchemistry/audio_label_file_conversions) and [lexicon_file_conversions](https://github.com/speechchemistry/lexicon_file_conversions) repositories:

- Input fixtures are in `<project>/tests/fixtures/<converter>/inputs/*.txt`.
- Approved outputs are in `<project>/tests/fixtures/<converter>/approved/*.approved.txt`.
- On a mismatch — or on a brand new fixture that has no approved output yet — the proposed output is written to `<project>/tests/fixtures/<converter>/received/*.received.txt`, and the test failure prints the exact command to promote it.

Unlike the EAF/XML fixtures in those sibling repos, comparison here is exact: no scrubbing and no Unicode normalisation, since NFC/NFD handling is itself part of what each `Convert()` guarantees.

Most of `chao2diacritics.py`'s input fixtures are `diacritics2chao.py`'s own approved outputs, copied over as-is: that makes its approval suite a genuine round-trip regression net against real converter output, rather than a fresh set of guesses.

To add a fixture or approve a changed one: drop or edit a `.txt` file under `inputs/`, run the tests, **read** the resulting `.received.txt` file, and only once it looks correct, run the `cp` command the failure prints to promote it into `approved/`. See the [`adding-an-approval-fixture`](.claude/skills/adding-an-approval-fixture/SKILL.md) skill for the full procedure.

## Related

`Extract_Chao_tone_letters_from_tone_diacritics.py` was extracted from [flextools_modules](https://github.com/speechchemistry/flextools_modules), which keeps a mirrored copy for now (still under this module's old name). **This repository is the canonical one.** Modules that walk the FLEx model rather than transform a string — such as `Fix_Pronunciation_Media_Paths.py` — stay there.

Attributions: This repository includes code from C D Farrows (licensed under LGPL 2.1) in `Extract_Chao_tone_letters_from_tone_diacritics.py`, so that file's licence is LGPL 2.1. Please see the source code for more attribution information.
