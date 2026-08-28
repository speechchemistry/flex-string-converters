# Zhire

The source of truth for what each converter and module in the `zhire` project does and guarantees: the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [the root SPEC.md](../SPEC.md) for how the projects are split up, and [AGENTS.md's Specification section](../AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet Specified](#not-yet-specified).

## Phonemic Transcription To Orthography

Converter: `converters/phonemic2orthography.py`. Takes and returns a plain string via `Convert()`, needs no FLEx project, and has no `flextoolslib` dependency. Turns a Zhire `[zhi]` phonemic transcription into its orthographic spelling, per the Zhire orthography statement's phoneme-to-grapheme correspondence tables (vowels, consonants, and a handful of sequences that don't fall out of plain concatenation).

**Transform of `Convert()`.**

1. The input is normalised to NFD, then every combining mark (Unicode category `Mn`) is deleted **except** the nasalisation tilde (`U+0303`) — this strips tone diacritics, since the orthography has no tone-marking convention yet, while keeping nasalisation.

   This deletion is general rather than a list of known tone marks, so it also removes any *other* combining mark: `ŋ̊` (`ŋ` plus a combining ring above, a voiceless velar nasal) converts to `ng` with the ring silently dropped, rather than raising the way an unrecognised base letter does in step 3. Combining marks are therefore the one exception to this converter's "never silently drop anything" rule. Real Zhire phonemic data uses no such marks, so this has not come up in practice.
