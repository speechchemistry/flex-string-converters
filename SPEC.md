# SPEC.md

The source of truth for what each converter and module in this repository does and guarantees: the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [AGENTS.md's Specification section](AGENTS.md#specification) for how this file and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet Specified](#not-yet-specified).

Each converter is specified first, since the converter is the product and runs the same way from the command line, from a FLEx Process, and from FlexTools. The FlexTools module that wraps it is specified after it.

## Chao Tone Letters From Accent Notation

Converter: `converters/chao_tones.py`. Takes and returns a plain string via `convert()`, needs no FLEx project, and has no `flextoolslib` dependency, so the rules below hold whether it is called from FlexTools, from the command line, or as a FLEx Process.

**Transform of `extract_chao_letters()`.**

1. The input is normalised to NFD, so accents are separate combining code points, then split into words on whitespace runs.
2. Each word is walked one grapheme cluster at a time (`regex`'s `\X`), grouping clusters into **tone-bearing units**:
   - A maximal run of **adjacent vowel** grapheme clusters is **one** unit (a diphthong is one syllable). The tone-bearing vowels are `a e i o u y ɨ ʉ ɯ ɪ ʏ ʊ ø ɘ ɵ ɤ ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ ɶ ɑ ɒ ɚ ɝ`.
   - A cluster carrying a **syllabic mark** (`U+0329`, `U+030D`) is **its own** unit — a syllabic consonant such as `m̩` is a syllable on its own and never joins a following vowel, even with no consonant after it.
   - A **modifier letter** (Unicode category `Lm`, e.g. the length mark `ː`) is transparent: it neither starts a unit nor breaks a vowel run.
   - Anything else (a consonant, punctuation, a digit) breaks a vowel run without starting a unit of its own.

   A character already present in the input — including a Chao tone letter — that is none of the above is ordinary text as far as this rule is concerned: it is never mistaken for a tone letter this function itself produced.
3. Each recognised combining accent mark carried by a unit is replaced by its Chao tone letters:

   | Code point | Example | Output |
   | --- | --- | --- |
   | `U+030B` | ő | `˥` |
   | `U+0301` | ó | `˦` |
   | `U+0304` | ō | `˧` |
   | `U+0300` | ò | `˨` |
   | `U+030F` | ȍ | `˩` |
   | `U+030C` | ǒ | `˨˦` |
   | `U+0302` | ô | `˦˨` |
   | `U+1DC4` | o᷄ | `˧˦` |
   | `U+1DC5` | o᷅ | `˨˧` |
   | `U+1DC8` | o᷈ | `˨˦˨` |
   | `U+1DC6` | o᷆ | `˧˨` |
   | `U+1DC7` | o᷇ | `˦˧` |
   | `U+1DC9` | o᷉ | `˦˨˦` |

   The contour values for `U+030C`, `U+0302`, `U+1DC4`, `U+1DC5` and `U+1DC8` are deliberately more internally consistent than the IPA chart's.
4. A unit's tone letters (from step 3, in order) are concatenated, then adjacent identical tone letters in that concatenation collapse to one — a level tone spread across a diphthong is just that level tone (`kāī` → `˧`, not `˧˧`), while a contour distributed one letter per vowel does not collapse when its letters differ (`kàí` → `˨˦`, the same result as the same rising tone written on a single vowel, `kǎ` → `˨˦`). A unit with no accents contributes nothing.
5. A word's non-empty unit groups are joined with one space; words that produced at least one group are joined with two spaces, so a word gap stays wider than a within-word gap. A word with no accents contributes nothing.
6. Leading and trailing whitespace is stripped.

Example: `[nə̀jɛ᷅t]` → `˨ ˨˧`. A Chao tone letter already present in the input and not derived from any accent — e.g. a bare `˥` — is ordinary text as far as step 2's unit walk is concerned, so it collapses away like any other non-vowel, non-syllabic character: `extract_chao_letters("˥")` → `""`.

**Transform of `convert()`.** This is the converter's public entry point (used by the CLI, as a FLEx Process, and by the FlexTools module below).

1. The input is normalised to NFD.
2. A `base_text` is built by removing only the 13 tone-accent combining marks listed above from the decomposed form, then normalising the result back to NFC. Other diacritics and all whitespace are left exactly as in the input.
3. `extract_chao_letters()` is run over the original input, exactly as specified above.
4. The result is `base_text` alone when `extract_chao_letters()`'s result is empty, otherwise `base_text` + one space + that result.

Example: `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`.

**Command line.** Text given as arguments is converted one result per line, in the order given. With no arguments the converter reads standard input line by line and writes one converted line per input line, so it works as a filter in a pipeline. Results go to stdout and diagnostics to stderr; stdin and stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Dependencies.** Python 3 and the `regex` package.

### Extract Chao Tone Letters From Accent Notation (FlexTools module)

Module: `Extract_Chao_tone_letters_from_accent_notation.py`, wrapping the converter above. `FTM_ModifiesDB` is true.

**Reads.** The lexeme form of every entry, via `LexiconGetLexemeForm(entry)`. The lexeme form is read in the project's default vernacular writing system, so that writing system must be the one holding the accent notation.

**Transform.** `convert()` from `converters/chao_tones.py`, exactly as specified above — the lexeme form with tone accents stripped, plus tone letters when the lexeme form has any. The module adds no rules of its own.

**Writes.** The entry-level custom field named `Pitch`, via `LexiconSetFieldText(entry, flagsField, chao_letters, ws)`, and only when `modifyAllowed` is true.

- The value **replaces** whatever the field held, so running the module twice over the same entries leaves the same result as running it once.
- `Pitch` is overwritten with `convert()`'s result for every entry with a non-empty lexeme form — the spelled form alone when it has no tone marks, spelled form plus tone letters when it does. Only a genuinely blank lexeme form is left untouched. A `Pitch` value entered by hand is therefore **not** protected on entries whose lexeme form lacks tone marks: it is overwritten with the spelled form.
- `ws` is the project's default vernacular writing system — the same one the lexeme form is read from — unless the module's `PITCH_WS` constant names another. It is always passed explicitly, because `LexiconSetFieldText` otherwise defaults to the default *analysis* writing system, which would store text that a vernacular field never displays.
- `LexiconAddTagToField` is deliberately not used: it reads the field back without a writing system, which raises `AttributeError` on a multi-string custom field.

**Reporting.** The type of the `Pitch` field and the writing system being written to (that line prefixed with `[DRY RUN] ` when `modifyAllowed` is false), then an entry count, then a progress bar over all entries (`report.ProgressStart` / `report.ProgressUpdate`), then one `report.Info` line per entry showing `<lexeme form> -> <convert() result>`, then a final `Wrote Pitch for <n> of <total> entries; left <m> unchanged (empty lexeme form)` summary (`Would write` and the `[DRY RUN] ` prefix when `modifyAllowed` is false).

The `Pitch` field's type is reported using `LexiconFieldIsStringType` and `LexiconFieldIsAnyStringType`. `LexiconFieldIsMultiType` is deliberately not used: in flexlibs 1.2.8 and flexlibs2 2.3.1 it reads `FLExLCM.CellarMultiTypes`, a name `FLExLCM` never defines, so it raises `AttributeError` for every field.

**Prerequisites.**

- An entry-level custom field called `Pitch` must exist (Tools > Configure > Custom Fields…). If it is missing and `modifyAllowed` is true, the module reports `The entry-level Pitch field is missing` via `report.Error` and continues in read-only mode: it still reports every conversion but writes nothing.
- The writing system holding the source lexeme form must be the project's default vernacular writing system (Format > Set up vernacular writing systems…).
- The `Pitch` field must show that same writing system, since that is the alternative the module writes. A `Pitch` field configured for the analysis writing system will not display what is written unless `PITCH_WS` is changed to match.

**Downstream.** Values land in `Pitch` so they can be moved to the desired field with Bulk Edit Entries in FLEx.

## Not Yet Specified

Behaviours that are not pinned down yet. Add to the sections above as each is settled or implemented, rather than speculating here.

- Behaviour when an entry has no lexeme form in the default vernacular writing system.
- Reading a source form from a writing system other than the default vernacular.
