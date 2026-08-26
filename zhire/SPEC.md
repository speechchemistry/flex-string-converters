# Zhire

The source of truth for what each converter and module in the `zhire` project does and guarantees: the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [the root SPEC.md](../SPEC.md) for how the projects are split up, and [AGENTS.md's Specification section](../AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet Specified](#not-yet-specified).

## Phonemic Transcription To Orthography

Converter: `converters/phonemic2orthography.py`. Takes and returns a plain string via `convert()`, needs no FLEx project, and has no `flextoolslib` dependency. Turns a Zhire `[zhi]` phonemic transcription into its orthographic spelling, per the Zhire orthography statement's phoneme-to-grapheme correspondence tables (vowels, consonants, and a handful of sequences that don't fall out of plain concatenation).

**Transform of `convert()`.**

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

   Every other sequence the orthography statement documents (`ɡb`, `kp`, `ts`, `dz`, `mb`, `nd`, `ŋɡ`, `ndz`, `tw`, `tj`, `nj`) needs no table entry: concatenating the atomic consonants above already produces the correct grapheme. This is now an exhaustive claim rather than an illustrative list — every phoneme row in the statement is checked against `convert()` by the `orthography_statement_phonemes` fixture, so a sequence that needs an entry and lacks one fails a test.
3. Any input that contains a symbol, or a sequence of symbols, not covered by the token lexicon above causes `convert()` to raise `ValueError` naming the offending input — it does not pass unmapped text through unchanged or silently drop it. This includes the orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, which real phonemic data doesn't currently use (it spells these sounds with plain letter sequences instead — see step 2's fallout above). The check applies to base letters and their sequences; combining marks never reach it, having already been dropped or kept by step 1.
4. The result is normalised to NFC before being returned.

Example: `hwōrì` → `whori` (tone stripped, `hw` override applied). `ɔ̃ː` → `ɔ̃ɔ̃` (nasalised and long).

**Command line.** Text given as arguments is converted one result per line, in the order given. With no arguments the converter reads standard input line by line and writes one converted line per input line, so it works as a filter in a pipeline. Results go to stdout and diagnostics to stderr; stdin and stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Test fixtures.** Two kinds, with different jobs:

- `words` and `loanwords` are real phonemic/orthographic word pairs supplied by the language consultant, promoted through the normal approval loop. They are the regression net for real data.
- `orthography_statement_phonemes` is derived from `zhi_orthography_statement.md` (on the NRG Language Drive): one line per phoneme row in its vowel, consonant and modified-sound tables, with the statement's own grapheme column as the approved output. Both sides come from the statement, not from the converter — see [AGENTS.md's Testing Approach](../AGENTS.md#testing-approach) on why the promote loop is wrong for a spec-derived fixture. Rows written with the statement's `ʷ`/`ʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier letters are transliterated to the plain-letter notation real data uses (`ᵐb` to `mb`, `ᵑᵐɡb` to `ŋmɡb`, `tʲ` to `tj`, and so on), and where a row gives two alternatives the first is used. Re-derive it whenever the statement's tables change; it is a snapshot, so it cannot notice that on its own.

  This fixture is what makes the inventory claims above exhaustive rather than illustrative. It exists because three phonemes (`/l/`, `/tʃ/`, `/ŋmɡb/`) were each found missing one at a time, by a held-out word or by a human reading the source, after a 99/99 pass against the sample corpus had been mistaken for a completeness check.

**Dependencies.** Python 3 and the `pynini` package.

## Not Yet Specified

Behaviours that are not pinned down yet. Add to the sections above as each is settled or implemented, rather than speculating here.

- Phonetic input. `convert()` takes phonemic input, so the orthography statement's worked examples — which are phonetic — are not valid input as written. Three allophone correspondences were observed while checking them against the statement and are **not implemented or confirmed**: `[ɨ]` for `/ə/`, `[ɛ]` for `/e/` in a closed syllable, and a `[j]` offglide for `/i/`. Accepting phonetic input would be a separate feature, and would need those rules settled first.
- Syllabic nasals, beyond the ones already in the consonant table above.
- General morphophonological rules (nasal assimilation, vowel harmony, word-boundary coalescence).
- Tone *marking* in the orthography — tone is stripped, not re-marked, since there is currently no orthographic tone convention to re-mark it with.
- Capitalisation and punctuation conventions, including hyphens.
- The orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, until real phonemic data actually uses it.
- A FlexTools module wrapping this converter. `pynini` doesn't support the Python .NET/IronPython runtime FlexTools modules run under on Windows, so none is planned.
