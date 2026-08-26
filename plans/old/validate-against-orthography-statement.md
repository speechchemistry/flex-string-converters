# Validate the Zhire converter against the orthography statement, not just the sample data

Status: proposed and implemented 2026-08-26. All three gaps closed and all three open items answered by the language consultant — see [Resolution](#resolution).

## Why

`converters/phonemic2orthography.py` is missing `/tʃ/ → c`, so 'tree' `tʃi᷆` converts to `tshi` instead of `ci`. That gap was found by the language consultant reading the code, not by any test.

It is the second gap of the same kind, and looking properly turned up a third (`/ᵑᵐɡb/ → ngb`). `/l/` was the first, missing until a held-out word exercised it (see [`plans/old/zhire-phonemic-to-orthography-fst.md`](zhire-phonemic-to-orthography-fst.md)'s corrections section and the commit that added `/l/`). All three share one root cause, and this plan exists to fix the cause rather than a fourth symptom.

**The mapping table was derived from what made the 99 sample words pass, not from the orthography statement's tables.** The original plan states this in its own words: "This validation is also what surfaced the `hw`/`ɕw`/`ʑw` overrides." Deriving the spec from the test data means anything the sample happens not to contain is invisible.

`/dʒ/ → j` and `/tʃ/ → c` are structural twins — affricates whose grapheme is *not* the concatenation of their parts. `dʒ` occurs in exactly **one** of the 99 sample words, so it was caught. `tʃ` occurs in **none**, so it was not. Nothing about the reasoning distinguished them; only the sample did.

Two things then hid the gap:

- **"99/99 rows matched exactly" reads as validation of the mapping table, but only measures coverage of the sample.** A complete-looking number stood in for a completeness check that was never run.
- **The original plan asserts the statement's other complex phonemes "fall out of concatenation", listing `ɡb`, `kp`, `ts`, `dz`, `mb`, `nd`, `ŋɡ`, `ndz`, `tw`, `tj`, `nj`.** That is the subset that was considered, not an enumeration of the statement's 32 consonant rows. `/tʃ/` is exactly the row where concatenation gives the wrong answer, and enumerating the rows would have shown it immediately.

After `/l/`, [`zhire/SPEC.md`](../../zhire/SPEC.md)'s Not Yet Specified section recorded that it was "worth checking the implemented inventory against the orthography statement's tables in one pass". Filing that as future work rather than running it is what allowed `/tʃ/` to survive another two commits.

## What the systematic pass found

That pass has now been run, against `zhi_orthography_statement.md` (on the NRG Language Drive) read directly from the file rather than from a pasted copy, for the same reason the original plan gives — a pasted copy arrives with corrupted IPA.

Testing every row in the statement against `convert()` — each phoneme both as written and with modifier letters replaced by their plain-letter equivalents — **three disagree**:

| Statement | Grapheme | Best any input form gives | Verdict |
| --- | --- | --- | --- |
| `/tʃ/` | `c` | `tsh` | Real gap — needs an override entry |
| `/ᵑᵐɡb/` | `ngb` | `nggb` (from `ŋɡb`), `ngmgb` (from `ŋmɡb`) | Real gap — but the input form has to be settled first, see [Open items](#open-items) |
| `/ɾ/` | `r` | raises | Notation difference — see [Open items](#open-items) |

**The prenasalised labial-velar cannot fall out of concatenation, because the orthography is asymmetric about it.** `/ᵑɡ/` → `ngg` keeps the `ɡ` (`ŋ` + `ɡ` = `ng` + `g`), but `/ᵑᵐɡb/` → `ngb` drops it: `ngb` is `ng` + `b`, not `ng` + `gb`, which would give `nggb`. Of the plausible phonemic spellings only `ŋb` happens to produce `ngb`, and that omits the `ɡb` entirely, so it is unlikely to be what the data writes.

The first two rows were missed for the same reason `/l/` was: the sound is absent from the sample data, so nothing forced it to surface. The sample contains `ɡb` once and `ŋɡ` five times, but `ŋɡb`, `ŋmɡb`, `ŋb` and `ᵑ` zero times each.

**`/ᵑᵐɡb/` was also missed by the first version of this plan's own check**, which skipped every modifier-letter row as out of scope on the strength of the original plan's claim that their plain equivalents fall out of concatenation. That claim holds for `mb`, `nd`, `ŋɡ` and `ndz` — it was verified for those — and is false for exactly this row, which is the row the check declined to test. Trusting an untested assertion about which rows need testing is what let it through, and it is the reason the exhaustive fixture below is now the first thing to build rather than an optional extra.

Two further findings, checked and dismissed as non-issues, recorded so they are not re-investigated:

- `[ɨ]` appears in one *phonetic* example (`[ɣɨ᷅ɾ]` → `ghər`) and nowhere in the phoneme tables, so it is an allophone of `/ə/`, not a missing vowel. The sample data uses `ə` 12 times and `ɨ` zero times.
- `[tsʼ]` in `[tsʼēn]` → `tsen` carries an ejective mark (`U+02BC`, category `Lm`), again phonetic detail absent from the phoneme tables.

Counts that establish the blind spot, for the record: in the sample data `tʃ` occurs 0 times against `dʒ`'s 1; `ɾ` occurs 0 times against ASCII `r`'s 47.

## Changes

Only `/tʃ/` is unblocked; `/ᵑᵐɡb/` and `/ɾ/` wait on [Open items](#open-items).

- **`zhire/converters/phonemic2orthography.py`** — add `'tʃ': 'c'` to `OVERRIDES`, beside `'dʒ': 'j'`. It belongs there rather than in `ATOMIC_CONSONANTS` for the same reason `dʒ` does: `t` + `ʃ` concatenates to `tsh`, so the sequence needs an entry that beats its parts. Maximal munch then prefers it, as it already does for `dʒ`.
- **`zhire/tests/fixtures/phonemic2orthography/`** — a new fixture pair built from the statement's two attested `/tʃ/` examples, `tʃi᷆` → `ci` ('tree') and `tʃū` → `cu` ('grasshopper'). Real attested data, so no `_simulated` suffix is needed. Added first, with the received output confirmed wrong before the converter changes, then promoted with the command the failure prints — the TDD loop [AGENTS.md's Testing Approach](../../AGENTS.md#testing-approach) requires.
- **No new unit test.** `/tʃ/ → c` introduces no new rule; it is another row in an existing table, and the fixture covers it. Adding one would duplicate the corpus, which [AGENTS.md](../../AGENTS.md#testing-approach) rules out.
- **`zhire/SPEC.md`** — overrides table goes from four rows to five; the "every other complex sequence falls out of concatenation" sentence is re-checked so it no longer implies `/tʃ/` among them; and the inventory-completeness note under Not Yet Specified is replaced by what this pass actually found, since the open question it described has now been answered.

## Build the exhaustive check first

This is now the **first** thing to build, not an optional extra. It found `/ᵑᵐɡb/` in one pass, after two rounds of row-by-row reasoning had missed it — and the whole failure mode this plan addresses is a mapping gap that no test can see. Fixing `/tʃ/` without it would just leave the next gap waiting for the next held-out word.

The mechanism: **make the orthography statement's own worked examples into test data**, so the statement's ground truth becomes a regression net. Each example gives a phonetic form and its orthographic spelling, which is exactly an input/approved pair.

Three things make this less mechanical than it sounds, and shape which form it should take:

- **It has to be curated, not copied.** 11 of the 47 examples use the modifier-letter notation that is deliberately out of scope, and a few carry phonetic detail (`[ɨ]`, `[tsʼ]`) that phonemic input would not have. A fixture including them would fail by design, so the excluded rows have to be chosen deliberately — and the filename or a SPEC note has to record that it is a curated subset, since a fixture carries no comment lines.
- **It is a snapshot.** The statement lives on the NRG Language Drive, not in this repository, so a test cannot read it directly and would not notice the statement changing. The fixture pins what the statement said when it was taken; keeping it current is a manual re-run.
- **Phonetic versus phonemic.** The examples are phonetic (square brackets) while `convert()` takes phonemic input. For most rows these coincide, but where they don't the phonetic form is the wrong input, which is what the curation above is really resolving.

An alternative worth weighing: rather than a checked-in fixture, a small script kept in the repo that re-runs the comparison against the statement on demand, reporting disagreements. It cannot run in CI or on a machine without the drive mounted, but it never goes stale, and it is the thing to run whenever the statement is revised.

## Open items

1. **What does phonemic data write for the prenasalised labial-velar `/ᵑᵐɡb/` ('granary', `ngban`)?** This blocks fixing it, because the override's input side depends entirely on the answer. `ŋɡb` and `ŋmɡb` both need a new override entry to reach `ngb`; `ŋb` already works today and needs nothing. The sound appears nowhere in the sample data, so there is no evidence to infer it from — this one genuinely needs the consultant.
2. **`/ɾ/` — add `ɾ` → `r` as accepted input, or leave it unmapped?** The statement's phoneme column uses the tap `/ɾ/`; the sample data uses ASCII `r` 47 times and `ɾ` never. Adding it is free and creates no ambiguity, and it means data entered per the statement's own notation converts instead of erroring. Against: the original plan's stated principle is to handle only the notation real data actually uses, which is why the `ʷ`/`ʲ`/`ᵑ`/`ᵐ`/`ⁿ` forms are out of scope, and `/ɾ/` falls under the same rule. Recommendation: add it, as cheap insurance against a notation the source of truth uses — but this is the consultant's call, and the answer should be recorded in `zhire/SPEC.md` either way.
3. **Which form should [the exhaustive check](#build-the-exhaustive-check-first) take** — curated fixture, on-demand script, or both?

## What this deliberately does not attempt

- The `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation stays out of scope, unchanged from the original plan.
- Allophonic input (`[ɨ]` for `/ə/`, the ejective mark) stays out of scope: `convert()` takes phonemic input, and accepting phonetic detail is a different feature.
- The frozen plan in `plans/old/` is not edited to add `/tʃ/` to its tables. Its tables record what was approved at the time, and [AGENTS.md's Plans section](../../AGENTS.md#plans) says not to fix a plan to match later reality.

## Resolution

All three open items were answered by the language consultant, and all three gaps are closed. The converter now agrees with every one of the 47 phoneme rows in the statement.

- **`/ŋmɡb/ → ngb` confirmed** as the input spelling, so `'ŋmɡb': 'ngb'` is an override. It is the only prenasalised consonant needing one: `mb`, `nd`, `ŋɡ` and `ndz` all concatenate correctly.
- **`/ɾ/` accepted.** `[r]` and `[ɾ]` are allophones and the data writes `/r/`, but the statement's phoneme column uses `/ɾ/`. Rather than adding a 23rd phoneme, this went into a separate `INPUT_VARIANTS` table — an alternate notation for a phoneme already listed, so the "one grapheme per phoneme" reading of `ATOMIC_CONSONANTS` stays true.
- **Curated fixture only, no script.** Built as `orthography_statement_phonemes`, one line per phoneme row with the statement's grapheme column as approved output.

### The worked examples turned out not to be usable, and that changed the fixture's design

The plan above assumed the statement's 47 worked examples could become input/approved pairs. They cannot: **the examples are phonetic and `convert()` takes phonemic input.** Transliterating the modifier letters is not enough, because the phonetic forms also carry allophony.

Three examples disagreed even after all three mapping fixes, and every one turned out to be allophony rather than a converter gap — each converts correctly once written phonemically:

| Statement example | Wanted | As phonetic | As phonemic | The allophony |
| --- | --- | --- | --- | --- |
| `[ɣɨ᷅ɾ]` | `ghər` | `ɣɨɾ` raises | `ɣər` → `ghər` | `[ɨ]` realises `/ə/` |
| `[ⁿdɛ̀n]` | `nden` | `ndɛn` → `ndɛn` | `nden` → `nden` | `[ɛ]` realises `/e/` |
| `[ᵑɡēj]` | `nggei` | `ŋɡej` → `nggey` | `ŋɡei` → `nggei` | a `[j]` offglide realises `/i/` |

So the fixture is built from the statement's **phoneme column**, which is phonemic on both sides and needs no such inference. Using the worked examples would require encoding allophony rules that are not settled and are outside this converter's scope — recorded under `zhire/SPEC.md`'s Not Yet Specified as observed but unconfirmed, not implemented.

This is worth keeping in mind for any future attempt to widen the fixture: the statement's example columns look like free test data and are not.

### One convention change this forced

A spec-derived fixture cannot use the promote loop, because promoting makes the converter its own judge — the test would then only ever confirm what the converter already does, which is exactly the false confidence that let three phonemes go missing. Both sides are therefore written from the statement. [AGENTS.md's Testing Approach](../../AGENTS.md#testing-approach) has a new bullet carving this out as the single exception to "never write into `approved/` any other way", with the derivation recorded in `zhire/SPEC.md` so the fixture can be rebuilt when the statement changes.
