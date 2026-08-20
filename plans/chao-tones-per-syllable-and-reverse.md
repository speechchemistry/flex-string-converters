# Per-syllable tone letters in `diacritics2chao.py`, then a reverse converter

Status: approved 2026-08-19. Change 1 implemented 2026-08-19; change 2 implemented 2026-08-20. Two changes, in this order; all
decisions settled with the user. Supersedes the earlier reverse-only draft this file replaced (renamed
from `chao-accents-reverse.md`), which assumed the forward converter would stay as it is.

## Context

**Change 1 — the forward converter should group tone letters by syllable.** Today
`converters/diacritics2chao.py` emits one whitespace-separated group per *tone diacritic*, so a diphthong
carrying one tone comes out as two groups: `kāī` → `kai ˧ ˧`, `kàí` → `kai ˨ ˦`. A group between spaces
should be a syllable, so those become `kai ˧` and `kai ˨˦` — the latter being exactly what the same
rising tone written on a single vowel already produces (`kǎ` → `ka ˨˦`). The payoff is that notational
variants of one tone converge instead of depending on how many vowels the writer put tone diacritics over.

**Change 2 — a reverse converter**, `nəjɛt ˨ ˨˧` → `nə̀jɛ᷅t`, so data held as spelling + tone letters can
be rewritten as the tone diacritics a FLEx lexeme form normally carries.

Change 1 also removes the one real wart in the earlier reverse-only draft, where `kai ˧` → `kāī` was
not stable if converted back. After it, the two directions agree: `kāī` → `kai ˧` → `kāī`.

### The shared idea: tone-bearing units

Both changes need the same notion, which neither converter has today — and which is why change 1 is
not a one-line tweak. Within a word:

- A maximal run of **adjacent vowel** grapheme clusters is **one** unit (a diphthong is one syllable).
- A cluster carrying a **syllabic mark** (`U+0329`, `U+030D`) is **its own** unit — `m̩` is a syllable
  on its own and never joins a following vowel.
- A **modifier letter** (Unicode category `Lm`: `ː`, `ʲ`, …) is transparent: it neither starts a unit
  nor breaks a vowel run.
- Anything else (a consonant letter, punctuation, a digit) breaks a vowel run without starting a unit.

Verified against the existing corpus with `regex`'s `\X`: `m̩pad` → `['m̩', 'p', 'a', 'd']` (the syllabic
mark stays with its consonant) and `kwoː` → `['k', 'w', 'o', 'ː']` (the length mark is its own cluster,
so a tone diacritic lands on `o`, giving `kwōː` and never `kwoː̄`).

Each converter gets its **own copy** of the vowel set and syllabic marks rather than importing the
other's: a converter has to stand alone as a FLEx Process, where a sibling import is not guaranteed to
resolve. Drift is caught by a test that imports both files and asserts the tables are identical — the
same trick used for the reverse tone table below.

## Change 1: per-syllable groups in `converters/diacritics2chao.py`

### Behaviour

`tone_diacritics_to_chao_letters()` emits **one group per tone-bearing unit that carries at least one
tone diacritic**, not one per tone diacritic. A unit's group is its tone diacritics' tone letters
concatenated in order, with **adjacent identical letters collapsed** (`˧` + `˧` → `˧`: a level tone
spread over a diphthong is just that level tone). Collapsing is safe to apply across the whole group
because no single tone diacritic's own letters repeat. Consequences:

| Input | Today | After change 1 |
| --- | --- | --- |
| `kāī` | `kai ˧ ˧` | `kai ˧` |
| `kàí` | `kai ˨ ˦` | `kai ˨˦` |
| `kǎǐ` (caron on both vowels) | `kai ˨˦ ˨˦` | `kai ˨˦˨˦` — no adjacent duplicates, so nothing collapses |
| `kǎ`, `kǎi`, `kāi`, `kaī` | `ka ˨˦` / `kai ˨˦` / `kai ˧` / `kai ˧` | all unchanged |
| everything in the current fixture corpus | — | **unchanged** (verified) |

