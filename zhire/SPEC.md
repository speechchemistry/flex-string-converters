# Zhire

The source of truth for what each converter and module in the `zhire` project does and guarantees:
the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [the root
SPEC.md](../SPEC.md) for how the projects are split up, and [AGENTS.md's Specification
section](../AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet
Specified](#not-yet-specified).

## Phonemic Transcription To Orthography

Converter: `converters/phonemic2orthography.py`. Takes and returns a plain string via `convert()`,
needs no FLEx project, and has no `flextoolslib` dependency. Turns a Zhire `[zhi]` phonemic
transcription into its orthographic spelling, per the Zhire orthography statement's
phoneme-to-grapheme correspondence tables (vowels, consonants, and a handful of sequences that don't
fall out of plain concatenation).

**Transform of `convert()`.**

1. The input is normalised to NFD, then every combining mark (Unicode category `Mn`) is deleted
   **except** the nasalisation tilde (`U+0303`) — this strips tone diacritics, since the orthography
   has no tone-marking convention yet, while keeping nasalisation.
2. The tone-stripped string is matched against a token lexicon using a finite-state transducer (built
   with [pynini](https://pypi.org/project/pynini/)), which tokenises the input into the longest
   possible sequence of known phoneme tokens (maximal munch) and maps each to its grapheme:
   - The 8 vowels `a e ɛ ə i o ɔ u`, each to its own identical-looking grapheme.
   - The 21 atomic consonants:

     | Phoneme | Grapheme |     | Phoneme | Grapheme |
     | ------- | -------- | --- | ------- | -------- |
     | b       | b        |     | p       | p        |
     | d       | d        |     | r       | r        |
     | f       | f        |     | s       | s        |
     | ɡ       | g        |     | ʃ       | sh       |
     | ɣ       | gh       |     | t       | t        |
     | h       | h        |     | v       | v        |
     | k       | k        |     | w       | w        |
     | x       | kh       |     | j       | y        |
     | m       | m        |     | z       | z        |
     | n       | n        |     | ʒ       | zh       |
     | ŋ       | ng       |     |         |          |

   - Four overrides, for sequences that plain concatenation of the atomic consonants above would get
     wrong:

     | Input sequence | Grapheme |
     | --------------- | -------- |
     | `dʒ`            | `j`      |
     | `hw`            | `wh`     |
     | `ɕw`            | `why`    |
     | `ʑw`            | `yh`     |

   - A space, mapped to itself (kept as a word divider).
   - For each of the 8 vowels: that vowel followed by the nasalisation tilde maps to itself (kept);
     that vowel followed by the IPA length mark `ː` (`U+02D0`) maps to the vowel's grapheme doubled;
     and that vowel followed by both (nasalised **and** long) maps to the nasalised grapheme doubled,
     with the tilde on each copy (e.g. `ɔ̃ː` → `ɔ̃ɔ̃`).

   Every other "complex" sequence the orthography statement documents (`ɡb`, `kp`, `ts`, `dz`, `mb`,
   `nd`, `ŋɡ`, `ndz`, `tw`, `tj`, `nj`, …) needs no table entry: concatenating the atomic consonants
   above already produces the correct grapheme sequence for these.
3. Any input that contains a symbol, or a sequence of symbols, not covered by the token lexicon above
   causes `convert()` to raise `ValueError` naming the offending input — it does not pass unmapped
   text through unchanged or silently drop it. This includes the orthography statement's
   `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, which real phonemic data doesn't currently use (it
   spells these sounds with plain letter sequences instead — see step 2's fallout above).
4. The result is normalised to NFC before being returned.

Example: `hwōrì` → `whori` (tone stripped, `hw` override applied). `ɔ̃ː` → `ɔ̃ɔ̃` (nasalised and long).

**Command line.** Text given as arguments is converted one result per line, in the order given. With
no arguments the converter reads standard input line by line and writes one converted line per input
line, so it works as a filter in a pipeline. Results go to stdout and diagnostics to stderr; stdin and
stdout are both read and written as UTF-8 regardless of the console's own encoding.

**Dependencies.** Python 3 and the `pynini` package.

## Not Yet Specified

Behaviours that are not pinned down yet. Add to the sections above as each is settled or implemented,
rather than speculating here.

- Syllabic nasals, beyond the ones already in the consonant table above.
- General morphophonological rules (nasal assimilation, vowel harmony, word-boundary coalescence).
- Tone *marking* in the orthography — tone is stripped, not re-marked, since there is currently no
  orthographic tone convention to re-mark it with.
- Capitalisation and punctuation conventions, including hyphens.
- The orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation, until real phonemic data
  actually uses it.
- A FlexTools module wrapping this converter. `pynini` doesn't support the Python .NET/IronPython
  runtime FlexTools modules run under on Windows, so none is planned.