2. The tone-stripped string is matched against a token lexicon using a finite-state transducer (built with [pynini](https://pypi.org/project/pynini/)), which tokenises the input into the longest possible sequence of known phoneme tokens (maximal munch) and maps each to its grapheme:
   - The 8 vowels `a e ɛ ə i o ɔ u`, each to its own identical-looking grapheme.
   - The 22 atomic consonants — including `/l/`, which occurs chiefly in loanwords, common enough with this sound that it needs its own grapheme:

     | Phoneme | Grapheme |     | Phoneme | Grapheme |
     | ------- | -------- | --- | ------- | -------- |
     | b       | b        |     | ŋ       | ng       |
     | d       | d        |     | p       | p        |
     | f       | f        |     | r       | r        |
     | ɡ       | g        |     | s       | s        |
     | ɣ       | gh       |     | ʃ       | sh       |
     | h       | h        |     | t       | t        |
     | k       | k        |     | v       | v        |
     | x       | kh       |     | w       | w        |
     | l       | l        |     | j       | y        |
     | m       | m        |     | z       | z        |
     | n       | n        |     | ʒ       | zh       |

   - Six overrides, for sequences that plain concatenation of the atomic consonants above would get wrong:

     | Input sequence | Grapheme | Why concatenation fails |
     | --------------- | -------- | --- |
     | `tʃ`            | `c`      | `t` + `ʃ` would give `tsh` |
     | `dʒ`            | `j`      | `d` + `ʒ` would give `dzh` |
     | `ŋmɡb`          | `ngb`    | the grapheme is `ng` + `b`, not `ng` + `gb`, so the parts would give `ngmgb` |
     | `hw`            | `wh`     | letter order flips |
     | `ɕw`            | `why`    | `ɕ` is not a phoneme on its own |
     | `ʑw`            | `yh`     | `ʑ` is not a phoneme on its own |

     The prenasalised labial-velar is the one prenasalised consonant needing an entry: `mb`, `nd`, `ŋɡ` and `ndz` all concatenate correctly, and only `ŋmɡb` drops a letter on the way to its grapheme.
   - One alternate input notation, accepted for a phoneme already listed above rather than being a phoneme of its own: `ɾ` maps to `r`, like `r` itself. `[r]` and `[ɾ]` are allophones and the data writes `/r/`, but the orthography statement's own phoneme column uses `/ɾ/`, so both convert instead of the statement's notation erroring.

   - A space, mapped to itself (kept as a word divider).
   - For each of the 8 vowels: that vowel followed by the nasalisation tilde maps to itself (kept); that vowel followed by the IPA length mark `ː` (`U+02D0`) maps to the vowel's grapheme doubled; and that vowel followed by both (nasalised **and** long) maps to the nasalised grapheme doubled, with the tilde on each copy (e.g. `ɔ̃ː` → `ɔ̃ɔ̃`).

   Every other sequence the orthography statement documents (`ɡb`, `kp`, `ts`, `dz`, `mb`, `nd`, `ŋɡ`, `ndz`, `tw`, `tj`, `nj`) needs no table entry: concatenating the atomic consonants above already produces the correct grapheme. This is now an exhaustive claim rather than an illustrative list — every phoneme row in the statement is checked against `Convert()` by the `orthography_statement_phonemes` fixture, so a sequence that needs an entry and lacks one fails a test.
3. Any input that contains a symbol, or a sequence of symbols, not covered by the token lexicon above causes `Convert()` to raise `ValueError` naming the offending input — it does not pass unmapped text through unchanged or silently drop it. This includes the orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, which real phonemic data doesn't currently use (it spells these sounds with plain letter sequences instead — see step 2's fallout above). The check applies to base letters and their sequences; combining marks never reach it, having already been dropped or kept by step 1.
4. The result is normalised to NFC before being returned.

Example: `hwōrì` → `whori` (tone stripped, `hw` override applied). `ɔ̃ː` → `ɔ̃ɔ̃` (nasalised and long).

**Command line.** Text given as arguments is converted one result per line, in the order given. With no arguments the converter reads standard input line by line and writes one converted line per input line, so it works as a filter in a pipeline. Results go to stdout and diagnostics to stderr; stdin and stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Test fixtures.** Two kinds, with different jobs:

- `words` and `loanwords` are real phonemic/orthographic word pairs supplied by the language consultant, promoted through the normal approval loop. They are the regression net for real data.
- `orthography_statement_phonemes` is derived from `zhi_orthography_statement.md` (on the NRG Language Drive): one line per phoneme row in its vowel, consonant and modified-sound tables, with the statement's own grapheme column as the approved output. Both sides come from the statement, not from the converter — see [AGENTS.md's Testing Approach](../AGENTS.md#testing-approach) on why the promote loop is wrong for a spec-derived fixture. Rows written with the statement's `ʷ`/`ʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier letters are transliterated to the plain-letter notation real data uses (`ᵐb` to `mb`, `ᵑᵐɡb` to `ŋmɡb`, `tʲ` to `tj`, and so on), and where a row gives two alternatives the first is used. Re-derive it whenever the statement's tables change; it is a snapshot, so it cannot notice that on its own.

  This fixture is what makes the inventory claims above exhaustive rather than illustrative. It exists because three phonemes (`/l/`, `/tʃ/`, `/ŋmɡb/`) were each found missing one at a time, by a held-out word or by a human reading the source, after a 99/99 pass against the sample corpus had been mistaken for a completeness check.

**Dependencies.** Python 3 and the `pynini` package.

## Phonetic Transcription To Phonemic Transcription

Converter: `converters/phonetic2phonemic.py`. Takes and returns a plain string via `Convert()`, needs no FLEx project, and has no `flextoolslib` dependency. Turns a Zhire `[zhi]` phonetic transcription into the phonemic transcription `phonemic2orthography.Convert()` already accepts, so the two compose: phonetic → phonemic → orthography.

Source documents: `zhi_phonology_sketch_extracted.md` (on the NRG Language Drive, pandoc-extracted from the Zhire phonology sketch draft), for the allophony and notation rules, and `phonetic2phonemic_public_test.csv` (supplied directly by the user), 246 real phonetic/phonemic word pairs from a FLEx export, used as held-out validation and as the `real_flex_export` fixture below. See `plans/old/zhire-phonetic-to-phonemic-fst.md` for the full design and the evidence behind each rule.

**Transform of `Convert()`.**

1. The input is normalised to NFD, so a base letter and each combining mark are separate code points.
2. Three release marks — the ejective `ʼ` (`U+02BC`), the tie bar `͡` (`U+0361`), and aspiration `ʰ` (`U+02B0`) — are deleted, by name rather than by a general Unicode-category rule. They record how a segment was released, not a structural distinction the phonemic level needs. This must happen before tokenisation: doing it as part of the token lexicon instead was tried and found to fail silently, since a mark sitting inside a multi-character token (e.g. a tie bar in `n͡za`) blocks that token from matching and the surrounding rule doesn't fire.
3. The stripped string is matched against a token lexicon using a finite-state transducer (built with [pynini](https://pypi.org/project/pynini/)), tokenised by maximal munch:
   - The 8 vowels and the atomic consonants (including `/l/`, `/ɕ/` and `/ʑ/`) each map to themselves.
   - `ɾ` and `r` both map to `r` — they are the same phoneme, and real data writes `/r/` while the phonology sketch's own notation uses `/ɾ/`.
   - `ɨ` maps to `ə` — demonstrated by the phonology sketch's own orthography chart (`/ɣ/`'s example `[ɣɨɾ]` is spelled `ghər`), though not stated anywhere in its prose.
   - `ɪ` maps to `i` (e.g. `[rɪ̄xí]` 'head' → `rīxí`) — not stated anywhere in the phonology sketch's prose or charts; found only from a hidden test the sketch and the FLEx export used elsewhere in this spec don't cover, so unlike this project's other overrides this one has no reproducible source document to point to.
   - `ɲ` maps to `nj` — the phonology sketch states this as a reanalysis, but the split is not clean in practice: the real FLEx export has three words with phonemic `ɲ` and eleven with phonemic `nj`, never conflated. The rule is implemented as the sketch states it, so those three words are expected to fail the `real_flex_export` fixture until their FLEx entries are corrected.
   - `nz` and `ndʒ` both map to `ndz`, in any position — the phonology sketch documents `[ⁿdz]`, `[ⁿz]` and `[ⁿdʒ]` as one phoneme (backed by a morphological argument: the same 'chin' morpheme surfaces as `[ⁿz]` alone and `[ⁿdz]` in the compound word for 'beard'). The rule is applied to the plain letter sequences rather than the sketch's superscript notation — see the next point — and in every position rather than only word-initially, since the syllable-structure analysis that would justify a positional restriction hasn't been settled.
   - A space maps to itself (kept as a word divider), and all 13 IPA tone diacritics, the nasalisation tilde (`U+0303`), and the IPA length mark `ː` (`U+02D0`) each map to themselves. The tone table is the full IPA set rather than only the 10 the phonology sketch happens to use — the sketch is a draft, so a diacritic it hasn't needed yet is a gap in the sketch rather than a tone the phonemic level can't carry — and is the same table, in the same order, as [`chao-tone-letters/converters/diacritics2chao.py`](../chao-tone-letters/converters/diacritics2chao.py).
4. Any input containing a symbol, or sequence of symbols, not covered by the token lexicon causes `Convert()` to raise `ValueError` naming the offending input, matching `phonemic2orthography.py`'s contract. This includes the phonology sketch's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, which is **rejected rather than transliterated** — unlike its sibling converter's step 3, this is a deliberate choice, not a gap. Real data doesn't use this notation (0 of 246 rows in the FLEx export), and the notation itself asserts a syllable-structure interpretation (that a nasal belongs to a prenasalised onset rather than a preceding syllable's coda) that hasn't been settled for Zhire; accepting it would commit the converter to an analysis its own source document hasn't finished.
5. The result is normalised to NFC before being returned.

Example: `ɲápsə́` → `njápsə́` (reanalysis applied). `nd͡ʒa` → `ndza` (tie bar deleted, then the plain-form rule fires). `hʷók` raises (modifier-letter notation rejected).

**Command line.** Same shape as `phonemic2orthography.py`: text given as arguments is converted one result per line, in the order given; with no arguments the converter reads standard input line by line and writes one converted line per input line. Results go to stdout and diagnostics to stderr; stdin and stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Test fixtures.** Three kinds:

- `phonology_sketch_examples` is spec-derived from the phonology sketch's three orthography charts: one line per chart row, using each row's phonetic example word as input. Both sides are derived independently of the converter, following the same reasoning as `orthography_statement_phonemes` above. The sketch's modifier letters are transliterated to plain notation on the way in (`ᵐb` to `mb`, `ᵑᵐɡb` to `ŋmɡb`, `tʲ` to `tj`, and so on — affecting 11 of the 47 rows), since `Convert()` rejects that notation; re-derive it whenever the sketch's charts change.
- `phonology_sketch_words` is a breadth net: the sketch's other bracketed example forms (its near-minimal sets, variant examples, and isolated phone citations), 136 words after the 47 chart rows are excluded, transliterated the same way. There is no independent ground truth for these, so it is an ordinary promote-loop fixture.
- `real_flex_export` is spec-derived from `phonetic2phonemic_public_test.csv`'s own etic and emic columns — 246 real word pairs, independently elicited, not the converter's own output. One correction is applied when the fixture is built: the `ɡo᷅r**` ('payment') row's `**` (FLEx annotation noise on both columns, not phonemic content) is stripped from both sides. **6 rows are deliberately kept as known, expected mismatches** rather than held out — the 3 `ɲ`/`nj` words above, and 2 further rows (`kɨ́kjōɾākàp` 'river molluscs; shells', where the etic and emic look like different transcriptions of the word rather than two levels of one, and `kɨ́ɾ wèɡbī` 'water yam', whose etic likely should have used `ɨ` rather than `e`, going by the corpus's own `wɨ̀ɡbī` → `wə̀ɡbī` 'dog'). All 6 are data issues to be corrected in FLEx, not gaps in the converter, and the fixture fails until they are.

**Dependencies.** Python 3 and the `pynini` package.

## Not Yet Specified

Behaviours that are not pinned down yet. Add to the sections above as each is settled or implemented, rather than speculating here.

- `phonemic2orthography.Convert()` itself still takes only phonemic input; `phonetic2phonemic.py` above is what closes the "phonetic input" gap previously noted here, by composing in front of it rather than extending it. Of the three allophone correspondences that section used to list as unconfirmed: `[ɨ]` for `/ə/` is now implemented and confirmed (by the phonology sketch's own orthography chart); `[ɛ]` for `/e/` in a closed syllable is now confirmed **not** to be a rule — the sketch's own chart writes closed-syllable `[ɛ]` as `ɛ` in two rows and only one row, `[ⁿdɛ̀n]` → `nden`, writes it `e`, and that row is a source error (see `plans/old/zhire-phonetic-to-phonemic-fst.md`'s Prototype results section); a `[j]` offglide for `/i/` is still open.
- `phonetic2phonemic.Convert()` does not model `/ʒ/`'s free variation with `[j]` — the phonology sketch asserts both that they contrast (`[ja᷆ː]` 'mother' vs `[ʒa᷆ː]` 'monitor lizard') and that they vary freely (`[jɛ᷆ŋ]` 'sheep' vs `[ʒɛ᷆ŋ]` 'ewe'), which a transducer can't encode both of at once without merging a real contrast. `[j]` maps to `/j/` and `[ʒ]` to `/ʒ/`; the free variation is simply not modelled.
- `phonemic2orthography.Convert()` does not accept literal `/ɲ/` — real data confirms this is not merely theoretical, since the FLEx export's own emic (phonemic) field contains `ɲ` in 3 words. The composed chain never hits this, because `phonetic2phonemic.Convert()` maps `ɲ` to `nj` first, which `phonemic2orthography.Convert()` already accepts. But feeding a phonemic field containing literal `ɲ` straight to `phonemic2orthography.Convert()`, bypassing `phonetic2phonemic.py`, still hits it today.
- `phonetic2phonemic.Convert()` only strips the specific `**` annotation pattern found in one row of `real_flex_export`, by correcting the fixture rather than by a general rule; other FLEx annotation conventions in future exports are not handled and would need the same fixture-time treatment or a converter change, whichever the pattern turns out to warrant.
- Syllabic nasals, beyond the ones already in the consonant table above.
- General morphophonological rules (nasal assimilation, vowel harmony, word-boundary coalescence).
- Tone *marking* in the orthography — tone is stripped, not re-marked, since there is currently no orthographic tone convention to re-mark it with.
- Capitalisation and punctuation conventions, including hyphens.
- The orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, until real phonemic data actually uses it. `phonetic2phonemic.py`'s corresponding phonology-sketch notation is rejected outright rather than left pending, per that section above.
- A FlexTools module wrapping either converter. `pynini` doesn't support the Python .NET/IronPython runtime FlexTools modules run under on Windows, so none is planned for either.
