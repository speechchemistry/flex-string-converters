# CV Patterns

The source of truth for what each converter in the `cv-patterns` project does and guarantees: the transform rules, the source data and its reconciliation, and its prerequisites. See [the root SPEC.md](../SPEC.md) for how the projects are split up, and [AGENTS.md's Specification section](../AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only behaviour that is implemented today. Anything else belongs under [Not Yet Specified](#not-yet-specified).

Language-universal: no per-language configuration. The output alphabet is deliberately small — `C` and `V` only, with tone left to the [`chao-tone-letters`](../chao-tone-letters/SPEC.md) project.

## CV Pattern From Phonemes

Converter: `converters/phonemes2cv.py`. Takes and returns a plain string via `Convert()`, needs no FLEx project, and has no `flextoolslib` dependency. Turns a phonemic or phonetic transcription into its CV pattern, e.g. `nə̀jɛt` → `CVCVC`.

**Transform of `Convert()`.**

1. The input is normalised to NFD, then tokenised against `converters/cv_profile.tsv` (a [`segments`](https://pypi.org/project/segments/) orthography profile — see [Source data](#source-data) below) using longest match, producing one class token per recognised grapheme: `C`, `V`, `NULL`, `SYL` or `TIE` (see [The profile's three special values](#the-profiles-three-special-values)). An unrecognised symbol becomes one U+FFFD token.
2. A post-pass then applies the three rules a flat table can't express on its own, word by word (a tie bar or syllabic mark never crosses a word boundary):
   - A `TIE` token merges the class either side of it into one — `t͡ʃ` (with a tie bar) is `C`; `ɡ͡b` is `C`; `a͡ɪ` is `V`.
   - A `SYL` token promotes the immediately preceding `C` to `V` — a syllabic consonant is a vowel (`kn̩` → `CV`).
   - A `NULL` token contributes nothing to the output.
   - A U+FFFD token becomes `?` in the output, and prints one warning to stderr naming the symbol and the input string it appeared in. This never raises and the exit status stays 0 (as `chao2diacritics.py` already does), so a FLEx Process can't blank a field or abort a bulk edit over one stray character.
3. Word boundaries survive as a single space, so a multi-word field stays readable (`ab ec` → `VC VC`). A word that reduces to no class symbols at all (e.g. one made only of tone letters) is dropped entirely rather than left as an empty word, so the output never has doubled or trailing spaces.
4. A digraph is one phone only when a tie bar joins it. `t͡ʃ` is `C`; bare `tʃ` is `CC`. **Clicks are the one exception**: an accompaniment letter plus a click letter (`ŋǃ`, `kǀ`, `ⁿgǂ`, `gʘ`, `ǃǃ`, …) is always one `C`, tie bar or not, because unlike `kh` or `pt` the sequence is unambiguous — a nasal-plus-click cluster is not a thing in any language.
5. Glides are consonants (`waj` → `CVC`), a syllabic consonant is a vowel (`kn̩` → `CV`), and a vowel sequence is one `V` per vowel unless a tie bar joins them (`aɪ` → `VV`, `a͡ɪ` → `V`).
6. Tone is recognised and contributes nothing, whether written as a diacritic on a vowel or as a standalone tone letter — so `diacritics2chao.py`'s own output composes straight through: `nəjɛt ˨ ˨˧` → `CVCVC`.

**Consequence to accept.** Real data often omits the tie bar. A FLEx project whose transcriptions follow the IPA chart or PHOIBLE convention will have `tʃ`, `ts`, `dʒ`, `kp` written bare, and this converter calls each of them `CC`. That is the decided behaviour, and it is defensible — it never guesses that a sequence is one phone — but a user seeing `CCV` for what they consider a `CV` word is not seeing a bug. It is the strongest argument for a later per-language override or wrapper (see [Not Yet Specified](#not-yet-specified)).

**Command line.** Text given as arguments is converted one result per line, in the order given. With no arguments the converter reads standard input line by line and writes one converted line per input line, so it works as a filter in a pipeline. Results go to stdout, warnings to stderr; stdin, stdout and stderr are all read and written as UTF-8 regardless of the console's own encoding.

**Dependency.** The [`segments`](https://pypi.org/project/segments/) package (`pip install segments`), the orthography-profile tokeniser from Moran & Cysouw's Unicode Cookbook. It pulls in `csvw`, `clldutils` and `regex` (`regex` is already needed by [`chao-tone-letters`](../chao-tone-letters/SPEC.md)).

### The profile's three special values

`converters/cv_profile.tsv` has exactly two columns, `Grapheme` and `CV`. Besides `C` and `V`, the `CV` column takes three other values:

- **`NULL`** — recognised, contributes nothing: every tone row, the markers table, and every diacritic row except the syllabic ones. This is the literal string `NULL`, not an empty cell — `segments.Profile.from_file()` maps the literal string `NULL` in a non-`Grapheme` column to `None`, which is skipped entirely when transforming; an empty cell instead emits an empty token, which showed up as a doubled space (`tãn` → `V  C`) when tried directly against `segments`.
- **`TIE`** — U+0361 and U+035C as standalone rows. The post-pass merges `X TIE Y` into a single `X`, which is what makes `t͡ʃ`, `ɡ͡b` and `a͡ɪ` work without listing a single tie-barred combination by name.
- **`SYL`** — U+0329 and U+030D as standalone rows. The post-pass promotes the preceding `C` to `V` and drops the sentinel, covering every syllabic consonant BIPA doesn't already list outright (see [Source data](#source-data)).

## Source data

The profile (`converters/cv_profile.tsv`) is generated by `tools/build_cv_profile.py` from **CLTS's BIPA transcription system**, release **v2.3.0** (`pkg/transcriptionsystems/bipa/` in [cldf-clts/clts](https://github.com/cldf-clts/clts), DOI [10.5281/zenodo.3515744](https://doi.org/10.5281/zenodo.3515744)): 729 consonant graphemes, 326 vowels, 132 tones, 115 diacritics, 6 markers, and a 46-row normalisation table. A tagged release is pinned rather than `master` so the profile can be re-derived from the same document later; re-run the generator (which re-asserts every row count below and fails loudly if BIPA has changed) whenever the pinned tag is bumped. Licence CC-BY-4.0 — see [Licensing and attribution](#licensing-and-attribution).

BIPA is a grapheme grammar rather than a word list: it separates base graphemes from diacritics and records for each diacritic whether it attaches before or after its base (`◌ʷ` vs `ᵐ◌`), which is exactly the decomposition this converter needs — a diacritic that isn't part of a listed grapheme still costs nothing, because its own row deletes itself from the token stream.

**PHOIBLE is not the source; it is the independent net.** [PHOIBLE](https://github.com/phoible/dev)'s segment feature table (3000+ doculects, 2100+ ISO codes, 2162 segments with a `syllabic` feature) has no base/diacritic decomposition for 2056 of its 2162 segments, so it cannot say what to do with a segment it has never seen — but it fails in the opposite direction from a BIPA-derived check, by containing real attested segments BIPA's own tables might not cover. Its `data/` directory is MIT-licensed.

Neither source writes affricates with a tie bar — PHOIBLE has zero tie bars in 2162 segments (`t̠ʃ`, `ts`, `tʃ`), and BIPA's `normalize.tsv` actively strips `◌͡◌` and `◌͜◌`. The tie-bar rule is therefore ours, not inherited, and is implemented by leaving rows out (below) rather than by trusting the source's own segmentation.

### Reconciling BIPA

Every row of each table lands in exactly one bucket, and the buckets sum to the source total. The generator (`tools/build_cv_profile.py`) asserts every count below; re-run it and re-check this reconciliation whenever the pinned tag changes.

- **Consonants, 729 rows, in three buckets**, split by counting base letters (Unicode category Ll/Lu/Lo, after NFD) and by BIPA's own `MANNER` column:
  - **532 single-base rows** (at most one base letter, any number of diacritics) become `C`.
  - **48 multi-base click rows** (`MANNER` ending in `click`, e.g. `ŋǃ`, `kǀ`, `gʘ`, `ǃǃ`) are **also** `C` — the click exception, below.
  - **149 remaining multi-base rows** (`ts`, `tʃ`, `kp`, `ŋm`, `nm`, `pt`, `th`, …) are **excluded**: including them would make a bare, tie-less digraph a single `C`, against the tie-bar decision. They segment into their parts instead and come out `CC`.
  - Of the 580 rows kept (532 + 48), **25** are syllabic — BIPA's own `EXTRA` column says `syllabicity:syllabic` — and get `V` instead of `C`. 22 carry the combining mark U+0329 or U+030D (`n̩`, `l̩`, `ɹ̩`, `s̩`, …); the other 3 (`ḷ`, `ṇ`, `ṃ`) are Indological dot-below transliterations of the same alias with no such mark at all, found only by checking `EXTRA` directly rather than the mark alone — the mark-only check this generator started with silently missed all three.
- **Vowels, 326 rows.** All become `V`. None has more than one base letter, so `aɪ` → `VV` needs no exclusion — it falls out, and a test confirms that rather than asserting it.
- **Diacritics, 115 rows.** All are `NULL` (with the `◌` placeholder stripped from the grapheme), except the 4 rows whose `FEATURE` is `syllabicity`: `VALUE=syllabic` (`◌̩`, `◌̍`) becomes `SYL`; `VALUE=non-syllabic` (`◌̯`, `◌̑`) stays `NULL`.
- **Tones, 132 rows**, and the **6-row markers table**: `NULL`.
- **`normalize.tsv`, 46 rows, and it is not optional.** BIPA's tone table is written in superscript digits (`¹¹`, `²³`), so the Chao tone letters `˥ ˦ ˧ ˨ ˩` appear nowhere but this table — skip it and `diacritics2chao.py`'s own output (`nəjɛt ˨ ˨˧`) comes back full of `?`. Each row is a `SOURCE` → `TARGET` alias; the generator resolves `TARGET`'s class (by direct lookup, or by tokenising and reducing it exactly as `Convert()`'s own post-pass would) and gives `SOURCE` that same class, with four named exceptions:
  - `ǧ`, `ǯ`, `ǰ` → `dʒ` are each hand-assigned `C`: a *single character* standing for the affricate `dʒ` is one phone, unlike the two-letter spelling (which is `CC`, per the tie-bar rule).
  - `|` → `|` (a self-referential row, not an alias to anything else in the tables) is hand-assigned `NULL`: it is BIPA's own notation for a prosodic/foot boundary, not one of the 6 rows in `markers.tsv`, but the same kind of thing they are.
  - The 2 tie-bar rows (`◌͡◌`, `◌͜◌`) become standalone `TIE` rows.
  - A `SOURCE` that is itself a bare diacritic template (`◌̱` → `◌̠`) is resolved against the diacritic it aliases, not against the generic tokenise-and-reduce path.
- **Alias rows are kept** (BIPA marks them `+` in its `ALIAS` column). They are non-canonical spellings of the same sound, which is exactly what messy real-world FLEx data contains.

### Beyond BIPA

Two small, named additions sit on top of the BIPA-derived table above, both found by testing rather than assumed:

- **6 combining contour tone diacritics** (U+1DC4–U+1DC9: `᷄ ᷅ ᷆ ᷇ ᷈ ᷉`) as `NULL`, taken from this repository's own [`chao-tone-letters/converters/diacritics2chao.py`](../chao-tone-letters/converters/diacritics2chao.py). BIPA v2.3.0 covers 7 of the 13 tone diacritics that converter recognises (the plain accent marks) but not these 6. Found when the `words.txt` approval fixture below — real Zhire phonetic data, which uses exactly these marks — turned every tone-marked syllable into `?`. Without them, the "so the two projects compose" guarantee above would only hold for `diacritics2chao.py`'s *output* (bare Chao tone letters), not for tone-marked input on its way in.
- **2 further IPA diacritics**, dental (U+032A, `◌̪`) and linguolabial (U+0347, `◌͇`), as `NULL`. Confirmed missing from both `diacritics.tsv` and `tones.tsv` — found by the PHOIBLE coverage test below, which is the independent net over BIPA precisely so a gap like this surfaces on real attested segments. Unlike the tone marks above, nothing else in this repository already depends on these; they were added because they are themselves ordinary IPA, not because of another converter's contract.

## Test fixtures

- **`words.txt`** is real data: the phonology sketch's own example words, reused from [`zhire/tests/fixtures/phonetic2phonemic/inputs/phonology_sketch_examples.txt`](../zhire/tests/fixtures/phonetic2phonemic/inputs/phonology_sketch_examples.txt) rather than inventing anything, and approved through the ordinary promote loop. It demonstrates the tie-bar consequence directly on attested data: `ɡbàk`, `mba᷄ŋ`, `ndɛ̀n`, `ŋmɡba᷆n`, `nzo᷇ɾ`, `twɔ᷅ŋ`, `tjɛ᷅ɾ`, `hwók`, `ɕwè`, `ʑwú` and `kpi᷆ː` all come out with the bare cluster as `CC` (or, for the 4-consonant `ŋmɡb`, `CCCC`).
- **`bipa_graphemes`** is a source-derived fixture (see [`checking-a-converter-against-its-source`](../.claude/skills/checking-a-converter-against-its-source/SKILL.md)): one line per row of BIPA's `consonants.tsv` that survived the reconciliation above, `vowels.tsv`, and `tones.tsv` — 1038 rows total (580 + 326 + 132) — with the approved side giving each its expected pattern (`C`, `V`, or empty for a tone). Built by `tools/build_bipa_graphemes_fixture.py` directly from a fresh read of BIPA's tables, independently of `cv_profile.tsv` and never by promoting `Convert()`'s own output — otherwise the fixture could only ever confirm what the converter already does. Uses the ordinary CLI approval harness (it's just another `inputs`/`approved` pair), so a row silently dropped on the way into `cv_profile.tsv` fails a test instead of surviving unnoticed.
- **`phoible_segments.txt`** is the independent-net check: the `segment` column of PHOIBLE's own segment feature table (`raw-data/FEATURES/phoible-segments-features.tsv`), pinned at commit `fd7894c10e6f894ac37f3e22765d15504b8eb25d` of [phoible/dev](https://github.com/phoible/dev) (PHOIBLE has no tagged releases), 2162 distinct segments, built by `tools/build_phoible_segments_fixture.py`. `tests/test_phonemes2cv_source.py` asserts, entirely offline, that `Convert()` produces no *unexpected* `?` against any of them — a tieless affricate or other bare digraph PHOIBLE lists is expected to come out `CC`, per the tie-bar decision, which is a real answer, not a `?`. 23 of the 2162 segments are named exceptions in that test, reviewed and accepted as PHOIBLE-specific or otherwise non-standard notation rather than a BIPA coverage gap: a double-click notation (`‼`, 12 segments) BIPA spells differently; a raised capital `ᴱ` (3 segments) and a small-capital `ᴅ` (3 segments), both idiosyncratic to PHOIBLE rather than general IPA; and 5 asterisk-prefixed segments (`*R`, `*Rʲ`, `*R̪`, `*R̪̥`, `*R̪̰`), which are PHOIBLE's own marker for something other than a transcribed phone. The exceptions are named explicitly rather than only counted, so a *different* segment producing `?` — a real regression, or a genuinely new gap — still fails the test instead of silently fitting under a number. Two earlier findings from this same test were real BIPA gaps, not PHOIBLE quirks, and are fixed in the profile instead of listed here — see [Beyond BIPA](#beyond-bipa).

## Licensing and attribution

BIPA is CC-BY-4.0 (`"dc:license"` in CLTS's `cldf-metadata.json`, matching its `.zenodo.json`; there is no `LICENSE` file at the repository root, which is why the licence has to be read from the metadata) — attribution-only, so a generated TSV can sit in this MIT-licensed repository without changing its licence. `cv_profile.tsv` carries its own credit, title, licence and link in a comment header, and states there that it is a derived, filtered and reclassified copy (rows filtered to the three consonant buckets, a `CV` column derived from the source's own `MANNER`/`TYPE`/`FEATURE` columns and table membership, and the two small additions in [Beyond BIPA](#beyond-bipa)). Cite CLTS as List, Anderson, Tresoldi, Rzymski & Forkel, with the Zenodo DOI and the pinned `v2.3.0`, in any further reuse.

PHOIBLE, used only for the coverage test, is MIT-licensed in its `data/` directory (the repository as a whole reports GPL-3.0 for its scripts, which this project does not use).

## Not Yet Specified

Behaviours that are not pinned down yet. Add to the sections above as each is settled or implemented, rather than speculating here.

- A `CVN` (or richer sound-class) variant, marking nasals as `N`, as a thin wrapper in the style of `diacritics2chao_tone_letters_only.py` rather than a change to `phonemes2cv.py` itself.
- Per-language overrides for the tie-bar and digraph rules — see [Consequence to accept](#consequence-to-accept).
- Tone in the output. Tone is recognised and contributes nothing; re-marking it in the CV pattern itself is a different, unbuilt feature.
- A FlexTools module. FLEx's Pronunciation object has a built-in **CV Pattern** field, which is the natural target when a module is added, so no custom field will be needed.
