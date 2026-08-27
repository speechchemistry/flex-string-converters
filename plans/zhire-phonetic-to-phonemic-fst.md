# Zhire phonetic-to-phonemic converter, built as a pynini FST

Status: proposed 2026-08-27, not yet implemented. The rule set below was extracted from the phonology sketch and prototyped against it (see [Prototype results](#prototype-results-measured-not-assumed)) — 47 of 47 orthography-chart rows run end to end, 44 matching the chart exactly and 3 exposing inconsistencies in the sketch itself. No converter, test or fixture file has been written yet.

## Why

`zhire/converters/phonemic2orthography.py` takes a **phonemic** transcription. Most of the Zhire `[zhi]` data actually collected in the field is **phonetic** — the phonology sketch's examples, Roger Blench and Timothy Terna's April 2025 elicitation, and the FLEx `lx_pt` field are all narrow transcriptions carrying detail that the phoneme inventory does not. Today that data cannot be spelled without a human normalising it first, and `zhire/SPEC.md` records this gap explicitly under [Not Yet Specified](../zhire/SPEC.md#not-yet-specified): "Phonetic input. `convert()` takes phonemic input, so the orthography statement's worked examples — which are phonetic — are not valid input as written."

This plan adds `zhire/converters/phonetic2phonemic.py`, a second converter in the same project folder, whose `convert()` maps a phonetic transcription to the phonemic transcription that `phonemic2orthography.convert()` already accepts. The two compose: phonetic → phonemic → orthography.

It is deliberately a *separate converter*, not an extension of `phonemic2orthography.py`, because the two answer different questions from different sources. `phonemic2orthography.py` implements the orthography statement's grapheme tables; this one implements the phonology sketch's allophony and notation. Keeping them apart means each has one source document to be reconciled against, which is what [AGENTS.md's External Specifications section](../AGENTS.md#external-specifications) asks for.

Following its sibling, the segmental mapping is implemented **exclusively as a finite-state transducer using [pynini](https://pypi.org/project/pynini/)**.

## Source of truth for the mapping

`zhi_phonology_sketch_extracted.md`, on the NRG Language Drive at `ZHI Zhire/Linguistics/phonology_sketch/automatic_rendering/`, authored by Tim Kempton — the pandoc-extracted Markdown of the Zhire phonology sketch (draft, version 1). Read the file directly rather than a pasted copy: the sibling plan records IPA being corrupted in transit through a chat transport.

Three of its parts carry the rules:

- **@tbl:consonants and @tbl:vowels** — the phoneme inventory, i.e. the converter's *output* alphabet.
- **The "Variants of coronal consonants" section and the `variant:` cells of the three phone relationship charts** — the only places the sketch asserts that two phones belong to one phoneme. There are exactly four such cells, plus two more assertions in prose. See [The variant assertions](#the-variant-assertions-all-six-of-them).
- **@tbl:consonant_graphemes, @tbl:vowel_graphemes and @tbl:modified_graphemes** — 47 rows, each pairing a phoneme with a *phonetic* example word and its orthographic spelling. These are the ground truth for the end-to-end fixture, and they are the same 47 rows the existing `orthography_statement_phonemes` fixture covers from the other document.

The three `phone_relationship_chart_*.md` files in the same folder are extracts of the sketch's own charts against a slightly older draft (they still write `ɲ` where the sketch now writes `nʲ`). Use the sketch, not those.

## Reconciling the sketch's phone inventory

Per [AGENTS.md's rule on accounting for every row of the source](../AGENTS.md#external-specifications), the reconciliation is over *symbols actually used in the sketch's phonetic transcriptions*, not over table rows — a phone that only ever appears inside a bracketed example still has to be mapped or explicitly excluded.

Mechanically extracting every `[...]` phonetic form in the sketch gives **183 unique forms**, built from:

| Class | Count | Disposition |
| ----- | ----- | ----------- |
| Base letters (Unicode `Ll`) | 35 | 29 are phonemes, 6 are not — broken out below |
| Modifier letters (`Lm`) | 7 | `ʷ ʲ ᵐ ⁿ ᵑ` transliterated to plain letters, `ː` kept, `ʼ` deleted |
| Tone marks (`Mn`) | 10 | all kept |
| Other combining marks (`Mn`) | 2 | `U+0303` nasal tilde kept, `U+0361` tie bar deleted |

The 35 base letters split as **29 that are phonemes** — the 8 vowels `a e i o u ɔ ə ɛ`, and the 21 distinct letters the 32 consonant phonemes of @tbl:consonants are spelled from (`p b t d k ɡ m n ŋ ɾ f v s z ʃ ʒ x ɣ h j w`) — and **6 that are not**, each of which needs a rule or an exclusion:

| Letter | Where it occurs | Disposition |
| ------ | --------------- | ----------- |
| `r` | 5 forms (`hǎr`, `hʲár`, `ta᷄r`, `xa᷆r`, `ʃa᷆r`) | free variant of `/ɾ/` — sketch-stated rule |
| `ɨ` | 2 forms (`ɡɨ̄ɾfò`, `ɣɨ᷅ɾ`) | maps to `/ə/` — *not* stated as a rule; see [Rules the sketch demonstrates but does not state](#rules-the-sketch-demonstrates-but-does-not-state) |
| `ɲ` | prose only, in the nasal-contrast section | reanalysed as `[nʲ]`, so maps to `/nj/` — sketch-stated |
| `ɕ` | only ever in `[ɕʷ]` | kept as the unit `/ɕw/`, which `phonemic2orthography` already accepts |
| `ʑ` | only ever in `[ʑʷ]` | kept as the unit `/ʑw/`, likewise |
| `l` | 1 form, `[lāwūɾ]` 'sweet potato' | not a Zhire phoneme; the sketch names it a Hausa loan. See [Open questions](#open-questions) |

35 = 29 + 6, and every one of the 6 has a bucket. The counts above are what a first implementation step should re-derive from the file and assert, so that a revised sketch introducing a 36th letter fails a test rather than being silently ignored.

## The variant assertions, all six of them

The sketch defines "variant" as deliberately agnostic — "whether the sounds are in free variation or if one sound is an allophone of the other". For this converter the distinction does not matter: either way the two phones collapse to one phoneme. What matters is that the set is closed and countable, so that a later draft adding a seventh is noticed.

Four come from `variant:` cells in the phone relationship charts, two from prose:

| # | Assertion | Where | Rule |
| - | --------- | ----- | ---- |
| 1 | `/ɾ/` is realised `[ɾ]` or `[r]` | `@ex:free_variation_ɾ_r` | `r` → `r` (see [Open questions](#open-questions) on the output symbol) |
| 2 | `/ts/` is realised `[ts]` or `[tsʼ]` | `@ex:free_variation_ts_ts` | delete `ʼ` (`U+02BC`) |
| 3 | `[ⁿdz]` and `[ⁿz]` are variants of one phoneme | `@ex:variant_ⁿdz_ⁿz` | `ⁿz` → `ndz` |
| 4 | `[ⁿdʒ]` is a rare dialectal variant of `/ⁿdz/` | prose, Orthography section | `ⁿdʒ` → `ndz` |
| 5 | `[ɲ]` was reanalysed as `[nʲ]` | prose, "Contrast between nasal consonants" | `ɲ` → `nj` |
| 6 | `/ʒ/` is realised `[ʒ]` or `[j]` | `@ex:free_variation_ʒ_j` | **not implementable — excluded, see below** |

**Assertion 6 is the one to be careful about.** The same chart cell reads "`@ex:ʒ_j` with variant: `@ex:free_variation_ʒ_j`" — the sketch asserts that `[ʒ]` and `[j]` both *contrast* (`[ja᷆ː]` 'mother' vs `[ʒa᷆ː]` 'monitor lizard') and *vary freely* (`[jɛ᷆ŋ]` 'sheep' vs `[ʒɛ᷆ŋ]` 'ewe'). A transducer cannot have it both ways: mapping `[j]` to `/ʒ/` would merge a contrast the sketch elsewhere establishes. So `[j]` maps to `/j/` and `[ʒ]` to `/ʒ/`, the free variation is not modelled, and this is written down in `zhire/SPEC.md` as a known limitation rather than left as an unexplained gap. This is a question for the linguist, not for the converter — flagged in [Open questions](#open-questions).

## Rules the sketch demonstrates but does not state

Two rules are not asserted anywhere in the sketch's prose, but its own orthography charts depend on them. Per [AGENTS.md](../AGENTS.md#external-specifications) — "Never assert that a row 'falls out' of composing other entries — test it" — both were checked, not assumed.

- **`[ɨ]` → `/ə/`.** @tbl:consonant_graphemes gives `/ɣ/` the example `[ɣɨ᷅ɾ]` spelled `ghər`. The `ə` in that spelling can only come from the `[ɨ]`. `zhire/SPEC.md` currently lists this under Not Yet Specified as "observed... **not implemented or confirmed**"; the sketch's own chart is the confirmation. Verified: the rule makes that row round-trip.
- **Prenasalisation is written with modifier letters, and the phonemic form spells it out.** `[ᵐb] [ⁿd] [ᵑɡ] [ᵑᵐɡb] [ⁿdz]` become `/mb/ /nd/ /ŋɡ/ /ŋmɡb/ /ndz/`. Verified: all five then spell as `mb`, `nd`, `ngg`, `ngb`, `ndz`, matching the chart.

By contrast, the third rule `zhire/SPEC.md` lists as observed-but-unconfirmed — **`[ɛ]` for `/e/` in a closed syllable** — is *contradicted* by the sketch and is **not** implemented. The same table writes closed-syllable `[ɛ]` as `ɛ` in `[mɛ᷆k]` → `mɛk` and `[tʲɛ᷅ɾ]` → `tyɛr`, but as `e` in `[ⁿdɛ̀n]` → `nden`. Two rows against one; the odd row out is treated as a source error, not a rule. See [Prototype results](#prototype-results-measured-not-assumed).

## The mapping

Everything below is a flat symbol-level mapping — no context-dependent rewrite rules are needed, which is why a token lexicon plus maximal munch (the architecture `phonemic2orthography.py` already uses) is sufficient.

### Modifier letters transliterated to plain letters

`phonemic2orthography.convert()` accepts plain letter sequences and explicitly *rejects* the modifier-letter notation, so this converter must emit plain sequences. This is not a free choice; it is what makes the two converters compose.

| Phonetic | Phonemic | Note |
| -------- | -------- | ---- |
| `ʷ` (`U+02B7`) | `w` | labialisation |
| `ʲ` (`U+02B2`) | `j` | palatalisation |
| `ᵐ` (`U+1D50`) | `m` | prenasalisation |
| `ⁿ` (`U+207F`) | `n` | prenasalisation |
| `ᵑ` (`U+1D51`) | `ŋ` | prenasalisation |

### Segments rewritten

| Phonetic | Phonemic | Source |
| -------- | -------- | ------ |
| `r` | `r` | variant assertion 1 |
| `ɾ` | `r` | the phoneme itself, in `phonemic2orthography`'s notation |
| `ɨ` | `ə` | demonstrated by @tbl:consonant_graphemes |
| `ɲ` | `nj` | variant assertion 5 |
| `ⁿz` | `ndz` | variant assertion 3 |
| `ⁿdʒ` | `ndz` | variant assertion 4 |

### Marks deleted

| Mark | Why |
| ---- | --- |
| `ʼ` (`U+02BC`) modifier letter apostrophe | ejective release; variant assertion 2 |
| `͡` (`U+0361`) combining double inverted breve | tie bar on `[k͡p]`; notation only, and the sketch writes the same phoneme `[kp]` untied elsewhere |

### Marks kept

- **All 10 tone marks.** The phonemic form stays tonal: the sketch treats tone as contrastive, and the project's real phonemic data (`zhire/tests/fixtures/phonemic2orthography/inputs/words.txt`) carries tone marks throughout. Stripping tone is `phonemic2orthography.py`'s job, at the end of the chain, and doing it twice would throw information away a step early.
- **`U+0303` combining tilde** — nasalisation is contrastive (`@ex:a_a_aŋ`).
- **`ː` (`U+02D0`)** — vowel length is contrastive.
- **Space**, as a word divider, matching the sibling converter.

### One source typo normalised

`[dzu᷈:ŋ]` 'permitted to go' writes the length mark as an ASCII colon `U+003A` rather than `U+02D0`. Map `:` to `ː` so the sketch's own data converts, and note it in `zhire/SPEC.md`. Worth reporting upstream too.

## Prototype results (measured, not assumed)

The rule set above was run over the sketch as a throwaway prototype composed with the real `phonemic2orthography.convert()`. Naming the artifact explicitly, per [AGENTS.md](../AGENTS.md#external-specifications):

- **All 47 rows of @tbl:consonant_graphemes, @tbl:vowel_graphemes and @tbl:modified_graphemes**, taking each row's phonetic example as input and its orthography column as expected output: **44 match, 3 mismatch, 0 error.**
- **All 183 unique bracketed phonetic forms in the sketch**, checked only for "produces a phonemic form that `phonemic2orthography` can spell without raising": **183 of 183.** This is a coverage check, not a correctness check — there is no orthographic ground truth for the other 136 forms.

The 3 mismatches all look like inconsistencies **in the sketch**, each contradicting another row of the same table. None of them is a converter bug, and none should be "fixed" by adding a rule:

| Row | Converter gives | Chart says | Reading |
| --- | --------------- | ---------- | ------- |
| `/ⁿd/`, `[ⁿdɛ̀n]` 'door' | `ndɛn` | `nden` | The chart's own vowel table maps `/ɛ/` to `ɛ`, and `[mɛ᷆k]` → `mɛk`, `[tʲɛ᷅ɾ]` → `tyɛr` do so. `nden` looks like a leftover. |
| `/ᵑɡ/`, `[ᵑɡēj]` 'branch' | `nggey` | `nggei` | The chart maps `/j/` to `y`, so a `[j]` offglide should give `y`. Either the offglide is really `/i/` (a diphthong `[ei]`), or the orthography has an unstated offglide convention. This is the same "`[j]` offglide" question `zhire/SPEC.md` already lists as unconfirmed. |
| `/ⁿdz/`, `[ⁿzo᷇ɾ]` 'chin' | `ndzor` | `nzor` | The chart's own phoneme row says `/ⁿdz/` is spelled `ndz`, and the surrounding prose records the grapheme being changed from `nj` to `ndz`. `nzor` looks like that change not being carried into the example column. |

**These three rows must not go into the approved fixture as written.** Resolve them with the linguist first — see [Open questions](#open-questions) — and record the resolution in `zhire/SPEC.md` next to the fixture, so the fixture can be re-derived when the sketch is revised.

## What `convert()` does

1. Normalise the input to NFD, so a base letter and its combining marks are separate code points.
2. Replace ASCII `:` with `ː`.
3. Feed the result through the pynini token lexicon, which tokenises by maximal munch and rewrites each token per [The mapping](#the-mapping). Multi-character tokens (`ⁿz`, `ⁿdʒ`, `ɕʷ`, `ʑʷ`) must win over their single-character parts, which maximal munch gives for free — the sibling converter's [correction 2](old/zhire-phonemic-to-orthography-fst.md#corrections-found-after-implementation) records where that behaviour actually comes from, and the same unweighted construction applies here.
4. Raise `ValueError` naming the input on anything the lexicon does not cover, matching `phonemic2orthography.py`'s contract rather than passing unknown text through.
5. Normalise the result to NFC.

Tone marks and the nasal tilde pass through the FST unchanged rather than being handled outside it. This differs from `phonemic2orthography.py`, which strips combining marks in a Python pre-pass — but that converter *deletes* marks by a general Unicode-category rule, whereas this one *preserves* them, and preserving is exactly what an identity arc in the lexicon does. Worth confirming during implementation that a combining mark round-trips cleanly through `pynini` in `utf8` token mode; if it does not, fall back to a pre-pass that splits marks off, converts the base, and reassembles.

## Testing

Following [AGENTS.md's Testing Approach](../AGENTS.md#testing-approach), and TDD throughout — fixture and failing test first, implementation second.

**Inline unit tests** (`zhire/tests/test_phonetic2phonemic.py`), one per general rule with the clearest single example, not duplicating what the corpus already covers: modifier-letter transliteration, each of the five implemented variant rules, `[ɨ]` → `/ə/`, tie-bar deletion, tone/nasalisation/length preservation, the ASCII-colon normalisation, and the unmapped-input `ValueError`.

**Approval fixtures** (`zhire/tests/fixtures/phonetic2phonemic/`), following the [`adding-an-approval-fixture`](../.claude/skills/adding-an-approval-fixture/SKILL.md) skill except where noted:

- `phonology_sketch_examples` — **specification-derived, so the promote loop is wrong for it**, exactly as for the existing `orthography_statement_phonemes` fixture. Both sides come from the sketch: input is the phonetic example column of the three grapheme charts, and the approved side is hand-written from the sketch's phoneme column. Write it by hand; never promote a received file into it. Record its derivation in `zhire/SPEC.md`.
- `phonology_sketch_words` — the sketch's other bracketed example forms, as a breadth net. There is no phonemic ground truth for these, so this one *is* an ordinary promote-loop fixture, and its approved file must be read before it is first promoted, not accepted on trust.
- Real held-out phonetic data, if the linguist has phonetic/phonemic pairs not used to derive any rule above. This is the net that source-derived fixtures are structurally blind to — the `/l/` gap that the existing SPEC.md records was found exactly this way, and the sketch has the same hole (it names `[lāwūɾ]` as the one `[l]` word and excludes `/l/` from the inventory). See [Open questions](#open-questions).

**An end-to-end composition test.** The most valuable check available, since the sketch supplies both ends: run each chart row's phonetic example through `phonetic2phonemic.convert()` then `phonemic2orthography.convert()` and compare against the sketch's orthography column. This is what produced the 44/47 above. Put it in `zhire/tests/`, and keep the 3 unresolved rows out of it until the linguist has ruled on them, with a comment naming them rather than a silent omission.

## File layout

- `zhire/converters/phonetic2phonemic.py` — the converter: header block per [AGENTS.md's Converter Conventions](../AGENTS.md#converter-conventions), `convert()`, and a CLI under `if __name__ == '__main__':` matching `phonemic2orthography.py`'s shape (arguments converted one per line, or stdin as a filter; UTF-8 forced on both streams).
- `zhire/tests/test_phonetic2phonemic.py` — inline unit tests.
- `zhire/tests/test_phonetic2phonemic_cli.py` — the approval test driving the fixtures through the CLI.
- `zhire/tests/test_phonetic2orthography_chain.py` — the end-to-end composition test.
- `zhire/tests/fixtures/phonetic2phonemic/{inputs,approved}/` — the fixtures above.

No new dependency: `pynini` is already required by this project. No FlexTools module, for the same reason as its sibling — `pynini` does not support the Python .NET/IronPython runtime FlexTools modules run under.

## Documentation to update once this is implemented

- `zhire/SPEC.md` — a new "Phonetic Transcription To Phonemic Transcription" section; name the phonology sketch as the source document and which of its tables the converter implements; record the excluded `[ʒ]`~`[j]` variation, the three chart inconsistencies, and the ASCII-colon normalisation. Then revise the [Not Yet Specified](../zhire/SPEC.md#not-yet-specified) entry on phonetic input, which this converter partly closes: `[ɨ]` for `/ə/` is now implemented and confirmed, `[ɛ]` for `/e/` in closed syllables is confirmed *not* to be a rule, and the `[j]` offglide is still open.
- `README.md` — a section for the new converter, and the composition with `phonemic2orthography.py`.
- Move this plan to `plans/old/` in the same change that finishes the implementation, fixing its relative links from one level up to two, per [AGENTS.md's Plans section](../AGENTS.md#plans).

## Open questions

Answers change the implementation, so worth settling before writing code — but none of them blocks starting, since each has a stated default.

1. **`/ɾ/` or `/r/` as the output symbol?** The sketch and the orthography statement both name the phoneme `/ɾ/`; the project's real phonemic data and `phonemic2orthography.py`'s own table use `r`, with `ɾ` accepted as an alternate notation. Both spell correctly. **Default: emit `r`**, for consistency with the existing phonemic corpus.
2. **Should `[j]` map to `/ʒ/` anywhere?** The sketch asserts both contrast and free variation between them. **Default: no** — `[j]` → `/j/`, and the free variation goes unmodelled and documented.
3. **The three chart inconsistencies** in [Prototype results](#prototype-results-measured-not-assumed) — `nden`, `nggei`, `nzor`. Each contradicts another row of the same table, so my reading is that the sketch is wrong in all three and should be corrected upstream. **Default: treat as source errors**, hold them out of the fixture, and note them.
4. **`[l]`.** The sketch excludes `/l/` from the inventory and names `[lāwūɾ]` a Hausa loan, but `phonemic2orthography.py` implements `/l/` — added precisely because held-out data showed it was needed. **Default: pass `[l]` through as `/l/`**, so the two converters agree and loanwords survive the chain.
5. **Is there held-out phonetic data** with a known phonemic or orthographic form, not used to derive any rule above? Source-derived fixtures cannot catch a gap in the source, and the sketch's `/l/` treatment shows this source has such gaps.
6. **Which phonetic notation is the real input?** The rule set is a superset: it handles the sketch's narrow notation (`ʷ ʲ ᵐ ⁿ ᵑ ɨ tsʼ k͡p`) and the FLEx `lx_pt` field's broader notation (already plain sequences, differing mainly by `ɲ` and `r`/`ɾ`) alike, so no change is needed either way — but knowing which one matters in practice would set where the fixtures should come from.
