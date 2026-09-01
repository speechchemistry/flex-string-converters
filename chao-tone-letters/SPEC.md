# Chao Tone Letters

The source of truth for what each converter and module in the `chao-tone-letters` project does and guarantees: the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [the root SPEC.md](../SPEC.md) for how the projects are split up, and [AGENTS.md's Specification section](../AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet Specified](#not-yet-specified).

Each converter is specified first, since the converter is the product and runs the same way from the command line, from a FLEx Process, and from FlexTools. The FlexTools module that wraps it is specified after it.

## Chao Tone Letters From Tone Diacritics

Converter: `converters/diacritics2chao.py`. Takes and returns a plain string via `Convert()`, needs no FLEx project, and has no `flextoolslib` dependency, so the rules below hold whether it is called from FlexTools, from the command line, or as a FLEx Process.

**Transform of `tone_diacritics_to_chao_letters()`.**

1. The input is normalised to NFD, so tone diacritics are separate combining code points, then split into words on whitespace runs.
2. Each word is walked one grapheme cluster at a time (`regex`'s `\X`), grouping clusters into **tone-bearing units**:
   - A maximal run of **adjacent vowel** grapheme clusters is **one** unit (a diphthong is one syllable). The tone-bearing vowels are `a e i o u y ɨ ʉ ɯ ɪ ʏ ʊ ø ɘ ɵ ɤ ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ ɶ ɑ ɒ ɚ ɝ`.
   - A cluster carrying a **syllabic mark** (`U+0329`, `U+030D`) is **its own** unit — a syllabic consonant such as `m̩` is a syllable on its own and never joins a following vowel, even with no consonant after it.
   - A **modifier letter** (Unicode category `Lm`, e.g. the length mark `ː`) is transparent: it neither starts a unit nor breaks a vowel run.
   - Anything else (a consonant, punctuation, a digit) breaks a vowel run without starting a unit of its own.

   A character already present in the input — including a Chao tone letter — that is none of the above is ordinary text as far as this rule is concerned: it is never mistaken for a tone letter this function itself produced.
3. Each recognised tone diacritic carried by a unit is replaced by its Chao tone letters:

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
4. A unit's tone letters (from step 3, in order) are concatenated, then adjacent identical tone letters in that concatenation collapse to one — a level tone spread across a diphthong is just that level tone (`kāī` → `˧`, not `˧˧`), while a contour distributed one letter per vowel does not collapse when its letters differ (`kàí` → `˨˦`, the same result as the same rising tone written on a single vowel, `kǎ` → `˨˦`). A unit with no tone diacritics contributes nothing.
5. A word's non-empty unit groups are joined with one space; words that produced at least one group are joined with two spaces, so a word gap stays wider than a within-word gap. A word with no tone diacritics contributes nothing.
6. Leading and trailing whitespace is stripped.

Example: `[nə̀jɛ᷅t]` → `˨ ˨˧`. A Chao tone letter already present in the input and not derived from any tone diacritic — e.g. a bare `˥` — is ordinary text as far as step 2's unit walk is concerned, so it collapses away like any other non-vowel, non-syllabic character: `tone_diacritics_to_chao_letters("˥")` → `""`.

**Transform of `Convert()`.** This is the converter's public entry point (used by the CLI, as a FLEx Process, and by the FlexTools module below).

1. The input is normalised to NFD.
2. A `base_text` is built by removing only the 13 recognised tone diacritics listed above from the decomposed form, then normalising the result back to NFC. Other diacritics and all whitespace are left exactly as in the input.
3. `tone_diacritics_to_chao_letters()` is run over the original input, exactly as specified above.
4. The result is `base_text` alone when `tone_diacritics_to_chao_letters()`'s result is empty, otherwise `base_text` + one space + that result.

Example: `nə̀jɛ᷅t` → `nəjɛt ˨ ˨˧`.

**Attached output.** `Convert(input_string, attached=True)`, and equivalently `tone_diacritics_to_attached(input_string)`, writes each unit's tone letters immediately after that unit instead of gathering them into a trailing section: `nə̀jɛ᷅t` → `nə˨jɛ˨˧t`, `bjo᷆ sādù` → `bjo˧˨ sa˧du˨`. The segmentation, the tone-letter values and the adjacent-duplicate collapsing are all exactly as above; only where the letters are written differs. A word with no tone diacritics is returned as it was.

The point of the form is that spacing then carries no meaning at all, so a shell pipeline, a spreadsheet or a copy-paste that collapses runs of spaces or adds a trailing one cannot change how the result reads back — which the trailing section, whose word gaps *are* its meaning, cannot survive. It is therefore the safer form to store in a table column or a FLEx field. It is off by default so that the FLEx Process, the FlexTools module and every existing caller keep the output they already have.

`Convert()` keeps its single-argument signature for use as an SIL FLEx Process; `attached` is an optional keyword argument. A raw FLEx Process always calls a bare `Convert(input_string)` with no keyword arguments, so it has no way to select `attached=True` this way — `converters/diacritics2chao_attached.py` exists for that case: a thin wrapper with no transform rules of its own, whose `Convert(input_string)` forwards to this converter's `Convert(input_string, attached=True)`, so a FLEx Process gets attached output by being pointed at that file instead of this one.

**Command line.** Text given as arguments is converted one result per line, in the order given. With no arguments the converter reads standard input line by line and writes one converted line per input line, so it works as a filter in a pipeline. `--attached` selects the attached output described above. Results go to stdout and diagnostics to stderr; stdin and stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Dependencies.** Python 3 and the `regex` package.

## Tone Diacritics From Chao Tone Letters

Converter: `converters/chao2diacritics.py`. Reverses `converters/diacritics2chao.py`: given text carrying Chao tone letters, places tone diacritics back onto the tone-bearing units they belong to. Takes and returns a plain string via `Convert()`, needs no FLEx project, and has no `flextoolslib` dependency.

**Where the tone letters may sit.** Anywhere. `Convert()` reads the tone letters attached to their syllable (`ma˦ ti˦˨`), gathered into a section before or after the text (`ma ti ˦  ˦˨`, `˦  ˦˨ ma ti`), or a mixture of those, and all of them give the same result. Spacing carries no meaning of its own, so a spreadsheet, a shell pipeline or a copy-paste that collapses runs of spaces or adds a trailing one cannot change the reading.

**Transform of `Convert()`.**

1. The input is NFD-normalised and walked once by grapheme cluster. Every run of adjacent Chao tone letters (`U+02E5`–`U+02E9`) is one **group**, so `˦˨` is a single contour and `˦ ˨` is two groups.
2. Each group is **attached** or **free**. It is attached when it immediately follows a tone-bearing unit in the same word with no whitespace in between — reaching back over a coda consonant, so `mat˦` marks the `a`. It is free otherwise: preceded by whitespace, or at the start of a word.
3. The text is walked into tone-bearing units exactly as `diacritics2chao.py`'s `tone_diacritics_to_chao_letters()` does (see that converter's step 2 above), using its own copy of the tone-bearing vowel set and syllabic marks. Chao tone letters are Unicode category `Sk`, not `Lm`, so a tone letter breaks a vowel run rather than being transparent to it: `ma˦i` is two units, not one.
4. Attached groups bind to the unit they follow. Free groups then fill the units no attached group claimed, in document order. For a unit of *m* tone-bearing clusters receiving a group of *k* tone-letter characters:
   - the whole group is one of the 13 recognised tone-letter values and *m* = 1 → place that single tone diacritic on the one cluster (`ka˨˦` → `kǎ`).
   - *k* = 1 → repeat that tone diacritic on every cluster in the unit (`kai˧` → `kāī`).
   - *k* = *m* → place one tone diacritic per cluster, in order (`kai˨˦` → `kàí`).
   - otherwise → the input is returned unchanged (this is where a contour with no tone diacritic equivalent lands — see below).

   The tone diacritic is appended after any marks the cluster already carries, and the whole result is normalised to NFC.
5. The tone letters are removed. A whitespace run that separated them is dropped where the removal leaves no surviving text on one side of it, and kept otherwise — so the space inside `ma˦ ti˦˨` survives and the one before a trailing tone section does not.

**Attached marking may be partial; free groups must fill exactly.** `ma˦ ti` → `má ti`: an attached letter names its own syllable, so an unmarked syllable is unambiguously toneless and no count applies. A free group has only its position to say which syllable it means, so the free groups must match the unmarked units exactly or the whole input is returned unchanged. A partial fill would have to guess that the missing tones are the trailing ones, and when the dropped letter was actually the first, every remaining tone shifts one syllable and the result still looks plausible.

6. The whole input is returned unchanged, rather than partially converted, whenever: the free groups don't match the unmarked units in number; two groups bind to the same unit (`ma˦t˨`); or a group's letters/cluster combination doesn't fit any of step 4's rules. A line that comes back still visibly carrying its tone letters is self-diagnosing.

   Only 8 contours have a tone diacritic equivalent — `˨˦ ˦˨ ˧˦ ˨˧ ˨˦˨ ˧˨ ˦˧ ˦˨˦` — so a contour such as `˨˩` or `˥˩` cannot be placed as a single tone diacritic and always falls into this unchanged case (e.g. `ka˨˩` → `ka˨˩`, unchanged) when it is the whole of a one-cluster unit's group.

Example: `nəjɛt ˨ ˨˧` → `nə̀jɛ᷅t`, and identically `nə˨jɛ˨˧t` → `nə̀jɛ᷅t`.

**Any Chao tone letter in the input is consumed as a tone mark.** This converter has no trailing-section pattern to match first, so unlike `diacritics2chao.py` — whose step 2 leaves a tone letter already present in the input as ordinary text — it cannot treat one as literal data. Text that needs to carry a Chao tone letter as content is not valid input to this converter.

**Warnings.** `convert_with_warnings(input_string)` returns `(result, warnings)`, where `warnings` is a possibly empty list of plain strings; `Convert()` returns just the first element. They are kept apart so that `Convert()` writes nothing anywhere: it runs unchanged as an SIL FLEx Process, and a FlexTools module wrapping it must report through the `report` object rather than `print`. The list is not exhaustive, and covers:

| Condition | Message | Converted? |
| --- | --- | --- |
| The free groups don't match the unmarked units | `not converted: 2 detached tone letter groups for 3 unmarked syllables` | no |
| A group has no tone diacritic equivalent | `not converted: no tone diacritic for ˨˩` | no |
| Two groups bind to one unit | `not converted: two tone letter groups on one syllable` | no |
| The base text already carries a tone diacritic | `base text already carries a tone diacritic` | yes, but to a doubly marked vowel: `má˨` → `má̀` |
| The line mixes attached and free groups | `line mixes attached and detached tone letters` | yes, but a free group can reach back past a syllable an attached one claimed: `pa ta˧ ka˨ ˩` → `pȁ tā kà` |
| Attached marking leaves some units unmarked | `1 of 2 syllables not marked by an attached tone letter` | yes |

**`chao_letters_to_tone_diacritics(base_text, tone_letters)`** places `tone_letters` onto `base_text`'s units as free groups and returns `None` if they don't correspond — useful on its own when spelling and tone letters already come from two separate fields, such as a FlexTools module reading a lexeme form and a `Pitch` field.

**Round-trip status.** `diacritics2chao.py`'s `Convert()` followed by this converter's `Convert()` returns the original word exactly, for every word that isn't one of the two cases below — in either of that converter's output forms, the trailing section or `--attached`. This converter's `Convert()` followed by `diacritics2chao.py`'s `Convert()` is always exact.

What does not round trip: which vowels of a diphthong originally carried a tone diacritic is not recoverable, since a level tone repeated across a diphthong and a level tone written on only one of its vowels produce the same tone letters (`kāi` and `kāī` both give `kai ˧`, and this converter always writes `kāī`), and likewise for a contour written as a single tone diacritic versus one letter per vowel (`kǎi` and `kàí` both give `kai ˨˦`, and this converter always writes `kàí`).

**Command line.** Text given as arguments converts one result per line, in the order given; with no arguments the converter reads standard input line by line. Results go to stdout and warnings to stderr, prefixed with the line number and quoting the line: `chao2diacritics: line 2: not converted: no tone diacritic for ˨˩: 'ka˨˩'`. Every input line is written to stdout whether or not it converted, so a column of a table keeps all of its rows, and the exit status stays 0 when lines warn — a warning is a diagnostic, not a failure. stdin, stdout and stderr are all read and written as UTF-8.

**Dependencies.** Python 3 and the `regex` package.

### Extract Chao Tone Letters From Tone Diacritics (FlexTools module)

Module: `Extract_Chao_tone_letters_from_tone_diacritics.py`, wrapping the converter above. `FTM_ModifiesDB` is true.

**Reads.** The lexeme form of every entry, via `LexiconGetLexemeForm(entry)`. The lexeme form is read in the project's default vernacular writing system, so that writing system must be the one holding the tone diacritics.

**Transform.** `Convert()` from `converters/diacritics2chao.py`, exactly as specified above — the lexeme form with tone diacritics stripped, plus tone letters when the lexeme form has any. The module adds no rules of its own.

**Writes.** The entry-level custom field named `Pitch`, via `LexiconSetFieldText(entry, flagsField, chao_letters, ws)`, and only when `modifyAllowed` is true.

- The value **replaces** whatever the field held, so running the module twice over the same entries leaves the same result as running it once.
- `Pitch` is overwritten with `Convert()`'s result for every entry with a non-empty lexeme form — the spelled form alone when it has no tone marks, spelled form plus tone letters when it does. Only a genuinely blank lexeme form is left untouched. A `Pitch` value entered by hand is therefore **not** protected on entries whose lexeme form lacks tone marks: it is overwritten with the spelled form.
- `ws` is the project's default vernacular writing system — the same one the lexeme form is read from — unless the module's `PITCH_WS` constant names another. It is always passed explicitly, because `LexiconSetFieldText` otherwise defaults to the default *analysis* writing system, which would store text that a vernacular field never displays.
- `LexiconAddTagToField` is deliberately not used: it reads the field back without a writing system, which raises `AttributeError` on a multi-string custom field.

**Reporting.** The type of the `Pitch` field and the writing system being written to (that line prefixed with `[DRY RUN] ` when `modifyAllowed` is false), then an entry count, then a progress bar over all entries (`report.ProgressStart` / `report.ProgressUpdate`), then one `report.Info` line per entry showing `<lexeme form> -> <Convert() result>`, then a final `Wrote Pitch for <n> of <total> entries; left <m> unchanged (empty lexeme form)` summary (`Would write` and the `[DRY RUN] ` prefix when `modifyAllowed` is false).

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
- A FlexTools module wrapping `converters/chao2diacritics.py` to write tone diacritics back onto a FLEx field. Deliberately not built: it would write lexeme forms, a riskier write than `Pitch`. See [`plans/old/chao-tones-per-syllable-and-reverse.md`](../plans/old/chao-tones-per-syllable-and-reverse.md) for the reasoning.
- *Attested* diphthong forms in `chao2diacritics.py`'s approval corpus. Simulated ones now appear in `attached_simulated` and `trailing_spacing_variants_simulated`, both derived from `diacritics2chao.py`'s own `diphthongs_simulated` fixture, so the rule is covered end to end; only real-world diphthong data is still missing (see the same plan's Approval corpus section).
- Which rule should eventually replace `chao2diacritics.py`'s bail-out on a contour with no tone diacritic equivalent (e.g. `ka ˨˩`). Two alternatives were considered and deferred: duplicating the vowel with one level tone diacritic per step (`ka ˨˩` → `kàȁ`), which changes the base spelling and breaks the round trip; or stacking the level tone diacritics on one vowel, which keeps the spelling but is not conventional notation. See the same plan's "Deferred, and documented" section for the full discussion.