All five `tests/fixtures/diacritics2chao/inputs/*.txt` files were scanned for a vowel run with more than one
tone-diacritic-carrying vowel: there are none, so **every approved file stays byte-identical** and no re-approval is
needed.

Two deliberate side effects, both confirmed with the user:

- **A word gap becomes exactly two spaces.** Today a wider input gap leaks through (`nə̀t  nə̀t` →
  `˨   ˨`, three spaces); no fixture covers it. `SPEC.md`'s step 4 is reworded from "any three-space run
  collapses to two" to "groups within a word are separated by one space and words by two".
- **`multisub()` goes.** The cluster walk looks each mark up individually, so Darius Bacon's CC-BY-SA
  helper is no longer used. Remove it, and update the README's Attributions line to drop the CC-BY-SA
  clause and the resulting-GPL-3 wording — the LGPL 2.1 attribution for
  `Extract_Chao_tone_letters_from_tone_diacritics.py` stays, so state the combined licence that follows
  from LGPL 2.1 alone.

### Implementation

The current regex pipeline cannot express this: once non-diacritic runs collapse to spaces, `˧ ˧` from a
diphthong is indistinguishable from `˧ ˨` from two syllables. Patching the collapsing regex ("collapse
a run to nothing when it contains no consonant") also mis-handles a syllabic consonant directly
followed by a tone-diacritic-carrying vowel (`m̩̄ā`), where nothing breaks between the two tone diacritics even though they
are two syllables. So `tone_diacritics_to_chao_letters()` becomes a grapheme-cluster walk, which is what the rule
is actually defined in terms of:

1. NFD-normalise; split on whitespace runs into words.
2. Per word, walk `regex.findall(r'\X', word)`, building the unit list per the rules above and
   collecting each cluster's tone diacritics, in order, into its unit.
3. Per unit that has tone diacritics: map each mark through `TONE_DIACRITIC_TO_CHAO_LETTERS` (as a dict), concatenate,
   collapse adjacent identical letters.
4. Join a word's groups with one space, and words that produced groups with two spaces; a word with no
   tone diacritics contributes nothing. This reproduces today's outputs for every fixture, including
   `cat nə̀t` → `˨` and `nə̀t nə̀t` → `˨  ˨`.

`convert()` is untouched — it still strips the 13 marks for `base_text` and appends
`tone_diacritics_to_chao_letters()`'s result.

### Tests (first, per TDD)

New in `tests/test_diacritics2chao.py`, extending the existing `tone_diacritics_to_chao_letters` block:

- `tone_diacritics_to_chao_letters("kāī") == "˧"` — a level tone over a diphthong is one group (collapsing).
- `tone_diacritics_to_chao_letters("kàí") == "˨˦"` — a contour spread over a diphthong is one group.
- `tone_diacritics_to_chao_letters("kǎi") == "˨˦"` — the same tone written on one vowel gives the same result.
  This pair is the point of the change.
- `tone_diacritics_to_chao_letters("kǎǐ") == "˨˦˨˦"` — concatenation without collapsing when the letters differ.
- `tone_diacritics_to_chao_letters("m̩̄ā") == "˧ ˧"` — a syllabic consonant is its own syllable even with no
  consonant after it (the case the regex shortcut got wrong). `sākpò` → `˧ ˨` already covers the
  ordinary "consonant between vowels" case.
- `convert("kāī") == "kai ˧"` — one `convert()`-level case; the rest is unchanged composition.

Synthetic `kai`-style forms are deliberate here: there are no attested diphthong forms to hand (see
[Approval corpus](#approval-corpus)), and [AGENTS.md's Testing
Approach](../AGENTS.md#testing-approach) wants a unit test to use whatever example shows its rule most
clearly.

## Change 2: `converters/chao2diacritics.py`

Plain Python 3, `regex` only, no `flextoolslib`; header block and CLI per [AGENTS.md's Converter
Conventions](../AGENTS.md#converter-conventions).

- `convert(input_string)` — the FLEx Process entry point; splits base text from the trailing
  tone-letter section, then delegates.
- `chao_letters_to_tone_diacritics(base_text, tone_letters)` — the placement engine, counterpart of
  `tone_diacritics_to_chao_letters()`, usable when the two parts are already separate (e.g. a module reading
  spelling and `Pitch` from two fields).
- `CHAO_LETTERS_TO_TONE_DIACRITIC` — the 13 pairs inverted, a standalone copy guarded by an inverse test.
- `TONE_BEARING_VOWELS` (`a e i o u y ɨ ʉ ɯ ɪ ʏ ʊ ø ɘ ɵ ɤ ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ ɶ ɑ ɒ ɚ ɝ`) and
  `SYLLABIC_MARKS` — copies of change 1's, guarded by an equality test.

### Algorithm

1. **Split.** `^(?P<base>.*?)\s+(?P<tones>[˥-˩][˥-˩ ]*)$`, non-greedy base so the longest legitimate
   trailing tone section wins. No match — including a line that is *entirely* tone letters, with no
   separator — means there is nothing to re-attach: return the input unchanged. So `convert("˥") ==
   "˥"` and `convert("cat") == "cat"`, round-tripping the forward converter's own results.
2. **Group.** Split the tone section on runs of **two or more** spaces into one list per word, then on
   single spaces into per-syllable runs. Two-or-more also absorbs the wider gaps today's forward
   converter can emit, so old data still parses after change 1 standardises on two.
3. **Find the units** in the base text, exactly as in change 1. After change 1 this is a strict 1:1
   correspondence — one tone group per unit — with no fallback branch, which is why change 1 comes
   first.
4. **Place.** For a unit of *m* vowels receiving a group of *k* tone letters:
   - the group maps to a single tone diacritic and *m* = 1 → use it: `ka ˨˦` → `kǎ`.
   - *k* = 1 → repeat that tone diacritic on every vowel: `kai ˧` → `kāī`.
   - *k* = *m* → one letter per vowel: `kai ˨˦` → `kàí`.
   - otherwise → bail out (step 6). This is where an **unmapped contour** lands — see
     [Deferred](#deferred-and-documented-contours-with-no-tone-diacritic-equivalent).

   The tone diacritic is appended at the end of its cluster and the whole result NFC-normalised, which
   canonically reorders the marks and recomposes where a precomposed form exists. Verified against the
   forward fixtures: `m + U+0329 + U+0304` → `m̩̄`, `ɛ + U+0303 + U+0300` → `ɛ̃̀`, `m + i + U+0301` → `mí`.
   Base-text spacing is reproduced exactly by splitting on whitespace runs *keeping the separators*.
5. **Round-trip status.** forward → reverse → forward is exact, and reverse → forward is exact. What is
   still not recoverable is *which* vowels of a diphthong were marked: `kāi` and `kāī` both give
   `kai ˧`, and the reverse writes `kāī`. Likewise `kǎi` and `kàí` both give `kai ˨˦`, and the reverse
   writes `kàí`. `SPEC.md` says so plainly.
6. **Bail out on any mismatch** — word counts differ, a word's group count differs from its unit count,
   a *k*/*m* combination not covered in step 4, or a tone-letter run that isn't one of the 13. Return
   the input unchanged rather than placing part of it:

   | Input | Unchanged (this plan) | Best-effort alternative |
   | --- | --- | --- |
   | `cat nət ˨` (forward output of `cat nə̀t` — the toneless word left no slot) | `cat nət ˨` | `càt nət` — tone on the wrong word, and it looks right |
   | `mi ˥ ˦` (forward output of `mí ˥` — a literal tone letter in the spelling) | `mi ˥ ˦` | `mí`, `˥` silently dropped |
   | `o ˥˩` / `ka ˨˩` (a contour with no tone diacritic among the 13) | unchanged | `o` / `ka`, tone silently lost |
   | `cat ˨ ˧ ˦` (more groups than units) | `cat ˨ ˧ ˦` | `càt`, two groups dropped |

   A line that comes back still visibly carrying its tone letters is self-diagnosing — the entries that
   didn't convert are obvious and the data can be fixed. Best-effort output is plausible-looking
   tone-diacritic notation indistinguishable from correct data, which matters most if this ever writes to a FLEx field
   (see [AGENTS.md's Data Safety](../AGENTS.md#data-safety)).

**Command line** exactly as `diacritics2chao.py`'s: positional text or stdin lines, one result per line,
results to stdout, diagnostics to stderr, `reconfigure(encoding="utf-8")` on both streams.

### Tests (first, per TDD)

`tests/test_chao2diacritics.py`, one rule per test:

- **Table guards**: `CHAO_LETTERS_TO_TONE_DIACRITIC` is the exact inverse of
  `diacritics2chao.TONE_DIACRITIC_TO_CHAO_LETTERS` (all 13, no duplicates either way), and the vowel set and
  syllabic marks are identical to change 1's.
- **One case per tone diacritic row**, parametrized off the reverse table: `chao_letters_to_tone_diacritics("o", "˥") == "ő"`.
- **Spec example**: `convert("nəjɛt ˨ ˨˧") == "nə̀jɛ᷅t"`.
- **NFC output**: `convert("mi ˦") == unicodedata.normalize("NFC", "mí")`, guarded by the NFD form
  differing.
- **Units**: a syllabic consonant carries a tone (`convert("m̩ ˧") == "m̩̄"`); a plain consonant cannot
  (`convert("n ˧")` unchanged); the length mark keeps the tone diacritic on the vowel (`convert("oː ˧") ==
  "ōː"`); an existing diacritic is stacked under, not replaced (`convert("ɛ̃ ˨") == "ɛ̃̀"`).
- **Diphthongs**: `convert("kai ˧") == "kāī"`, `convert("kai ˨˦") == "kàí"`, `convert("ka ˨˦") == "kǎ"`.
- **Words**: `convert("nət nət ˨  ˨") == "nə̀t nə̀t"`.
- **Passthrough**: `""`, `"cat"`, `"cat   dog"`, `"˥"` all returned unchanged.
- **Mismatch returns the input unchanged**: `"cat ˨ ˧ ˦"`, `"nət nət ˨"` (the toneless-word case),
  `"o ˥˩"`, and `"ka ˨˩"` (the unmapped contour).
- **Round trip**: for a curated list of tone-diacritic words — the forward converter's own unit-test
  words and the Plateau forms — `chao2diacritics.convert(diacritics2chao.convert(w)) ==
  unicodedata.normalize("NFC", w)`. The documented lossy cases stay out of that list and are covered by
  the mismatch tests; that split is the honest statement of what "reverse" guarantees.

### Approval corpus

The forward converter's **approved outputs are exactly this converter's inputs**, which makes the
reverse corpus a genuine round-trip regression net rather than a fresh set of guesses. Copy each
`tests/fixtures/diacritics2chao/approved/<stem>.approved.txt` to
`tests/fixtures/chao2diacritics/inputs/<stem>.txt` (`tone_diacritic_table`, `plateau_examples`, `words`,
`unicode_forms`, `whitespace_and_passthrough`), and add a `mismatches.txt` for the bail-out cases.
Approved files are produced *only* through the approval loop: run pytest, read each
`received/*.received.txt`, check it against the original forward input, then run the `cp` command the
failure prints — see the
[`adding-an-approval-fixture`](../.claude/skills/adding-an-approval-fixture/SKILL.md) skill.

**No diphthong fixture in either corpus for now.** There are no attested forms to hand, and after
commit `3a10d15` the corpus takes real words rather than inventions, so diphthongs stay in the unit
tests until real data exists. Recorded as a gap in [SPEC.md's Not Yet Specified
section](../SPEC.md#not-yet-specified) so it isn't forgotten.

To avoid a second copy of the ~100-line harness, lift the reusable parts of
`tests/test_diacritics2chao_cli.py` (`_input_fixtures`, `_promote_command`, `_assert_approved`, the
subprocess call with `encoding="utf-8"`) into `tests/approval.py`, parametrised by converter name and
fixture directory, and have both CLI test files use it. The existing forward tests staying green is
what makes that refactor safe.

## Documentation

- **`SPEC.md`**, change 1: rewrite `tone_diacritics_to_chao_letters()`'s steps 2–4 in terms of tone-bearing units
  — the unit rules, one group per tone-diacritic-carrying unit, concatenation with adjacent-duplicate collapsing, and
  the one-space/two-space wording. Change 2: a new "Tone Diacritics From Chao Tone Letters" section
  with the split rule, the *k*/*m* placement rules, the bail-out conditions, the worked example, and an
  explicit paragraph on what does not round trip.
- **`README.md`**: update the `diacritics2chao.py` examples for change 1, add a `chao2diacritics.py`
  subsection with its two CLI examples, note that the reverse corpus is fed by the forward converter's
  approved outputs, and correct the Attributions line now that `multisub()` is gone.
- **Not Yet Specified**: three entries — the reverse FlexTools module (deliberately not built), the
  missing diphthong fixtures (no attested forms yet), and the unmapped-contour rule (below).
- **This plan**: update the status line when it is approved, and again once it is implemented.

## Verification

- `python -m pytest` after change 1: the new diphthong and syllabic-nasal tests pass and **all five
  existing approved files are still byte-identical** (no `received/` files) — the check that change 1
  didn't disturb the established corpus.
- `python -m pytest` after change 2: both approval suites and the untouched module tests green.
- `python3 converters/diacritics2chao.py 'kāī'` → `kai ˧`; `python3 converters/diacritics2chao.py 'kàí'` →
  `kai ˨˦`.
- `echo 'nəjɛt ˨ ˨˧' | python3 converters/chao2diacritics.py` → `nə̀jɛ᷅t`.
- Round trip at the shell, both orders:
  `python3 converters/diacritics2chao.py 'm̩̄pa᷆d' | python3 converters/chao2diacritics.py` → `m̩̄pa᷆d`, and
  `python3 converters/chao2diacritics.py 'kai ˧' | python3 converters/diacritics2chao.py` → `kai ˧`.
- Confirm `SPEC.md` and the code agree, per AGENTS.md's rule that a mismatch between them is a bug.

## Settled

- **Change 1 is wanted**: the forward converter's behaviour changes to per-syllable groups.
- **Adjacent-duplicate collapsing** yes, so `kāī` → `kai ˧`; and `kǎǐ` → `kai ˨˦˨˦`, which no single
  tone diacritic maps back to, so the reverse bails on it. Not seen in the data yet either way.
- **Word gap** standardises on two spaces.
- **`multisub()`** is dropped, with the README Attributions line updated.
- **Tone-bearing segments**: hand-listed IPA vowel set plus the two syllabic marks. No `panphon`, so
  the dependency list stays at `regex` and both converters stay IronPython/Python.NET-safe.
- **Diphthong reading**: a diphthong is one syllable; a level tone repeats over its vowels and a
  contour distributes one letter per vowel (`kai ˧` → `kāī`, `kai ˨˦` → `kàí`).
- **Scope**: converters + tests + docs. No FlexTools module for the reverse direction (it would write
  lexeme forms — a much riskier write than `Pitch`).

## Deferred, and documented: contours with no tone diacritic equivalent

**Decision: defer (option 1 below).** An unmapped contour bails out and the line is returned unchanged.
The alternatives are documented rather than dropped, so the next person doesn't have to rediscover the
problem.

Only 8 of the possible contours have a tone-diacritic equivalent — `˨˦ ˦˨ ˧˦ ˨˧ ˨˦˨ ˧˨ ˦˧ ˦˨˦` — so a
contour like `˨˩` or `˥˩` cannot be written as a single tone diacritic at all. Every *level* letter does have
one (`˥ ˦ ˧ ˨ ˩` → double acute, acute, macron, grave, double grave), so any contour can in principle be
decomposed into level steps; the question is where to put them.

1. **Bail out unchanged** — chosen. `ka ˨˩` comes back as `ka ˨˩`: visibly unconverted, nothing
   invented, consistent with every other mismatch in step 6. The current Plateau data stays inside the
   8 contours, so nothing is lost today.
2. **Duplicate the vowel, one level tone diacritic per step** — `ka ˨˩` → `kàȁ`. Generalises cleanly, but
   **changes the spelling, not just the tone notation**: `kàȁ` forward-converts to `kaa ˨˩`, so the base
   text has gained a vowel and the round trip no longer returns the text it started from.
3. **Stack the level tone diacritics on one vowel** — `a` + grave + double grave. Keeps the spelling and
   round-trips exactly, but renders as two marks piled on one vowel and is not conventional notation.

Worth knowing whenever this is revisited: most Asian tone systems fall *outside* the 8 contours
(Mandarin 51/35/214, Cantonese 21/25, Thai 41/21), so this rule is what decides whether such data is
convertible at all. It is also why looking to Asia for diphthong fixtures needs care — those tone values
mostly can't be written as tone diacritics, so the forms would exercise this rule rather than the
clean diphthong path.

**Where this gets documented:**

- `SPEC.md`, in change 2's converter section: the *implemented* behaviour — an unmapped contour is one
  of the bail-out conditions, with `ka ˨˩` as the example, and a sentence naming the 8 mappable
  contours so the limit is visible rather than surprising.
- `SPEC.md`, [Not Yet Specified](../SPEC.md#not-yet-specified): one entry saying which rule will
  eventually replace the bail-out is undecided, listing options 2 and 3 in a line each with their
  trade-off (spelling changes vs. stacked marks).
- This plan keeps the full discussion, as the historical record of why option 1 was chosen.

## Changes since approval

- **2026-08-19, after change 1 landed:** the [Approval corpus](#approval-corpus) section's "no
  diphthong fixture in either corpus for now" decision is relaxed for the forward corpus. Rather than
  waiting indefinitely for an attested diphthong example, `AGENTS.md`'s Testing Approach now allows a
  linguistically plausible *constructed* fixture when no real one is at hand, provided the filename
  says so (a `_simulated` suffix) — the fixture has no comment lines to carry that label, so the
  filename is the only place it can live. `tests/fixtures/diacritics2chao/inputs/diphthongs_simulated.txt`
  was added on this basis, covering the same rules as the diphthong unit tests
  (level-tone collapsing, contour distribution, and convergence with the single-vowel spelling) with
  different words, so it doesn't duplicate them. The reverse corpus's diphthong gap (change 2, not yet
  built) is unaffected by this note and can use the same allowance when it's implemented.
- **2026-08-20, terminology rename:** "accent" is purged from the repository's vocabulary (it was
  never the right term — the combining marks are **tone diacritics**, the letters are **Chao tone
  letters**), and this plan's own body is updated to match rather than left with the old wording, since
  it documents behaviour that is still current. Renamed: `converters/chao_tones.py` →
  `converters/diacritics2chao.py`; `converters/chao_accents.py` → `converters/chao2diacritics.py`;
  `extract_chao_letters()` → `tone_diacritics_to_chao_letters()`; `apply_chao_letters()` →
  `chao_letters_to_tone_diacritics()`; `ACCENT_TO_TONE_LETTERS` → `TONE_DIACRITIC_TO_CHAO_LETTERS`;
  `TONE_LETTERS_TO_ACCENT` → `CHAO_LETTERS_TO_TONE_DIACRITIC`; `TONE_ACCENT_MARKS` → `TONE_DIACRITICS`;
  the FlexTools module `Extract_Chao_tone_letters_from_accent_notation.py` →
  `Extract_Chao_tone_letters_from_tone_diacritics.py` (with `FTM_Version` bumped 0.8 → 0.9); the test
  files and fixture directories renamed to match (`tests/test_diacritics2chao*.py`,
  `tests/test_chao2diacritics*.py`, `tests/fixtures/diacritics2chao/`, `tests/fixtures/chao2diacritics/`);
  and the `accent_table` fixture stem renamed to `tone_diacritic_table` in both fixture trees. `convert()`
  keeps its name in both converters, since it is the SIL FLEx Process entry-point contract. No behaviour,
  table contents, or fixture bytes changed — confirmed by the test suite staying at 106 passing throughout.
