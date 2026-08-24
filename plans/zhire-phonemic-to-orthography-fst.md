# Zhire phonemic-to-orthography converter, built as a pynini FST

Status: proposed 2026-08-24, not yet implemented. `pynini` is installed, and the whole mapping table
below has been validated against 99 real phonemic/orthographic word pairs (see [Validation against
real sample data](#validation-against-real-sample-data)) with a throwaway prototype — not yet the
actual converter file. Approval-test fixtures and a failing (pre-implementation) test file have been
committed from that same sample data; the converter itself has not.

## Why

The Zhire `[zhi]` language community has a draft orthography statement
(`zhi_orthography_statement.md`, on the NRG Language Drive, authored by Tim Kempton) that fixes a
phoneme-to-grapheme correspondence for vowels, consonants, and a handful of modified (labialised,
palatalised, nasalised, long) sounds. This plan adds a `convert()` in the `zhire` project folder
(scaffolded in [`plans/split-into-per-project-folders.md`](split-into-per-project-folders.md)) that
turns a phonemic transcription into the corresponding orthographic spelling, so literacy materials can
be generated from phonemic source data instead of respelled by hand.

Per the user's explicit request, the segmental phoneme-to-grapheme mapping is implemented
**exclusively as a finite-state transducer using [pynini](https://pypi.org/project/pynini/)** — not as
ad hoc string substitution — even though the mapping itself is simple (no context-dependent rewrite
rules are needed). Tone-diacritic stripping is the one exception: the user has confirmed it doesn't
need to go through the FST, and it's considerably simpler done as an ordinary Python preprocessing
step (see [Tone](#tone-confirmed-tonal-strip-on-the-way-to-orthography) below) — everything downstream
of that step is FST-only.

## Source of truth for the mapping

Two sources, and where they disagree, the real sample data wins:

1. `zhi_orthography_statement.md`'s three correspondence tables and one paragraph of prose, read from
   the actual file (not a pasted copy — a copy pasted through the chat transport arrived with corrupted
   IPA characters; reading the file directly avoided baking that corruption into this repository).
2. `sample_phonemic2orthographic_data.csv`, 99 real phonemic/orthographic word pairs supplied directly
   by the user (see [Validation against real sample data](#validation-against-real-sample-data)).

The orthography statement's tables use IPA modifier letters (`ʷ` labialisation, `ʲ` palatalisation,
`ᵑ`/`ᵐ`/`ⁿ` prenasalisation) to mark several phonemes as fused units — e.g. `/hʷ/` for the "wh" sound,
`/ᵑɡ/` for the prenasalised "ngg" sound. **None of those modifier letters appear anywhere in the real
sample data.** It spells these with plain letter sequences instead (`hw` for what the statement calls
`hʷ`; a plain `n` followed by `d` for what it calls `ⁿd`; etc.). Per your confirmation, the phonemic
data may eventually adopt the statement's `Cʷ`/`Cʲ` modifier-letter notation, but for now it's plain
sequences, so **this converter only handles plain-letter sequences** — the modifier-letter forms are
explicitly out of scope until real data actually uses them.

This turns out to simplify the mapping table substantially: most of the orthography statement's
"complex" consonant rows (`ᵐb`, `ⁿd`, `ᵑɡ`, `ⁿdz`, `ɡb`, `kp`, and even `ɲ`/`nʲ` via the plain spelling
`nj`) don't need their own table entry at all — they fall out for free from concatenating the already-
tabled *plain* consonants (`m`+`b` → `mb`, `n`+`d` → `nd`, `ŋ`+`ɡ` → `ngg`, `n`+`j` → `ny`, …), because
in every one of those cases the target grapheme literally is the concatenation of the components'
individual graphemes. Confirmed empirically against all 99 real examples — see below.

### Vowels (one grapheme per phoneme)

| Phoneme | Grapheme |
| ------- | -------- |
| a       | a        |
| e       | e        |
| ɛ       | ɛ        |
| ə       | ə        |
| i       | i        |
| o       | o        |
| ɔ       | ɔ        |
| u       | u        |

### Atomic consonants (one grapheme per phoneme — these don't decompose into anything simpler)

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

### Overrides — the only sequences that need an explicit table entry, because naive per-character
concatenation of the atomic consonants above would give the *wrong* answer

| Input sequence | Grapheme | Why it can't just fall out of concatenation |
| --------------- | -------- | --- |
| `dʒ`            | `j`      | `d`→`d` + `ʒ`→`zh` would wrongly give `dzh`; real example: `dʒùrɔ̄` → `jurɔ` |
| `hw`            | `wh`     | letter order flips (`h`,`w` → `w`,`h`); real example: `hwōrì` → `whori` |
| `ɕw`            | `why`    | `ɕ` isn't a phoneme on its own — only ever attested as part of this pair; real example: `ɕwú` → `whyu` |
| `ʑw`            | `yh`     | `ʑ` isn't a phoneme on its own either; real example: `ʑwòŋʑwǒŋ` → `yhongyhong` |

Everything else the orthography statement documents as a "complex" phoneme (`ɡb`, `kp`, `ts`, `dz`,
`ᵐb`/plain `mb`, `ⁿd`/plain `nd`, `ᵑɡ`/plain `ŋɡ`, `ⁿdz`/plain `ndz`, `tʷ`/plain `tw`, `tʲ`/plain `tj`,
`ɲ`/`nʲ`/plain `nj`) needs **no table entry at all** — concatenating the atomic consonants (and, for
`nj`, `n`→`n` and `j`→`y`) already produces the right grapheme, confirmed against real examples of most
of these in the sample data.

### General rules (not literal table rows — generalised from one worked example each, per your
confirmation that both generalise to every vowel)

- **Length**: any vowel followed by the IPA length mark `ː` (U+02D0) doubles that vowel's grapheme —
  generalises the table's only example, `/iː/ → ii`.
- **Nasalisation**: any vowel followed by a combining tilde `◌̃` (U+0303) keeps the tilde on output —
  generalises the table's only example, `/ã/ → ã` (which is exactly `a` + combining tilde in NFD, and
  recomposes to the single codepoint `ã` in NFC).
- **Confirmed**: a vowel that is both nasalised and long doubles the whole nasalised unit, e.g.
  `ɔ̃ː` → `ɔ̃ɔ̃` (tilde on each copy).

### Tone (confirmed tonal; strip on the way to orthography)

None of the orthography statement's example spellings carry a tone mark, and the "Tone" section of the
statement is still an open placeholder (no orthographic tone-marking rule decided yet). Per your
confirmation, phonemic input **is** tonal, so `convert()` deletes tone diacritics rather than rejecting
them.

**This step is a plain Python preprocessing pass, not part of the FST** — the user confirmed it
doesn't need to go through the transducer, and it's simpler this way. Rather than enumerating a fixed
list of tone diacritics (which risks missing one — the user confirmed it "doesn't matter... they will
all get stripped"), the rule is general: after normalising to NFD, delete every combining mark
(`unicodedata.category(ch) == "Mn"`) **except** the nasalisation tilde `U+0303`, which is the one
combining mark this converter needs to keep. This covers every tone mark actually seen in the
orthography statement's examples (grave, acute, macron, the `᷄ ᷅ ᷆ ᷇` contour marks) and, unlike an
enumerated list, also covers any tone diacritic Zhire fieldwork data uses that the statement doesn't
happen to illustrate — directly resolving the concern about the 13-item list's completeness.

### Unmapped input

Per your confirmation: any input symbol that is not one of the above phonemes, not a tone diacritic to
strip, and not the ASCII space (kept as a word divider) causes `convert()` to raise an error — it does
not pass through unchanged and does not silently drop the character. This includes stray IPA symbols
that exist in the phonology but haven't been assigned a grapheme yet (e.g. anything from the still-open
"(Syllabic nasals)" or "(Prenasalised consonants)" placeholder sections beyond what's already in the
consonant table). There is no hyphen-passthrough rule: the one sample-data row that had a hyphen turned
out to be a typo (see below) and the corrected form doesn't have one, so this hasn't come up for real
yet — add it if/when a genuine case does.

## Validation against real sample data

The user supplied `sample_phonemic2orthographic_data.csv` — 99 real phonemic/orthographic word pairs
(header `zhi-fonipa-x-emic,zhi`) — specifically as test data for this converter. Before writing any
fixtures, the table above (vowels + atomic consonants + the four overrides + the length/nasalisation
generalisations) was validated against every row with a throwaway prototype using the real `pynini` API
(not assumed from memory): **99/99 rows matched exactly**, after one correction:

- Row `ʑwòng-ʑwǒng,yhong-yhong` had two problems the user confirmed as a data-entry slip: the trailing
  syllable's `/ŋ/` was typed as the ASCII digraph `ng` instead of the single letter `ŋ` (inconsistent
  with every other `/ŋ/` in the sheet, e.g. `ŋɡùm` → `nggum`), and there was a spurious hyphen. The
  corrected pair used for the fixture is `ʑwòŋʑwǒŋ` → `yhongyhong`.

This validation is also what surfaced the `hw`/`ɕw`/`ʑw` overrides and confirmed the orthography
statement's modifier-letter notation (`ʷ`, `ʲ`, `ᵑ`, `ᵐ`, `ⁿ`) isn't actually used anywhere in real data
— see [Source of truth for the mapping](#source-of-truth-for-the-mapping) above.

## FST architecture

Validated directly against the installed `pynini` (see the worked prototype below) rather than assumed
from memory of the API.

1. **Normalise input to NFD**, then **strip tone diacritics** as described above (plain Python, not
   the FST): delete every `Mn`-category combining mark except `U+0303`. What reaches the FST is a
   tone-free but still possibly-nasalised, possibly-lengthened phonemic string.

2. **Build one token lexicon** as a plain Python list of `(input_phoneme, output_grapheme, weight)`
   triples, assembled from, in order: the 8 vowels, the 21 atomic consonants, the 4 overrides (`dʒ`,
   `hw`, `ɕw`, `ʑw`), one space → space identity pair, and the *generated* length/nasalisation pairs —
   produced by a small Python loop over the 8 vowels (not hand-written), covering plain nasalised,
   plain lengthened, and nasalised-and-lengthened forms for each vowel. Nothing else needs a row — see
   [Source of truth for the mapping](#source-of-truth-for-the-mapping) for why the rest of the
   orthography statement's "complex" phonemes fall out of these for free. Building this list in Python,
   then handing the whole thing to pynini in one call, is what keeps this "a simple mapping" per your
   framing, rather than a cascade of hand-written rewrite rules.

3. **Give every pair the same weight (`"1"`).** This is what actually produces maximal munch: with a
   uniform per-token cost, `pynini.shortestpath` (tropical semiring — minimises the *sum* of weights)
   ends up minimising the *number of tokens* used, which prefers one long token over several short ones
   covering the same span. (A weight proportional to *token length* — my first instinct — doesn't work:
   the total consumed length is fixed by the input regardless of how it's tokenised, so every
   tokenisation would sum to the same total and shortestpath couldn't discriminate between them.
   Uniform-cost-per-arc is the correct idiom, confirmed by testing both.)

4. **Compile with `pynini.string_map(pairs, input_token_type="utf8", output_token_type="utf8")`**, then
   take its `.closure()` so it can consume an arbitrary sequence of tokens. `token_type="utf8"` is
   essential: pynini's default byte-level FSTs treat each UTF-8 *byte* as a symbol, which would shred
   every multi-byte IPA character (`ɲ`, `ɡ`, `ʃ`, the modifier letters, …) into meaningless byte
   fragments. `token_type="utf8"` makes each Unicode codepoint one symbol, matching the phoneme-level
   pairs above.

5. **Compose the closure with an acceptor built from the (tone-stripped) input string**
   (`pynini.accep(input, token_type="utf8")`), via `input_acceptor @ token_star`.

6. **Detect unmapped input as an empty composition.** If any substring can't be covered by some
   combination of known tokens, the composed FST has no accepting path. Checked with
   `lattice.start() == pynini.NO_STATE_ID or lattice.num_states() == 0` — `convert()` raises a
   `ValueError` naming the offending input in that case, rather than returning a partial result.

7. **Resolve ambiguity with `pynini.shortestpath(lattice)`**, then extract the output string with
   `.string(token_type="utf8")`.

8. **Normalise the result to NFC** before returning, so e.g. `a` + combining tilde comes back as the
   single codepoint `ã`, matching the orthography statement's own spelling.

### Worked prototype (confirms the above; not the final converter code)

```python
import pynini

pairs = [("g", "g", "1"), ("b", "b", "1"), ("gb", "GB", "1"), ("a", "a", "1"), (" ", " ", "1")]
token_star = pynini.string_map(
    pairs, input_token_type="utf8", output_token_type="utf8"
).closure()

def convert(s):
    lattice = pynini.accep(s, token_type="utf8") @ token_star
    if lattice.start() == pynini.NO_STATE_ID or lattice.num_states() == 0:
        raise ValueError(f"no valid tokenization for: {s!r}")
    return pynini.shortestpath(lattice).string(token_type="utf8")

convert("gba")  # -> "GBa": gb (one token) beats g+b, confirming maximal munch
convert("gbx")  # -> raises ValueError: x is unmapped
```

Extending this with the real vowel/nasal/length pairs and running it on `kàm` → `kam` (tone stripped
before reaching the FST), `ã` → `ã`, `iː` → `ii`, and `ɔ̃ː` → `ɔ̃ɔ̃` all round-tripped correctly.

## What this converter deliberately does not attempt

Kept out of scope because the orthography statement itself hasn't decided these yet (its own section
headings for them are still open placeholders) — consistent with
[AGENTS.md's rule against speculatively extending a spec](../AGENTS.md#specification):

- Syllabic nasals, beyond the ones already in the main consonant table.
- General morphophonological rules (nasal assimilation, vowel harmony, word-boundary coalescence).
- Tone *marking* in the orthography (tone is stripped, not re-marked — there is currently no
  orthographic tone convention to re-mark it with).
- Capitalisation and punctuation conventions (including hyphens — no real example needs one yet).
- The orthography statement's `Cʷ`/`Cʲ`/`ᵑ`/`ᵐ`/`ⁿ` modifier-letter notation — per your confirmation,
  real phonemic data may eventually adopt it, but for now it's all plain letter sequences, so this
  converter only handles those.

These belong under `zhire/SPEC.md`'s own Not Yet Specified section once that file exists for real,
not as speculative behaviour built into this converter now.

## File layout

Following the [`adding-a-project`](../.claude/skills/adding-a-project/SKILL.md) skill's shape, inside
the `zhire/` folder already scaffolded:

- `zhire/converters/phonemic2orthography.py` — the converter, per
  [AGENTS.md's Converter Conventions](../AGENTS.md#converter-conventions): header block, `convert()`,
  and a command line interface under `if __name__ == '__main__':` matching the existing converters'
  shape (stdin-as-filter, or arguments converted one per line).
- `zhire/tests/conftest.py` — `sys.path` wiring for `zhire/converters/` and the repo's shared `tests/`
  (for the approval-testing harness). **Committed** (this plan's own change), ahead of the converter.
- `zhire/tests/test_phonemic2orthography.py` — inline unit tests, one per *general rule* (tone
  stripping, length doubling, nasalisation, the override sequences, the unmapped-input error), each
  with one clear example, per
  [AGENTS.md's rule against duplicating the two test layers](../AGENTS.md#testing-approach).
  **Committed**, deliberately failing (`ModuleNotFoundError`) until the converter exists — the TDD
  "red" step.
- `zhire/tests/fixtures/phonemic2orthography/{inputs,approved}/words.txt` — the 99 real word pairs from
  `sample_phonemic2orthographic_data.csv` (with the one correction noted above), one phonemic
  transcription per line and its orthographic spelling on the matching line of the approved file —
  real attested data from the user, exactly what
  [AGENTS.md's Testing Approach](../AGENTS.md#testing-approach) prefers over constructed examples.
  **Committed.**
- `zhire/tests/test_phonemic2orthography_cli.py` — the approval test driving those fixtures through the
  CLI, following `chao-tone-letters/tests/test_diacritics2chao_cli.py`'s shape. **Committed**,
  deliberately failing until the converter exists.
- `zhire/converters/phonemic2orthography.py` — the converter itself, per
  [AGENTS.md's Converter Conventions](../AGENTS.md#converter-conventions): header block, `convert()`,
  and a command line interface under `if __name__ == '__main__':` matching the existing converters'
  shape (stdin-as-filter, or arguments converted one per line). **Not yet written** — this is the next
  step, to make the above go green.

## Documentation to update once this is implemented (not part of this plan's own changes)

- `zhire/SPEC.md` — replace the "nothing implemented yet" placeholder with the converter's actual
  contract, following `chao-tone-letters/SPEC.md`'s shape.
- Root `SPEC.md` — add the `zhire` entry to the Projects list (deliberately not done yet — see
  [AGENTS.md's Specification section](../AGENTS.md#specification) on not registering a project ahead
  of its converter existing).
- `README.md` — a `zhire/` section following the existing `chao-tone-letters/` sections' shape, naming
  `pynini` as a dependency and noting its platform support explicitly (pip-installable prebuilt wheels
  on Linux; macOS and Windows need conda-forge, and Windows has no native wheel at all — install via
  WSL there). This also means, like `chao2diacritics.py` today, there is no FlexTools module planned
  for this converter for now: FlexTools modules run under Python .NET/IronPython on Windows, which
  pynini does not support.

## Open items

All resolved:

1. ~~pynini needs installing~~ — done; installed and its API validated against the prototype above.
2. ~~Confirm the `nj` → `ny` collision risk~~ — confirmed not an issue.
3. ~~Confirm the nasalised-and-lengthened-vowel assumption~~ — confirmed: double the whole nasalised
   unit (`ɔ̃ː` → `ɔ̃ɔ̃`).
4. ~~Confirm the tone-diacritic list is complete~~ — moot: tone stripping now uses the general
   "any combining mark except the nasalisation tilde" rule rather than an enumerated list, so
   completeness of any specific list is no longer a concern.

Ready to implement.
