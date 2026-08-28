# Position-agnostic Chao tone letter reader, with warnings on stderr

Status: proposed and approved 2026-08-28, implemented 2026-08-28. The design was prototyped end to end before being written down, and every number below is measured rather than assumed — see [Prototype results](#prototype-results-measured-not-assumed). No converter, test, fixture or `SPEC.md` change has been made yet.

## Why

`chao-tone-letters/converters/chao2diacritics.py` currently accepts exactly one input shape: base text, then whitespace, then a trailing section of Chao tone letters, in which a run of two or more spaces separates one word's tone letters from the next word's and a single space separates the syllables within one word. That convention is invisible in a spreadsheet cell, survives no copy-paste, and carries information nowhere else in the file format does.

It also fails in a way that is easy to misread as success. When the spacing is wrong the whole line is returned unchanged, so a pipeline keeps running and the output still looks like text. The user hit this twice in one session on real data: once because `awk` spliced an unquoted field into a shell command, which collapsed the double spaces to single ones, and once because the TSV field carried a trailing space. Measured against the project's own 33-line real-word corpus, **a single trailing space breaks 33 of 33 lines** and collapsing double spaces to single breaks 5 of 33.

Separately, a widely used convention writes the tone letter immediately after the syllable it belongs to — `ma˦ ti˦˨` — and the converter cannot read that at all.

This plan replaces the input grammar with one that does not care where the tone letters sit, and adds a warning channel on stderr so that a line which is not converted, or is converted but suspicious, says so instead of passing silently.

## What changes

### One rule, not two paths

An earlier draft of this design detected which of the two formats a line used and dispatched to a separate engine for each. That is discarded: it is unnecessary, because a single rule covers both and several arrangements neither format anticipated.

Walk the string once. Every run of adjacent Chao tone letters is one **group** (so `˦˨` stays a single contour, and `˦ ˨` is two groups). Each group is either:

- **attached** — it immediately follows a tone-bearing unit in the same word, with no whitespace in between. It may reach back over a coda consonant, so `mat˦` attaches to the `a`. It binds to that unit.
- **free** — anything else: preceded by whitespace, or at the start of a word. It goes into a queue.

Free groups then fill the units that no attached group claimed, in document order.

The trailing-section format is simply the case where every group is free, so [the flexible-spacing change discussed before this plan](#relationship-to-the-flexible-spacing-change) is subsumed rather than being a separate step. Pre-posed tone letters (`˦ma`) and a leading rather than trailing tone section fall out of the same rule without a clause of their own.

Tone-bearing units are found exactly as today, by `_word_units()`, which needs no change: Chao tone letters are Unicode category `Sk`, not `Lm`, so the existing "anything else breaks a vowel run" branch already segments `ma˦i` into two units rather than one. The three placement rules (whole group on a one-cluster unit; a single level tone repeated across a diphthong; one letter per cluster) are also unchanged.

`_SPLIT_RE` is deleted. This is the one genuine widening: the converter no longer requires the tone-letters-at-the-end shape to engage, so **any** Chao tone letter anywhere in the input is now treated as a tone mark and consumed. Text carrying a tone letter as literal data would be eaten. [`chao-tone-letters/SPEC.md`](../../chao-tone-letters/SPEC.md) currently promises the opposite for the forward converter, and that promise has to be restated on this converter's side.

### Whitespace left behind

Removing the tone letters can strand the whitespace that separated them. A whitespace run is dropped when the removal leaves no surviving text on one side of it, and kept otherwise — so the space inside `ma˦ ti˦˨` survives and the space before a trailing tone section does not. Without this the trailing-section cases come out as `'má tî   '`.

### Exact fill for free groups, partial fill for attached

Attached marking may be partial: `ma˦ ti` converts to `má ti`, with the second syllable simply toneless, because each attached letter says which syllable it belongs to and an unmarked one is unambiguously untoned.

Free groups must fill the unmarked units **exactly**, or the line is returned unchanged. This was the user's explicit call, and the reason is that position is the only clue a detached letter carries, so a partial fill has to guess that the missing tones are the trailing ones. When the dropped letter was actually the first, every remaining tone shifts one syllable and the result looks entirely plausible:

| input | exact (chosen) | permissive (rejected) |
| --- | --- | --- |
| `bjo sadu  ˧˨  ˧ ˨` (complete) | `bjo᷆ sādù` | `bjo᷆ sādù` |
| `bjo sadu  ˧ ˨` (first letter dropped) | unchanged, warns | `bjō sàdu` — every tone on the wrong syllable |

Exact keeps the count check as the last remaining safety net on detached data. A genuinely partially-toned line in the detached style cannot be expressed, and the answer is to write those tones attached instead, which the same engine reads.

## Warnings

The warning channel is worth building once, so it covers the obvious cases rather than only the count mismatch that prompted it. This list is deliberately not exhaustive.

Lines that are **not converted**, returned unchanged, and warn:

| # | Condition | Message |
| --- | --- | --- |
| W1 | Free groups do not match the unmarked syllables, in either direction. Covers input with tone letters but no tone-bearing unit at all (`pst˦`, a bare `˥`). | `2 detached tone letter groups for 3 unmarked syllables` |
| W2 | A group has no tone diacritic equivalent, or does not fit any placement rule. Only 8 of the possible contours have an equivalent. | `no tone diacritic for ˨˩` |
| W3 | Two groups bind to the same syllable, e.g. `ma˦t˨`. | `two tone letter groups on one syllable` |

Lines that **are converted** but warn anyway:

| # | Condition | Why it matters |
| --- | --- | --- |
| W4 | The base text already carries a tone diacritic. | The strongest case in the set. `má˨` converts to `má̀` and `mā ti ˦  ˨` to `mā́ tì` — a doubly marked vowel, silently. It means the data is half-converted already. |
| W5 | The line mixes attached and detached tone letters. | A detached group can reach back past an already-marked syllable: `pa ta˧ ka˨ ˩` converts to `pȁ tā kà`, the `˩` landing on `pa`. Correct by the rule, surprising to read, and a sign of inconsistent data entry. |
| W6 | Some syllables are marked by attached letters and others are not (**provisional** — see [Decisions](#decisions)). | Attached data has no count check at all, so this is its only net against a dropped tone letter. But it also fires on genuinely toneless syllables. |

### Where the warnings live

`convert(input_string)` must stay a pure string-to-string function with no output of its own: it is used unchanged as an SIL FLEx Process, and a FlexTools module wrapping it must report through the `report` object and never `print`, per [AGENTS.md's FlexTools Module Conventions](../../AGENTS.md#flextools-module-conventions).

So the reasons come from a new `convert_with_warnings(input_string)` returning `(result, warnings)`, where `warnings` is a possibly empty list of plain strings. `convert()` becomes a one-line wrapper returning the first element. Only the CLI writes to stderr. A future FlexTools module can surface the identical strings through `report.Warning` without restating them.

CLI output, with results still on stdout and every line passed through whether or not it converted:

```
$ ... | chao2diacritics.py
bjo᷆ sādù
bjo sadu  ˧ ˨
pa tā kà
ka˨˩
cat

--- stderr ---
chao2diacritics: line 2: not converted: 2 detached tone letter groups for 3 unmarked syllables: 'bjo sadu  ˧ ˨'
chao2diacritics: line 4: not converted: no tone diacritic for ˨˩: 'ka˨˩'
chao2diacritics: line 6: not converted: 1 detached tone letter group for 0 unmarked syllables: 'ma˦ ˨'
```

Every line still reaches stdout, so a TSV keeps all its rows. Line numbers are the stdin line number, or the argument index when text is given as arguments.

## Prototype results (measured, not assumed)

A working prototype of the unified engine was run before this plan was written.

**Against the project's real-word corpus.** The 33 lines of `chao-tone-letters/tests/fixtures/diacritics2chao/inputs/` were converted to tone-letter form and fed to the prototype in four different arrangements. 29 of the 33 are convertible; the other 4 are toneless lines (`cat`, `ë`, a bare `˥`, `cat   dog`) that today's engine also leaves alone.

| Input arrangement | Matches today's output | Differs |
| --- | --- | --- |
| Trailing section, canonical double-space | 29 | 0 |
| Trailing section, single-spaced | 29 | 0 |
| Trailing section, with a trailing space | 29 | 0 |
| Fully attached (inline) | 29 | 0 |

**Against hand-built cases.** 18 arrangements, all correct through the one code path:

```
trailing       'ma ti ˦  ˦˨'          -> 'má tî'
trailing 1sp   'ma ti ˦ ˦˨'           -> 'má tî'
trailing +sp   'ma ti ˦  ˦˨ '         -> 'má tî'
inline         'ma˦ ti˦˨'             -> 'má tî'
inline nospc   'ma˦ti˦˨'              -> 'mátî'
pre-posed      '˦ma ˦˨ti'             -> 'má tî'
leading sect   '˦  ˦˨ ma ti'          -> 'má tî'
mixed          'ma˦ ti ˦˨'            -> 'má tî'
coda           'mat˦'                 -> 'mát'
diphthong      'mai˦'                 -> 'máí'
spec example   'nəjɛt ˨  ˨˧'          -> 'nə̀jɛ᷅t'
spec inline    'nə˨jɛ˨˧t'             -> 'nə̀jɛ᷅t'
no tones       'ma ti'                -> 'ma ti'
unmappable     'ka˨˩'                 -> 'ka˨˩'
orphan         'ma˦ ˨'                -> 'ma˦ ˨'
user TSV       'bjo sadu  ˧˨  ˧ ˨'    -> 'bjo᷆ sādù'
user TSV 1sp   'bjo sadu  ˧˨ ˧ ˨'     -> 'bjo᷆ sādù'
user TSV +sp   'bjo sadu  ˧˨  ˧ ˨ '   -> 'bjo᷆ sādù'
```

**Round trip.** Diacritics to attached tone letters and back was exact on 32 of 33 lines. The one difference, `kǎun` to `kau˨˦n` to `kàún`, is the diphthong ambiguity [already documented in `SPEC.md`'s Round-trip status](../../chao-tone-letters/SPEC.md), not something this change introduces.

## Attached output from the forward converter

`diacritics2chao.py` emits only the trailing-section format, so after this change the pair is asymmetric: the reader accepts four arrangements, the writer produces one. The round trip still works, since the reader handles what the writer emits.

The user's call (2026-08-28) is to close that gap, because the trailing-section format is exactly the fragile one. Its meaning lives in whitespace, which is why `awk` collapsing double spaces destroyed it and a stray trailing space broke 33 of 33 lines. In the attached form spacing carries no information at all, so it survives shell mangling, spreadsheet round-trips and copy-paste. If tone letters are being *stored* anywhere — a TSV, a SayMore field, a FLEx field — the attached form is the more robust thing to store, and nothing in the repository can currently produce it.

| diacritics in | today (trailing section) | attached mode |
| --- | --- | --- |
| `nə̀jɛ᷅t` | `nəjɛt ˨ ˨˧` | `nə˨jɛ˨˧t` |
| `bjo᷆ sādù` | `bjo sadu ˧˨  ˧ ˨` | `bjo˧˨ sa˧du˨` |
| `má tî` | `ma ti ˦  ˦˨` | `ma˦ ti˦˨` |

This is a **separate commit, landing after the reader**, so the reader change stays reviewable on its own. It is roughly 20 lines plus a `--attached` CLI flag, reusing the unit walker that already exists: instead of collecting each unit's tone letters into a trailing section, append them to the unit's last cluster in place.

It does not change what `convert()` returns by default. The trailing section stays the default output so that nothing downstream of the existing converter changes, including the module and the existing approved fixtures.

One limitation it does not fix: attached output cannot distinguish a genuinely toneless syllable from one whose tone has not been transcribed, since both are simply unmarked. The trailing format cannot either, so nothing is lost.

## Relationship to the flexible-spacing change

A narrower change was discussed and approved first: keep the trailing-section format, but split it on any run of whitespace rather than on runs of two or more, and match the groups against a flat list of syllables across the whole line, ignoring word boundaries. That was separately prototyped and measured — 33 of 33 identical on the corpus, 0 regressions, fixing the trailing-space and single-space cases.

It is **not** a separate commit. The unified rule in this plan produces the same results for the same inputs and covers strictly more, since an all-free line is exactly what that change described. Implementing both would mean writing the positional matcher twice.

## Changes to SPEC.md

[`chao-tone-letters/SPEC.md`](../../chao-tone-letters/SPEC.md)'s Tone Diacritics From Chao Tone Letters section is rewritten:

- Step 1 loses `_SPLIT_RE` and gains the attached/free grouping rule.
- Step 2 loses the two-or-more-spaces convention entirely.
- Steps 4 and 5 keep the three placement rules but restate the matching as attached-binds-locally, free-fills-in-order, with exact fill required for free groups.
- A new paragraph states that any Chao tone letter anywhere in the input is consumed as a tone mark, explicitly reversing, for this converter, the promise made at the end of the forward converter's step 2 that a tone letter already present in the input is ordinary text.
- A new subsection documents `convert_with_warnings()` and the six warning conditions.
- The Command line paragraph gains the stderr warning behaviour and the fact that the exit status stays 0.
- Round-trip status notes that the reverse direction now also reads attached tone letters, and, once the follow-up commit lands, that `diacritics2chao.py` can emit them behind `--attached`.

[`README.md`](../../README.md)'s `chao2diacritics.py` section is updated in the same commit, per [AGENTS.md's Documentation section](../../AGENTS.md#documentation): the accepted input arrangements, the stderr warnings, and a worked example of each arrangement reaching the same output.

## Testing

TDD, red before green, per [AGENTS.md's Testing Approach](../../AGENTS.md#testing-approach).

Unit tests in `chao-tone-letters/tests/test_chao2diacritics.py`, each pinning one rule with the clearest example:

- the four arrangements — trailing, attached, pre-posed, mixed — reaching the same output
- attached reaching back over a coda (`mat˦`)
- attached partial marking leaving a syllable toneless (`ma˦ ti`)
- free groups requiring an exact fill, including the shifted-tone case from the table above
- orphaned whitespace dropped on one side but kept on the other
- each of the six warning conditions, asserted on `convert_with_warnings()`'s second element
- the existing double-space tests kept as-is, since they must still pass unchanged

Approval fixtures under `chao-tone-letters/tests/fixtures/chao2diacritics/`, following [the adding-an-approval-fixture skill](../../.claude/skills/adding-an-approval-fixture/SKILL.md), one input file per arrangement. Per the same section of AGENTS.md, no unit test should restate a pair a fixture already asserts.

The words in these fixtures are the attested ones already in the corpus, but the *arrangement* under test is constructed — no real Plateau data is written with pre-posed tone letters, and none mixes the two styles in one line. The thing being tested is therefore synthesised, so every new fixture takes the `_simulated` suffix the repository already uses for `diphthongs_simulated.txt`, per [AGENTS.md's rule that a constructed fixture must say so in its filename](../../AGENTS.md#testing-approach):

| Fixture stem | Covers |
| --- | --- |
| `attached_simulated` | real corpus words with the tone letters attached to each syllable |
| `preposed_simulated` | tone letters written before the syllable, and a leading rather than trailing section |
| `mixed_attachment_simulated` | attached and detached tone letters in one line, including a free group reaching back |
| `trailing_spacing_variants_simulated` | the trailing section single-spaced, wide-spaced, and with a trailing space |
| `warnings_simulated` | one line per warning condition W1 to W6 |

The existing six fixture pairs are left exactly as they are: they must still pass unchanged, which is the strongest evidence that the rewrite is a widening rather than a change.

A CLI test driving the subprocess with an explicit `encoding="utf-8"`, asserting that stdout carries every line and the expected warnings go to stderr.

The existing drift-guard tests that check this converter's copies of the diacritic table, vowel set and syllabic marks against `diacritics2chao.py` stay as they are.

## Decisions

Resolved with the user, 2026-08-28:

- Free groups must fill unmarked syllables exactly; a partial fill is rejected rather than guessed at.
- Attached groups may mark only some syllables, leaving the rest toneless.
- A warning goes to stderr when a line is not converted, and the channel is reused for other obviously suspicious lines rather than built only for the count mismatch.
- The two formats are read by one engine with no format detection.
- `diacritics2chao.py` does gain an attached-output mode behind `--attached`, as a separate commit after the reader — see [Attached output from the forward converter](#attached-output-from-the-forward-converter). The trailing section stays the default output.
- Constructed fixtures carry the `_simulated` filename suffix.

Defaults taken, to be corrected if wrong:

- Exit status stays 0 even when lines warn, so existing pipelines do not break. Warnings are diagnostics, not failures.
- W6, the warning for partially attached-marked lines, is provisional. It is the only net attached data has against a dropped tone letter, but it will also fire on genuinely toneless syllables. If it proves noisy in real use it is the one to drop.


## Changes after approval

Recorded rather than edited into the body above, so the record of what was approved stays honest.

- `preposed_simulated.txt` is hand-written rather than derived from the real corpus. The mechanical transform inserted each tone letter before its *vowel* rather than before its syllable, giving forms like `n˨əj˨˧ɛt` that exercise the rule but read as nothing any human would write. The other four fixtures are derived from the corpus as planned.
- `test_chao2diacritics_cli.py`'s blanket `assert result.stderr == ""` had to go: warnings now legitimately appear there. It is replaced by a check that every stderr line matches the warning format, so a stray traceback or debugging print still fails, plus three focused CLI tests covering the warning text, the pass-through of every line to stdout, and the zero exit status. The stdout approval artifacts are untouched.
- The attached output is exposed as `tone_diacritics_to_attached()` as well as `convert(..., attached=True)`, mirroring the existing `tone_diacritics_to_chao_letters()` next to `convert()`.
- A pre-existing unrelated failure, `zhire/tests/test_phonetic2phonemic_cli.py::test_stdin_lines_convert_to_approved_output[input_path2-approved_path2]`, was present before this work and is left alone.
