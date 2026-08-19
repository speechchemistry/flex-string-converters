# flex-string-converters

String converters for linguistic data, each usable three ways: from the command line, as an SIL FieldWorks Language Explorer (FLEx) Process, and as a [FlexTools](https://github.com/cdfarrow/flextools) module that runs it over a whole lexicon.

The converters in `converters/` are the product. Each is a plain Python 3 file with a `convert()` function that takes a string and returns a string, with no FieldWorks dependency, so it runs and can be tested anywhere. The `.py` files at the top level of this repository are thin FlexTools modules that call one.

These modules are in development. **Please back up your FLEx project before running any of them** — FLEx has no undo across a FlexTools run.

## Converters

### `converters/chao_tones.py`

Extracts Chao tone letters (only) from accent notation. For example `nə̀jɛ᷅t` → `˨ ˨˧`.

Run it on its own to convert text given as arguments, or lines read from standard input:

```
$ echo 'nə̀jɛ᷅t' | python3 converters/chao_tones.py
˨ ˨˧

$ python3 converters/chao_tones.py 'nə̀jɛ᷅t' 'ǒlō'
˨ ˨˧
˨˦ ˧
```

It needs Python 3 and the `regex` package (`pip install regex`); FieldWorks is not required.

It should also work as a FLEx Process once FLEx allows Python 3 processes (at the time of writing it only allows Python 2 processes, but the developers are working on upgrading this).

## FlexTools modules

To install, copy this whole folder into your FlexTools `Modules` folder, keeping its structure. FlexTools only looks one folder deep for modules, so `converters/`, `tests/` and `plans/` are left alone, and `__Template_converter_module.py` is skipped because its name starts with `__`.

### `Extract_Chao_tone_letters_from_accent_notation.py`

Goes through all the lexeme forms, runs `converters/chao_tones.py` over each one, and puts the result into a custom `Pitch` field. You can use Bulk Edit Entries in FLEx to move these to the desired field.

Running it again replaces the `Pitch` value rather than adding to it, so a second run over the same entries leaves the same result as the first. Entries whose lexeme form has no tone marks are left alone, so a `Pitch` value you typed in yourself is never cleared.

It requires that you set the source lexeme field writing system as the default vernacular language. To do this in FLEx use the menu item Format > Set up vernacular writing systems… then ensure that the writing system in the top right is the desired one (using the up and down arrow buttons). It also requires that you create an entry level custom field called "Pitch" (Tools > Configure > Custom Fields…).

The `Pitch` field should show that same default vernacular writing system, because that is the one the module writes to. Each run reports which writing system it used and what type the `Pitch` field is, so you can check. If your `Pitch` field uses a different writing system, set the `PITCH_WS` constant near the top of the module to its language tag.

### `__Template_converter_module.py`

A starting point for a new module: copy it to a name without the leading `__`, point it at your converter, and change the marked places. It reads the lexeme form of every entry and reports what your converter would produce; it writes nothing and needs no custom field, so a fresh copy runs immediately against any project. Writing the result back into a field is a commented-out block below `MainFunction` that you uncomment once the read-only report looks right — see `Extract_Chao_tone_letters_from_accent_notation.py` above for the worked example.

## Writing a new converter

1. Add `converters/<what_it_converts>.py` with a `convert(input_string)` function and a command line interface, and no `flextoolslib` or FieldWorks import.
2. Add `tests/test_<what_it_converts>.py` covering `convert()` directly.
3. If it should run over a whole lexicon, copy `__Template_converter_module.py` to a module file at the repository root.
4. Update [SPEC.md](SPEC.md) and this README in the same change.

See [AGENTS.md](AGENTS.md) for the full contributor conventions and [SPEC.md](SPEC.md) for what each converter and module guarantees.

## Tests

```
python -m pytest
```

from the repository root. The converter tests run on any platform; so do the module tests, which stub `flextoolslib` and drive `MainFunction` with a fake project.

## Related

`Extract_Chao_tone_letters_from_accent_notation.py` was extracted from [flextools_modules](https://github.com/speechchemistry/flextools_modules), which keeps a mirrored copy for now. **This repository is the canonical one.** Modules that walk the FLEx model rather than transform a string — such as `Fix_Pronunciation_Media_Paths.py` — stay there.

Attributions: This repository includes code from C D Farrows (licensed under LGPL 2.1) in `Extract_Chao_tone_letters_from_accent_notation.py` and Darius Bacon (licensed under CC-BY-SA) in `converters/chao_tones.py`. Combining these licences results in a GPL 3 licence. Please see the source code for more attribution information.
