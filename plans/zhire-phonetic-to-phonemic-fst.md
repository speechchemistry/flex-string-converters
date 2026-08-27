# Zhire phonetic-to-phonemic converter, built as a pynini FST

Status: proposed 2026-08-27, revised twice 2026-08-27, not yet implemented. The rule set was extracted from the phonology sketch and prototyped against it (see [Prototype results](#prototype-results-measured-not-assumed)) — 47 of 47 orthography-chart rows run end to end, 44 matching the chart exactly and 3 exposing inconsistencies in the sketch itself. It was then checked against 246 real etic/emic word pairs the user supplied from FLEx (`phonetic2phonemic_public_test.csv`) — see [Validation against real held-out data](#validation-against-real-held-out-data) — which confirmed most of the rule set and supplied one rule the sketch never states (aspiration deletion). All six original open questions plus one raised by the real data are resolved — see [Decisions](#decisions-resolved-2026-08-27); only the fixture's file name and location (5a) is still a default — including the user's explicit call (2026-08-27) to implement `[ɲ]` → `/nj/` as the sketch states it despite 3 real words disagreeing, and to keep all known-anomalous rows in the held-out fixture rather than hold them out or add rules around them. No converter, test or fixture file has been written yet.

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
| `ɲ` | prose only, in the nasal-contrast section | reanalysed as `[nʲ]`, so maps to `/nj/` — sketch-stated rule, implemented despite real data partly contradicting it; see [Validation against real held-out data](#validation-against-real-held-out-data) |
| `ɕ` | only ever in `[ɕʷ]` | kept as the unit `/ɕw/`, which `phonemic2orthography` already accepts |
| `ʑ` | only ever in `[ʑʷ]` | kept as the unit `/ʑw/`, likewise |
| `l` | 1 form, `[lāwūɾ]` 'sweet potato' | not a Zhire phoneme; the sketch names it a Hausa loan. Passed through as `/l/` — see [Decisions](#decisions-resolved-2026-08-27) item 4 |

35 = 29 + 6, and every one of the 6 has a bucket. The counts above are what a first implementation step should re-derive from the file and assert, so that a revised sketch introducing a 36th letter fails a test rather than being silently ignored.

## The variant assertions, all six of them

The sketch defines "variant" as deliberately agnostic — "whether the sounds are in free variation or if one sound is an allophone of the other". For this converter the distinction does not matter: either way the two phones collapse to one phoneme. What matters is that the set is closed and countable, so that a later draft adding a seventh is noticed.

Four come from `variant:` cells in the phone relationship charts, two from prose:

| # | Assertion | Where | Rule |
| - | --------- | ----- | ---- |
| 1 | `/ɾ/` is realised `[ɾ]` or `[r]` | `@ex:free_variation_ɾ_r` | `r` → `r` (see [Decisions](#decisions-resolved-2026-08-27) item 1 on the output symbol) |
| 2 | `/ts/` is realised `[ts]` or `[tsʼ]` | `@ex:free_variation_ts_ts` | delete `ʼ` (`U+02BC`) |
| 3 | `[ⁿdz]` and `[ⁿz]` are variants of one phoneme | `@ex:variant_ⁿdz_ⁿz` | `ⁿz` → `ndz` |
| 4 | `[ⁿdʒ]` is a rare dialectal variant of `/ⁿdz/` | prose, Orthography section | `ⁿdʒ` → `ndz` |
| 5 | `[ɲ]` was reanalysed as `[nʲ]` | prose, "Contrast between nasal consonants" | `ɲ` → `nj` |
| 6 | `/ʒ/` is realised `[ʒ]` or `[j]` | `@ex:free_variation_ʒ_j` | **not implementable — excluded, see below** |

**Assertion 6 is the one to be careful about.** The same chart cell reads "`@ex:ʒ_j` with variant: `@ex:free_variation_ʒ_j`" — the sketch asserts that `[ʒ]` and `[j]` both *contrast* (`[ja᷆ː]` 'mother' vs `[ʒa᷆ː]` 'monitor lizard') and *vary freely* (`[jɛ᷆ŋ]` 'sheep' vs `[ʒɛ᷆ŋ]` 'ewe'). A transducer cannot have it both ways: mapping `[j]` to `/ʒ/` would merge a contrast the sketch elsewhere establishes. So `[j]` maps to `/j/` and `[ʒ]` to `/ʒ/`, the free variation is not modelled, and this is written down in `zhire/SPEC.md` as a known limitation rather than left as an unexplained gap. Confirmed as the right call: user-confirmed 2026-08-27.

**Assertion 5 is implemented as the sketch states it, even though real data partly disagrees.** The user's 246-row FLEx export (see [Validation against real held-out data](#validation-against-real-held-out-data)) contains three words phonemically transcribed with `ɲ` (`ɲápsə́` 'hesitation', `ɲúnə̀` 'bitterness', `ɲo᷆k` 'to weave') alongside eleven transcribed with `nj` (`njōɾɔ᷆` 'to caress', `njɛ᷄ŋ` 'stomach', and nine others) — both **in the phonemic column**, never conflated. Per [AGENTS.md](../AGENTS.md#external-specifications), real data would normally be the tiebreaker over the source document — but the user's call (2026-08-27) is to implement the sketch's stated rule anyway: `ɲ` → `nj`, alongside the other four implemented assertions (1–4). The three `ɲ` words will then fail the held-out fixture until their FLEx entries are corrected — expected and left as-is rather than special-cased, per the user's instruction not to build rules around rare cases. See [Validation against real held-out data](#validation-against-real-held-out-data) for the resulting fixture-failure list. Checked directly against the real `phonemic2orthography.convert()`: it already accepts `nj` output fine (`n`+`j` concatenates to `ny`, e.g. `njōrɔ᷆` → `nyorɔ`), so mapping `ɲ` to `/nj/` here does not depend on any change to the sibling converter.

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
| `ɲ` | `nj` | variant assertion 5 — known to conflict with some real data; see [Validation against real held-out data](#validation-against-real-held-out-data) |
| `ⁿz` | `ndz` | variant assertion 3 |
| `ⁿdʒ` | `ndz` | variant assertion 4 |

### Marks deleted

| Mark | Why |
| ---- | --- |
| `ʼ` (`U+02BC`) modifier letter apostrophe | ejective release; variant assertion 2 |
| `͡` (`U+0361`) combining double inverted breve | tie bar on `[k͡p]`; notation only, and the sketch writes the same phoneme `[kp]` untied elsewhere |
| `ʰ` (`U+02B0`) modifier letter small h | aspiration release — **not in the sketch at all**; found in the real held-out data (`sīsʰi᷆p` → `sīsi᷆p` 'sweat'), the one row it occurs in. See [Validation against real held-out data](#validation-against-real-held-out-data). |

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

**These three rows must not go into the approved fixture as written.** User-confirmed 2026-08-27: all three are source errors in the sketch, not gaps in the rule set. **One piece of new counter-evidence for the `nzor` ('chin') row, surfaced only after that confirmation, worth a second look — see the note at the end of [Validation against real held-out data](#validation-against-real-held-out-data) below.**

## Validation against real held-out data

The user supplied `phonetic2phonemic_public_test.csv`, a 246-row FLEx export with an etic (`zhi-fonipa-x-etic`) and an emic (`zhi-fonipa-x-emic`) column for the same 246 words — real elicited data, independent of the phonology sketch, and exactly the kind of held-out net [AGENTS.md](../AGENTS.md#external-specifications) asks for: "source-derived fixtures and real or held-out data are complementary nets that fail in opposite directions." Naming the artifact: all 246 rows have both columns filled; none were dropped as unusable.

Running the etic column through the rule set in [The mapping](#the-mapping) and comparing to the emic column: **241 of 246 exact matches.** Reconciling all 246 rather than quoting the headline number, since the buckets are what show which rules are actually load-bearing:

| Bucket | Rows | |
| ------ | ---- | - |
| Two columns already identical, and still match | 178 | no rule needed |
| Differ, explained by `ɾ → r` alone | 58 | the single most load-bearing rule in the whole set |
| Differ, additionally need `ɨ → ə` | 4 | |
| Differ, additionally need `ʰ` deleted | 1 | the rule the sketch never states — see below |
| **Match subtotal** | **241** | |
| Identical columns *broken* by `ɲ → nj` | 3 | the rule implemented against real data, per [Decisions](#decisions-resolved-2026-08-27) item 7 |
| Differ, unexplained by any rule — data anomalies | 2 | |
| **Mismatch subtotal** | **5** | |
| **Total** | **246** | |

Worth being precise about the `ɲ → nj` bucket, because the headline framing hides it: those 3 rows have *identical* etic and emic columns, so they would match trivially under an identity rule. It is applying assertion 5 that breaks them. So the rule set's 5 failures are not 5 rows it fails to explain — they are 2 genuine data anomalies plus 3 rows it actively changes against the evidence, by explicit decision.

None of the sketch's modifier letters (`ʷ ʲ ᵐ ⁿ ᵑ`) appear anywhere in the etic column — confirming the user's report that this notation isn't used in practice — and neither does the ejective mark or the tie bar. Those parts of [The mapping](#the-mapping) are therefore entirely untested by this corpus, kept for compatibility with the sketch's own notation rather than dropped. The plain `r` identity rule, by contrast, does get exercised: 13 rows carry a literal `r` in the etic column.

**New rule, not in the sketch: aspiration is deleted.** `sīsʰi᷆p` → `sīsi᷆p` 'sweat' is the one row with `ʰ` (`U+02B0`, modifier letter small h) anywhere in the etic column. Added to [Marks deleted](#marks-deleted) alongside the ejective mark and the tie bar, both of which this rule set already drops for the same reason (release/notation detail the phonemic level doesn't carry).

**`[ɲ]` does not merge with `/nj/` in 3 of the 14 `nj`/`ɲ` words, and the rule is implemented anyway.** Covered under [The variant assertions](#the-variant-assertions-all-six-of-them) — the user's decision (2026-08-27) is to implement assertion 5 as the sketch states it and let the three conflicting words fail the held-out fixture for now, to be fixed in FLEx once seen, rather than special-case the rule around them.

With that decision, the rule set gives **5 mismatches out of 246**, all expected and all left in the fixture rather than held out:

| Etic | Rule-set output | Real emic | Gloss | Reading |
| ---- | ---------------- | --------- | ----- | ------- |
| `ɲápsə́` | `njápsə́` | `ɲápsə́` | hesitation | assertion 5 applied as the sketch states it; this word's FLEx entry is expected to need correcting |
| `ɲúnə̀` | `njúnə̀` | `ɲúnə̀` | bitterness | same |
| `ɲo᷆k` | `njo᷆k` | `ɲo᷆k` | to weave | same |
| `kɨ́kjōɾākàp` | `kə́kjōrākàp` | `kjukjōrɔ̄ kàp` | river molluscs; shells | not a phone-level correspondence — etic and emic look like different transcriptions of the word, not two levels of the same one. Data anomaly, not a rule; left to fail and be corrected in FLEx. |
| `kɨ́ɾ wèɡbī` | `kə́r wèɡbī` | `kə́r wə̀ɡbī` | water yam | `wèɡbī` (plain `e`) versus the corpus's own `wɨ̀ɡbī` → `wə̀ɡbī` 'dog' (same string, etic `ɨ`, gloss-unrelated but phonologically identical). Reads as an etic transcription slip — should have been `ɨ` — not a new rule; left to fail and be corrected in FLEx. |

All five stay in `real_flex_export` (see [Testing](#testing)) as ordinary approval-test mismatches: each run produces a `received/real_flex_export.received.txt` to diff against `approved/real_flex_export.approved.txt`, exactly the review loop the user asked for — no rule is built around any of them.

**One more anomaly, resolved differently from the 5 mismatches above.** `ɡo᷅r**` 'payment' carries a trailing `**` on *both* the etic and emic columns — FLEx annotation noise, not phonemic content, and not something either converter's token lexicon covers (`**` would make `convert()` raise `ValueError`, same as it does on `phonemic2orthography.convert()` today). User's call (2026-08-27): strip the `**` from both columns when building the fixture, rather than leave it to fail or isolate it — the row becomes an ordinary `ɡo᷅r` → `ɡo᷅r` pair, one of the 181 rows in the corpus whose two columns are already identical. This also sidesteps a mechanical wrinkle worth recording even though it no longer bites: the CLI approval test feeds a whole fixture file to the converter through one `subprocess.run(..., check=True)` call, so a raising row would have crashed that *entire file's* test before producing any output — hiding the diff for the other 245 words, not just skipping the bad one. Stripping the `**` avoids ever hitting that, so it's not something the fixture layout needs to work around.

**Counter-evidence on the `nzor` ('chin') row, found after the source-errors confirmation above.** The real corpus contains exactly this word: `nzo᷇ɾ` → `nzo᷇r` 'chin', in its *emic* (phonemic) column — no `d`, matching the sketch chart's disputed `nzor`, not the `ndzor` the stated `/ⁿdz/` → `ndz` grapheme rule would predict. Unlike `ɲ`, there's no second, contradicting form of this word in the corpus to weigh against it. Two readings are both live: either the chart's `nzor` example is genuinely a leftover from before the `nj`→`ndz` grapheme change (as reasoned in [Prototype results](#prototype-results-measured-not-assumed)), and this FLEx entry's emic field simply hasn't been updated to match either — or 'chin' is not actually an instance of the `/ⁿdz/` phoneme at all, and the sketch's own classification of it under that phoneme (in `@ex:variant_ⁿdz_ⁿz`, alongside `[ʃī ⁿdzòɾ]` 'beard' as the `[ⁿdz]` counterpart) is the error, with the two words never having been the same phoneme in the first place. Both readings still say the same thing for this converter: don't apply the `ⁿz → ndz` rule to plain, non-superscript `nz` — the real corpus never spells it as pre-nasalised with the sketch's modifier-letter notation, so the rule as scoped (superscript `ⁿ` only) already does the right thing here. Flagging this because it complicates "just a source error" enough that the linguist may want to know before the fixture is finalised, not because it changes the rule set as written.

## What `convert()` does

1. Normalise the input to NFD, so a base letter and its combining marks are separate code points.
2. Replace ASCII `:` with `ː`.
3. Feed the result through the pynini token lexicon, which tokenises by maximal munch and rewrites each token per [The mapping](#the-mapping). Exactly two tokens are genuinely multi-character — `ⁿz` → `ndz` and `ⁿdʒ` → `ndz` — and both must win over their single-character parts, which maximal munch gives for free; the sibling converter's [correction 2](old/zhire-phonemic-to-orthography-fst.md#corrections-found-after-implementation) records where that behaviour actually comes from, and the same unweighted construction applies here. **Checked rather than assumed, per [AGENTS.md](../AGENTS.md#external-specifications) on not claiming a row "falls out":** every other multi-letter sequence really does fall out of the per-character rules — `ɕʷ` → `ɕw`, `ʑʷ` → `ʑw`, `hʷ` → `hw`, `ⁿdz` → `ndz`, `ᵑᵐɡb` → `ŋmɡb` — so none of them needs a token of its own. Worth stating explicitly because `ⁿdz` and `ⁿdʒ` differ by a single letter and only the second one needs an entry.
4. Raise `ValueError` naming the input on anything the lexicon does not cover, matching `phonemic2orthography.py`'s contract rather than passing unknown text through.
5. Normalise the result to NFC.

Tone marks and the nasal tilde pass through the FST unchanged rather than being handled outside it. This differs from `phonemic2orthography.py`, which strips combining marks in a Python pre-pass — but that converter *deletes* marks by a general Unicode-category rule, whereas this one *preserves* them, and preserving is exactly what an identity arc in the lexicon does. Checked against `pynini` directly rather than left as an implementation risk: with combining marks given identity arcs in a `utf8`-token lexicon, `kār` round-trips byte-identical and `k͡pár` comes out as `kpár` — tie bar deleted, tone mark intact. So no pre-pass is needed, and marks can be handled inside the FST as described.

## Testing

Following [AGENTS.md's Testing Approach](../AGENTS.md#testing-approach), and TDD throughout — fixture and failing test first, implementation second.

**Inline unit tests** (`zhire/tests/test_phonetic2phonemic.py`), one per general rule with the clearest single example, not duplicating what the corpus already covers: modifier-letter transliteration, each of the five implemented variant rules (assertions 1–5, `ɲ` → `nj` included — see [Decisions](#decisions-resolved-2026-08-27)), `[ɨ]` → `/ə/`, tie-bar and aspiration deletion, tone/nasalisation/length preservation, the ASCII-colon normalisation, and the unmapped-input `ValueError`.

**Approval fixtures** (`zhire/tests/fixtures/phonetic2phonemic/`), following the [`adding-an-approval-fixture`](../.claude/skills/adding-an-approval-fixture/SKILL.md) skill except where noted:

- `phonology_sketch_examples` — **specification-derived, so the promote loop is wrong for it**, exactly as for the existing `orthography_statement_phonemes` fixture. Both sides come from the sketch: input is the phonetic example column of the three grapheme charts, and the approved side is hand-written from the sketch's phoneme column. Write it by hand; never promote a received file into it. Record its derivation in `zhire/SPEC.md`.
- `phonology_sketch_words` — the sketch's other bracketed example forms, as a breadth net. There is no phonemic ground truth for these, so this one *is* an ordinary promote-loop fixture, and its approved file must be read before it is first promoted, not accepted on trust.
- `real_flex_export` — the real held-out net: all 246 rows of `phonetic2phonemic_public_test.csv`, columns 3–4 only, with one cleanup: the `**` stripped from both columns of the `ɡo᷅r**` 'payment' row (per [5b](#open-questions)), so it converts as an ordinary identical pair rather than raising. The 5 remaining known mismatches (the 3 `ɲ` words plus the 2 data anomalies) are **left in this fixture on purpose** — they fail loudly with a normal received/approved diff for the user to review and fix in FLEx, rather than being held out or worked around with extra rules. **Specification-derived in the same sense as `phonology_sketch_examples`**: the emic column is independently elicited ground truth, not the converter's own output, so the promote loop is wrong for it too — write both sides directly from the CSV, never promote a received file into it. This is what caught the aspiration-deletion rule and the `ɲ`/`nj` split; see [Validation against real held-out data](#validation-against-real-held-out-data).

**An end-to-end composition test.** The most valuable check available, since the sketch supplies both ends: run each chart row's phonetic example through `phonetic2phonemic.convert()` then `phonemic2orthography.convert()` and compare against the sketch's orthography column. This is what produced the 44/47 above. Put it in `zhire/tests/`, and keep the 3 source-error sketch rows (`nden`, `nggei`, `nzor`) out of it until they are corrected upstream, with a comment naming them rather than a silent omission — these are the sketch's own chart rows, a different set from the `real_flex_export` mismatches above, which stay in their fixture and are expected to fail.

## File layout

- `zhire/converters/phonetic2phonemic.py` — the converter: header block per [AGENTS.md's Converter Conventions](../AGENTS.md#converter-conventions), `convert()`, and a CLI under `if __name__ == '__main__':` matching `phonemic2orthography.py`'s shape (arguments converted one per line, or stdin as a filter; UTF-8 forced on both streams).
- `zhire/tests/test_phonetic2phonemic.py` — inline unit tests.
- `zhire/tests/test_phonetic2phonemic_cli.py` — the approval test driving the fixtures through the CLI.
- `zhire/tests/test_phonetic2orthography_chain.py` — the end-to-end composition test.
- `zhire/tests/fixtures/phonetic2phonemic/{inputs,approved}/` — the fixtures above, including `real_flex_export.txt` derived from `phonetic2phonemic_public_test.csv`.

No new dependency: `pynini` is already required by this project. No FlexTools module, for the same reason as its sibling — `pynini` does not support the Python .NET/IronPython runtime FlexTools modules run under.

## Documentation to update once this is implemented

- `zhire/SPEC.md` — a new "Phonetic Transcription To Phonemic Transcription" section; name both source documents (the phonology sketch, and the real FLEx export used for the held-out fixture) and which of the sketch's tables the converter implements; record the excluded `[ʒ]`~`[j]` variation, the three chart inconsistencies, the `[ɲ]`→`/nj/` rule and that it's expected to fail on 3 words of `real_flex_export` until their FLEx entries are corrected, the aspiration-deletion rule the sketch doesn't state at all, the `ɡo᷅r**` annotation-noise row and that its `**` is stripped from both columns before the fixture is built, and the ASCII-colon normalisation. Note the narrower `/ɲ/` gap in `phonemic2orthography.convert()` — real emic data containing literal `ɲ` fails there if fed in directly, bypassing this converter — under that converter's own Not Yet Specified entry, as a follow-up rather than fixing it here. Then revise this converter's own Not Yet Specified entry on phonetic input, which this converter partly closes: `[ɨ]` for `/ə/` is now implemented and confirmed, `[ɛ]` for `/e/` in closed syllables is confirmed *not* to be a rule, and the `[j]` offglide is still open.
- `README.md` — a section for the new converter, and the composition with `phonemic2orthography.py`.
- Move this plan to `plans/old/` in the same change that finishes the implementation, fixing its relative links from one level up to two, per [AGENTS.md's Plans section](../AGENTS.md#plans).

## Decisions (resolved 2026-08-27)

1. **`/ɾ/` or `/r/` as the output symbol?** Resolved: emit `r`. Confirms the default, and turned out to be the single most exercised rule in the real corpus — `ɾ → r` accounts for roughly 60 of the 65 rows where etic and emic differ. See [Validation against real held-out data](#validation-against-real-held-out-data).
2. **Should `[j]` map to `/ʒ/` anywhere?** Resolved: no. Confirms the default — `[j]` → `/j/`, free variation unmodelled and documented in `zhire/SPEC.md`.
3. **The three chart inconsistencies** (`nden`, `nggei`, `nzor`) — resolved: source errors, held out of the fixture. Confirms the default, though see the `nzor`/'chin' counter-evidence at the end of [Validation against real held-out data](#validation-against-real-held-out-data), found after this was confirmed — it doesn't change the rule set, but the linguist may want it before the fixture is finalised.
4. **`[l]`.** Resolved: pass through as `/l/`. Confirms the default, and the real corpus corroborates it directly — the same `[lāwūɾ]` 'sweet potato' word the sketch names as a Hausa loan appears in the held-out data too (`kàːmō làwùɾ` → `kàːmō làwùr`), `l` unchanged on both sides.
6. **Which phonetic notation is the real input?** Resolved: plain letters, not the sketch's modifier-letter notation. Confirmed directly — none of `ʷ ʲ ᵐ ⁿ ᵑ` occur anywhere in the 246-row real corpus's etic column. The modifier-letter transliteration in [The mapping](#the-mapping) is kept for compatibility with the sketch's own notation (someone may eventually paste from it) but is untested by real data and could be dropped from a first implementation if that's preferred.
7. **`[ɲ]` → `/nj/` (assertion 5), or leave `ɲ` unchanged?** Resolved 2026-08-27: implement the sketch's stated rule, `ɲ` → `nj`, even though it conflicts with 3 of the 246 real words. Those 3 fail the held-out fixture until their FLEx entries are corrected — deliberately not special-cased, per the user's instruction: "Don't try and build the FST rules around rare cases." Same instruction applies to the fixture generally — see 5b below.

## Open questions

Question 5 (is there held-out phonetic data?) is answered — see [Validation against real held-out data](#validation-against-real-held-out-data). What to do with it is now mostly resolved too:

5a. **Where should `phonetic2phonemic_public_test.csv` live as a checked-in fixture, and under what name?** Only columns 3–4 (etic, emic) are needed, per the user's instruction — the other four columns (`entry_id`, `sense_guid`, `grammatical_info`, `gloss_en`) are FLEx bookkeeping, not phonemic content. Still a default, not yet confirmed: **`zhire/tests/fixtures/phonetic2phonemic/{inputs,approved}/real_flex_export.txt`**, one word per line, columns 3 and 4 only, following the existing `words`/`loanwords` fixtures' shape.
5b. **Resolved 2026-08-27: keep known-anomalous rows in the fixture and let them fail**, rather than holding them out. User's instruction: "just let them fail, and I'll inspect the data and probably edit it. This is the same with other rare anomalies." Applies to the 2 genuine data anomalies (`kɨ́kjōɾākàp`, `kɨ́ɾ wèɡbī`) and, per decision 7 above, the 3 `ɲ` words too — all 5 stay in `real_flex_export` as ordinary mismatches with a reviewable diff. **Resolved differently for `ɡo᷅r**` 'payment', on the user's instruction (2026-08-27): strip the `**` from both columns when building the fixture.** Unlike the other 5, this row's problem isn't a phone-level rule question at all — `**` is FLEx annotation noise on both sides, not phonemic content, and would make `convert()` raise rather than produce a reviewable mismatch. Stripping it turns the row into an ordinary identical pair, and avoids a mechanical wrinkle the raise would otherwise cause: the CLI approval test feeds a whole fixture file through one `subprocess.run(..., check=True)` call, so a raising row would crash that *entire file's* test before producing any output, hiding the diff for the other 245 words along with it.
5c. **The `/ɲ/` gap in `phonemic2orthography.convert()` turns out not to matter for the composed pipeline.** Checked directly (see [Decisions](#decisions-resolved-2026-08-27) item 7): once `phonetic2phonemic` maps `ɲ` → `nj`, the sibling converter already accepts `nj` fine (`njōrɔ᷆` → `nyorɔ`), so `phonetic2phonemic.convert()` → `phonemic2orthography.convert()` never hits a literal `ɲ`. The gap is real in a narrower sense, though: the 3 real words' *emic* field itself contains literal `ɲ`, so anyone feeding that field straight into `phonemic2orthography.convert()` — bypassing this new converter — hits it today, independent of this plan. Worth a line in `phonemic2orthography`'s own Not Yet Specified section for that reason, but it isn't this plan's gap to close.
