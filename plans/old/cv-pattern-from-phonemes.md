# CV pattern from a phoneme string

**Status:** Proposed and implemented 2026-09-08. See [Changes after approval](#changes-after-approval) for what was decided during implementation.

A new language-universal project folder, `cv-patterns/`, whose converter turns a phonemic or phonetic string into its CV pattern: `nə̀jɛt` → `CVCVC`. The first release is deliberately small — two class symbols, no per-language configuration — because the shape of the problem is in the segmentation, not in the alphabet.

## Decisions this plan implements

These were settled in discussion before the plan was written.

- **Output alphabet is `C` and `V` only.** Tone stays with the `chao-tone-letters/` project, so tone letters and tone diacritics are recognised and contribute nothing to the pattern. A `CVN` variant (nasals as `N`) is a later addition, as a thin wrapper in the style of `diacritics2chao_tone_letters_only.py`, not a v1 feature.
- **Language-universal, with no per-language override.** One table, one behaviour. An override mechanism waits until a real language needs one.
- **A digraph is one phone only when a tie bar joins it.** `t͡ʃ` is `C`; bare `tʃ` is `CC`. Clicks are the one exception, for the reason given in [Why the tie-bar rule survived a second look](#why-the-tie-bar-rule-survived-a-second-look). See also [Consequence to accept](#consequence-to-accept) — this remains the highest-risk decision in the plan.
- **Glides are consonants** (`waj` → `CVC`), **a syllabic consonant is a vowel** (`kn̩` → `CV`), and **a vowel sequence is one `V` per vowel** (`aɪ` → `VV`).
- **An unrecognised symbol becomes `?` in the output, with a warning naming the line on stderr.** The exit status stays 0, as `chao2diacritics.py` already does, so a FLEx Process cannot blank a field or abort a bulk edit over one stray character.
- **`segments` does the tokenising** — the orthography-profile tokeniser from Moran & Cysouw's Unicode Cookbook. `pip install segments` works out of the box; it pulls in `csvw`, `clldutils` and `regex` (`regex` is already needed by `chao-tone-letters/`).

## Why BIPA is the source, and what PHOIBLE is for

The table comes from **CLTS's BIPA transcription system**, release **v2.3.0** (`pkg/transcriptionsystems/bipa/` in [cldf-clts/clts](https://github.com/cldf-clts/clts), DOI [10.5281/zenodo.3515744](https://doi.org/10.5281/zenodo.3515744)): 729 consonant graphemes, 326 vowels, 132 tones, 115 diacritics, plus a markers and a normalisation table. A tagged release is pinned rather than `master` so the copy can be re-derived from the same document later; the generator records the tag it read. BIPA is a grapheme grammar rather than a word list — it separates base graphemes from diacritics and records for each diacritic whether it attaches before or after its base (`◌ʷ` vs `ᵐ◌`) — which is the same decomposition Phonology Assistant's parser relies on, and exactly the shape this converter needs. Licence CC-BY-4.0, so it needs an attribution line and nothing more.

**PHOIBLE is not the source; it is the independent net.** It is a database of what inventories are attested (3000+ doculects, 2100+ ISO codes), and its segment feature table lists 2162 segments with a `syllabic` feature. But 2056 of those 2162 are multi-codepoint bundles with no base/diacritic decomposition recorded, so PHOIBLE cannot say what to do with a segment it has never seen, whereas BIPA can. Its value here is that it fails in the opposite direction from a BIPA-derived test: a coverage test over its 2162 segments would surface anything BIPA's tables omit. Its `data/` directory is MIT-licensed.

Neither source writes affricates with a tie bar — PHOIBLE has zero tie bars in 2162 segments (`t̠ʃ`, `ts`, `tʃ`), and BIPA's `normalize.tsv` actively strips `◌͡◌` and `◌͜◌`. The tie-bar rule is therefore ours, not inherited, and is implemented by leaving rows out (below) rather than by trusting the source's own segmentation.

## Reconciling the source

Per [AGENTS.md's External Specifications](../../AGENTS.md#external-specifications), every row of each BIPA table lands in exactly one bucket, and the buckets must sum to the source total. Stated here as the intended reconciliation; the generator script asserts it.

- **Consonants, 729 rows, in three buckets.** 532 single-base rows become `C` in the profile. 48 rows are multi-base clicks (`ŋǃ`, `kǀ`, `gʘ`, `ǃǃ`, …) and are **also included** as `C`, per the click exception below. The remaining 149 rows have more than one base letter, no tie bar and no click (`ts`, `tʃ`, `kp`, `ŋm`, `nm`, `pt`, `th`, …) and are **deliberately excluded**, since including them would make bare `tʃ` a single `C` against the tie-bar decision; they segment into their parts instead and come out `CC`. 532 + 48 + 149 = 729.
- **Vowels, 326 rows.** All become `V`. None has more than one base letter, so `aɪ` → `VV` needs no exclusion — it falls out, and a test will confirm that rather than assert it.
- **Diacritics, 115 rows.** All are in the profile as `NULL`, so a diacritic never occupies a slot: `tʷ`, `tʲ`, `kʰ`, `ᵐb`, `ʰt` and `ã` are each one `C` or `V`. The four rows carrying `syllabicity` are the exception — `◌̩` and `◌̍` become the `SYL` sentinel, `◌̯` and `◌̑` stay `NULL` — and the `◌` placeholder is stripped when writing a grapheme, so `◌ʷ` and `ᵐ◌` both contribute a plain one-codepoint row.
- **Tones, 132 rows**, and the markers table: recognised, `NULL`. This is what keeps tone out of the pattern without making it an unknown symbol — panphon, by contrast, classifies `˥˩` as two consonants.
- **Markers, 6 rows** (`¯`, `+`, `_`, `→`, `←`, `∼`): `NULL`.
- **`normalize.tsv`, 46 rows, and it is not optional.** BIPA's tone table is written in superscript digits (`¹¹`, `²³`), so **the Chao tone letters `˥ ˦ ˧ ˨ ˩` appear nowhere but this table** — skip it and `nəjɛt ˨ ˨˧`, which is `diacritics2chao.py`'s own output, comes back full of `?` and the two projects in this repository fail to compose. Each row is a `SOURCE` → `TARGET` alias, so the generator gives `SOURCE` the class it resolves for `TARGET`: the 5 Chao letters and the digits `1`–`5` become `NULL` via the tone table, `:` → `ː` is `NULL`, `!` → `ǃ` is `C`, `ḷ` → `l̩` is `V`, `ǧ`/`ǯ`/`ǰ` → `dʒ` is `C` (a single character standing for an affricate is one phone, unlike the two-letter spelling), and the 2 tie-bar rows (`◌͡◌`, `◌͜◌`) become `TIE`.
- **Alias rows are kept** (BIPA marks them `+` in its `ALIAS` column). They are non-canonical spellings of the same sound, which is exactly what messy real-world FLEx data contains.

## How it works

A flat profile plus a very small post-pass, rather than a rule engine.

1. `cv-patterns/converters/cv_profile.tsv` is a `segments` orthography profile with a `Grapheme` column and a `CV` column, generated from the BIPA tables above. Longest match handles the multi-codepoint graphemes BIPA does list, and a diacritic that isn't part of a listed grapheme still costs nothing because its own row deletes itself.
2. `segments` tokenises the input against that profile. An unlisted grapheme comes back as one U+FFFD, which the converter turns into one `?` plus the stderr warning — nothing is ever silently dropped, which is the failure mode that rules panphon out.
3. A post-pass then handles the three things a flat table cannot express: a tie bar between two tokens collapses them into one class symbol, so any tie-barred combination works generatively including ones no table lists (`ɡ͡b`, `k͡p`, `t͡s`, and `a͡ɪ` as a single `V`); a syllabic mark promotes its `C` to `V`, covering the syllabic consonants beyond the 22 BIPA lists outright; and the word boundary token becomes a space again.
4. Spaces are therefore preserved, as Phonology Assistant does (`ab ec` → `VC VC`), so a multi-word field stays readable.

`Convert(input_string)` and a CLI per the usual conventions; the profile is found relative to `__file__`.

## Worked examples

These are the acceptance check: every row is a unit test, and together they cover each rule in this plan.

| Input | Output | Why |
| --- | --- | --- |
| `nə̀jɛt` | `CVCVC` | a tone diacritic contributes nothing; `j` is a consonant |
| `nəjɛt ˨ ˨˧` | `CVCVC` | tone letters contribute nothing, and a word that reduces to nothing leaves no stray space — this input is `diacritics2chao.py`'s own output, so the two projects compose |
| `tʷa`, `kʰat`, `ᵐba`, `ʰta` | `CV`, `CVC`, `CV`, `CV` | a diacritic never takes a slot, before or after its base |
| `t͡ʃa` vs `tʃa` | `CV` vs `CCV` | the tie-bar rule, and the consequence a user will query |
| `ŋǃa` | `CV` | the click exception |
| `kn̩` | `CV` | a syllabic consonant is a vowel — and `n̩` is one of the 22 BIPA lists, so this is the case the generator has to get right |
| `aɪ` vs `a͡ɪ` | `VV` vs `V` | one `V` per vowel unless a tie bar joins them |
| `ˈtata` | `CVCV` | stress is recognised and contributes nothing |
| `ab ec` | `VC VC` | spaces survive |
| `7a` | `?V` | unknown symbol, plus one warning on stderr naming the line; exit status still 0 |

The second row implies one small rule worth stating outright: after the post-pass, a word that produced no class symbols is dropped rather than left as an empty word, so the output has no doubled or trailing spaces.

## The profile's three special values

`Grapheme` and `CV` are the only columns. Besides `C` and `V`, the `CV` column takes exactly three other values, which is what keeps the post-pass to a few lines:

- **`NULL`** — recognised, contributes nothing: all 132 tone rows, the markers table, and every diacritic row except the syllabic ones. This is a literal `NULL`, not an empty cell; see the mechanics below.
- **`TIE`** — U+0361 and U+035C as standalone rows. The post-pass merges `X TIE Y` into a single `X`, which is what makes `t͡ʃ` one `C`, `ɡ͡b` one `C` and `a͡ɪ` one `V` without listing a single combination.
- **`SYL`** — U+0329 and U+030D as standalone rows. The post-pass promotes the preceding `C` to `V` and drops the sentinel, covering the syllabic consonants BIPA does not list outright. The non-syllabic marks U+032F and U+0311 get `NULL` in v1, since demoting a vowel to `C` would be wrong.

## Verified mechanics — do not re-derive these

Each of these four was tested against `segments` rather than assumed, because guessing any of them yields a plausible-looking wrong answer rather than an error.

- **Delete a grapheme with the literal string `NULL`, never an empty cell.** An empty cell emits an empty token: `tãn` came back as `V  C`, with a doubled space where the nasalisation had been. `NULL` removes it cleanly.
- **A space comes back as `#`, not as a space.** `ab ec` tokenises to `V C # V C`, so the post-pass maps the boundary token back to a single space. "Spaces are preserved" costs a line of code; it is not free.
- **The converter must NFD-normalise its input itself; `Tokenizer(..., form='NFD')` does not do it.** With an NFD profile, a precomposed (NFC) `ã` came back as an unknown symbol, and passing `form='NFD'` did not fix it. So the generator writes profile graphemes in NFD and the converter calls `unicodedata.normalize('NFD', ...)` on the way in — the same thing [`diacritics2chao.py`](../../chao-tone-letters/converters/diacritics2chao.py) already does, and it must be tested both ways round.
- **A listed syllabic consonant has to be given `V` by the generator, not by the post-pass.** BIPA lists 22 of them (`n̩`, `l̩`, `ɹ̩`, `s̩`, …). Longest match consumes the syllabic mark *inside* the grapheme, so the post-pass never sees a `SYL` token and `n̩` comes out `C` — tested, and confirmed wrong. The generator therefore assigns `V` to any consonant grapheme containing U+0329 or U+030D, and the `SYL` sentinel only has to cover the unlisted cases.

## Why the table is a TSV

**The profile is a checked-in TSV, not a literal inside the `.py`** (decided in discussion). A generated data file sitting beside a converter is new for this repo, so it is worth noting as a deliberate extension of [Converter Conventions](../../AGENTS.md#converter-conventions) — it is not another converter being imported, it is the converter's own data. A TSV earns it: 1000 rows as a Python literal would swamp the logic in the file a FLEx Process points at, a row change shows up as a one-line diff, and the file stays in `segments`' own profile format, so a user can open it in a spreadsheet or reuse it with the rest of the Unicode Cookbook toolchain. The generator lives at `cv-patterns/tools/build_cv_profile.py`, outside `converters/` so FlexTools never sees it, and records in the TSV header the CLTS release it read.

## Files to create

- `cv-patterns/SPEC.md` — the project's contract: the transform rules, the source and its reconciliation, and the tie-bar consequence.
- `cv-patterns/converters/phonemes2cv.py` — `Convert(input_string)` plus a CLI, per [Converter Conventions](../../AGENTS.md#converter-conventions) and [CLI Script Conventions](../../AGENTS.md#cli-script-conventions). No `flextoolslib` import.
- `cv-patterns/converters/cv_profile.tsv` — generated, checked in, licence header at the top.
- `cv-patterns/tools/build_cv_profile.py` — the generator. It downloads all six BIPA TSVs by raw URL at the `v2.3.0` tag (`consonants`, `vowels`, `tones`, `diacritics`, `markers`, `normalize` — no repo clone), asserts the row counts it expects (`532 + 48 + 149 == 729` consonants, 326 vowels, 132 tones, 115 diacritics, 6 markers, 46 normalise rows) and fails loudly if the source has changed, and writes the licence and provenance header. Sitting outside `converters/` keeps it away from the FlexTools scanner.
- `cv-patterns/tests/conftest.py` — copy the shape of [`zhire/tests/conftest.py`](../../zhire/tests/conftest.py): this project's `converters/` and the repository's shared `tests/` on `sys.path`.
- `cv-patterns/tests/test_phonemes2cv.py` and `cv-patterns/tests/test_phonemes2cv_cli.py`.
- `cv-patterns/tests/fixtures/phonemes2cv/{inputs,approved}/` — see [Tests](#tests).
- Edits to the root `SPEC.md` (index entry) and `README.md` (a section, the `segments` dependency, the Attributions line).

No FlexTools module and no `__pycache__`-style stray files; nothing in this project folder needs a module file yet.

## Implementation order

Follow [AGENTS.md's TDD rule](../../AGENTS.md#testing-approach) — the point of this order is that the generator's assertions and the unit tests both fail before anything works.

1. Write `build_cv_profile.py`, run it, and confirm the bucket assertions pass against v2.3.0. The generated TSV is the input to everything else.
2. Write the unit tests from the [Tests](#tests) list and confirm they fail.
3. Write `phonemes2cv.py` until they pass: tokenise, then the post-pass (`TIE` merge, `SYL` promotion, `#` → space, U+FFFD → `?` plus one stderr warning naming the line).
4. Add the approval fixtures via the [`adding-an-approval-fixture`](../../.claude/skills/adding-an-approval-fixture/SKILL.md) skill — read each received file before promoting it, never write into `approved/` by hand.
5. Write `SPEC.md`, the root index entry and the README section last, when the behaviour is settled.

## Licensing and attribution

BIPA is **CC-BY-4.0** (`"dc:license"` in the CLTS `cldf-metadata.json`, matching its `.zenodo.json`; there is no `LICENSE` file at the repo root, which is why the licence has to be read from the metadata). That is attribution-only — no share-alike, no copyleft — so a generated TSV can sit in this MIT repository without changing its licence, and this is a milder case than the LGPL module file the README already carves out.

What CC-BY-4.0 asks for, and where each part goes:

- **Credit, title, licence and a link**: a comment header in `cv_profile.tsv` itself, so the file carries its own provenance wherever it is copied; the source section of `cv-patterns/SPEC.md`; and the README's Attributions line. Cite CLTS as List, Anderson, Tresoldi, Rzymski & Forkel, with the Zenodo DOI and the pinned `v2.3.0`.
- **An indication that changes were made**, which they were: rows filtered to three buckets, tieless non-click digraphs dropped, and a `CV` column derived from the source's own `MANNER` and table membership. The `SPEC.md` reconciliation already states this; the TSV header will say it too.

The generator script is the honest way to satisfy the spirit of it as well — anyone can re-run it against v2.3.0 and see exactly what was taken and what was changed.

PHOIBLE, used only for the coverage test, is MIT in its `data/` directory (the repository as a whole reports GPL-3.0 for its scripts, which we do not use). Cite it if any of its segments end up checked in as a fixture.

**No dependency can supply this data instead**, which is the other half of the question:

- `segments` deliberately ships no universal profile — in the Unicode Cookbook model a profile is a per-language artifact, which is exactly the piece we are contributing.
- `pyclts` bundles only `clicks.tsv` and a test file; it reads the BIPA tables from a *cloned* CLTS repository registered in `~/.config/cldf/catalog.ini`, and fails out of the box after `pip install`. That install friction is why it was rejected as a runtime dependency, and it means depending on it would not get us the data anyway.
- `panphon` does bundle a segment table, but it records no base-versus-diacritic distinction and classifies the Chao tone letters as consonants, so it is the wrong source as well as the wrong parser.

So the table has to be generated and checked in. Being data derived from a citable, versioned source rather than a runtime import is also what makes the [`checking-a-converter-against-its-source`](../../.claude/skills/checking-a-converter-against-its-source/SKILL.md) workflow apply to it.

## Why the tie-bar rule survived a second look

The rule was reconsidered on the grounds that dropping it — taking BIPA's own segmentation wholesale, which needs no exclusion bucket — might be simpler. Reading the 197 multi-base rows shows it would not be a simplification but a correctness problem, so the rule stays.

BIPA lists as single graphemes `pt`, `bd`, `kt`, `tk`, `pk`, `tp`, `dg`, `gd`, `nm` and `ʔh`, and additionally lists `kh`, `ph`, `th` and `kw` as aliases of the aspirated and labialised stops. Accepting those would make `apta` → `VCV` and `kha` → `CV`. Every one of those sequences is an ordinary two-phoneme cluster in far more languages than it is a single phone, so the cost is wrong answers, not just a different convention — and wrong answers governed by a 149-row list the user never sees, which is worse for a survey tool than a rule that can be stated in one sentence.

It also saves almost no code. Tie bars have to be handled either way, because BIPA's `normalize.tsv` strips them, so an untreated `t͡ʃ` would come back as an unknown symbol. The whole difference is stripping the tie bar before tokenising versus merging two tokens after it — a few lines.

**The click exception.** 48 of the 197 are clicks, where an accompaniment letter precedes the click symbol (`ŋǃ`, `kǀ`, `ⁿgǂ`, `gʘ`, and `ǃǃ`). Nobody writes a tie bar in them, and unlike `kh` or `pt` the sequence is unambiguous — a nasal-plus-click cluster is not a thing in any language — so these are included as single `C`s. The test is `MANNER` ending in `click`, so it is one filter over the source data rather than a hand-kept list, and it keeps the converter from being wrong about every click language.

## Consequence to accept

Real data often omits the tie bar. A FLEx project whose transcriptions follow the IPA chart or PHOIBLE convention will have `tʃ`, `ts`, `dʒ`, `kp` written bare, and this converter will call each of them `CC`. That is the decided behaviour and it is defensible — it never guesses that a sequence is one phone — but it must be stated plainly in `SPEC.md` and in the README section, not buried, because a user seeing `CCV` for what they consider a `CV` word will otherwise read it as a bug. It is also the strongest argument for the later override or wrapper.

## Tests

- Unit tests on `Convert()` for each rule in isolation: base `C`/`V`, secondary articulation, prenasalisation, pre-aspiration, tie bar (both codepoints), a click with an accompaniment letter as one `C` and a tieless non-click digraph as `CC`, syllabic promotion for both a listed (`n̩`) and an unlisted syllabic consonant, vowel sequence, tone letter and tone diacritic contributing nothing, space preservation, unknown symbol, and **the same word in NFC and in NFD giving the same pattern** — that last one is the trap the mechanics section documents.
- An approval fixture `words.txt` for the CLI over real words, following [`adding-an-approval-fixture`](../../.claude/skills/adding-an-approval-fixture/SKILL.md). Zhire words from the existing [`zhire/tests/fixtures/phonetic2phonemic/inputs/`](../../zhire/tests/fixtures/phonetic2phonemic/inputs/) are attested and already in the repo, so no data needs inventing; anything constructed instead must carry a `_simulated` suffix.
- A **source-derived fixture** `bipa_graphemes`, whose approved side is written from BIPA's own tables rather than from the converter: one grapheme per line, expecting `C` for a row of `consonants.tsv` that is in the profile, `V` for `vowels.tsv`, and an empty pattern for `tones.tsv`. This is the ground-truth exception in [AGENTS.md's Testing Approach](../../AGENTS.md#testing-approach) — as `zhire`'s `orthography_statement_phonemes` does, do **not** promote a received file here; derive both sides from the source and say in `SPEC.md` how.
- A **PHOIBLE coverage test**, written as an assertion rather than an approval file: no segment of PHOIBLE's 2162 produces a `?`. Its tieless affricates are *expected* to give `CC`, which is the tie-bar decision showing up in a test rather than only in prose. **The test must not touch the network** — check the segment list in as a fixture input, taken from the `segment` column of `raw-data/FEATURES/phoible-segments-features.tsv` (176 KB in full, one column of it far less), and cite it in `SPEC.md`. If any segment does produce a `?`, that is a finding to report and discuss, not a number to adjust downwards until the test passes.

## Documentation

`cv-patterns/SPEC.md` (the transform rules, the source and its reconciliation, the tie-bar consequence), an entry in the root `SPEC.md` index, a README section naming `segments` as the dependency, and the BIPA CC-BY-4.0 credit on the README's Attributions line.

## Not in this release

A `CVN` (or richer sound-class) variant; per-language overrides for digraphs and glides; tone in the output; a FlexTools module. FLEx's Pronunciation object has a built-in **CV Pattern** field, which is the natural target when a module is added later, so no custom field will be needed.

## Changes after approval

Per [AGENTS.md's Plans section](../../AGENTS.md#plans), decisions made during implementation are appended here rather than edited into the body above; see `cv-patterns/SPEC.md` for the resulting spec.

- **25 listed syllabic consonants, not 22.** The plan's own Verified Mechanics section checked only for the two combining marks (U+0329, U+030D). BIPA's `consonants.tsv` marks syllabicity in its own `EXTRA` column (`syllabicity:syllabic`), and 3 of the 25 rows carrying it (`ḷ`, `ṇ`, `ṃ`, Indological dot-below transliterations) have neither mark. Checking `EXTRA` directly, rather than the mark alone, is what the generator does.
- **Two `normalize.tsv` wrinkles the plan's worked examples didn't anticipate**, both resolved during generation: `|` → `|` is a self-referential row (aliasing a prosodic/foot boundary not among BIPA's 6 `markers.tsv` rows) and is hand-assigned `NULL`; a `SOURCE` that is itself a bare diacritic template (`◌̱` → `◌̠`) is resolved against the diacritic it aliases rather than through the generic tokenise-and-reduce path used for the other ~40 rows.
- **6 combining contour tone diacritics (U+1DC4–U+1DC9) added beyond BIPA**, taken from this repository's own `chao-tone-letters/converters/diacritics2chao.py`. Found when the real-data `words.txt` fixture (Zhire phonetic data, which uses exactly these marks) turned every tone-marked syllable into `?` — without them, the plan's "so the two projects compose" claim only held for `diacritics2chao.py`'s output, not for tone-marked input going the other way.
- **2 further IPA diacritics (dental U+032A, linguolabial U+0347) added beyond BIPA.** Found by the PHOIBLE coverage test, confirmed missing from BIPA's own tables entirely. Discussed with the user rather than decided unilaterally, since — unlike the tone marks above — no other converter in this repository already depends on them; approved and added.
- **The PHOIBLE coverage test asserts a named allow-list of 23 known exceptions**, not zero unrecognised segments. Discussed with the user: the remaining gaps (a double-click `‼` notation BIPA spells differently, an idiosyncratic raised `ᴱ` and small-capital `ᴅ`, and 5 asterisk-prefixed non-phone markers) are PHOIBLE-specific or non-standard notation rather than a BIPA coverage gap, so the test names them explicitly rather than requiring a 100% pass that a future genuine regression could then hide inside.
- **PHOIBLE is pinned by commit** (`fd7894c10e6f894ac37f3e22765d15504b8eb25d` of `phoible/dev`), not a tag — PHOIBLE has no tagged releases.
- **`cv_profile.tsv`'s licence header is a `#`-comment block read via an explicit `commentPrefix` dialect override**, not `segments.Profile.from_file()` unmodified — that method sets no `commentPrefix` in its own default metadata, verified directly against `csvw`'s table-reading code, so `phonemes2cv.py` replicates `from_file()`'s logic with that one addition.
