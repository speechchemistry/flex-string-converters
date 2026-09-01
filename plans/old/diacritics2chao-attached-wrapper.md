# A thin wrapper converter so a raw FLEx Process can select attached output

Status: approved and implemented 2026-09-01. Real FLEx Process verification (see Verification below) is the user's own follow-up and remains outstanding.

## Why

`diacritics2chao.py`'s `Convert(input_string, attached=False)` has two output shapes, but a raw SIL FLEx Process (Bulk Edit → ... → Process, pointed directly at a converter file, as opposed to a FlexTools module, which is glue code we write ourselves) always calls a bare `Convert(input_string)` with no keyword arguments — confirmed against `AGENTS.md:107`'s contract. There is currently no way for a FLEx user to get attached output that way; they always get the trailing-section default.

Two approaches were weighed with the user: a module-level constant a user hand-edits (mirrors the existing `PITCH_WS` pattern in `Extract_Chao_tone_letters_from_tone_diacritics.py`, zero new import risk, but requires editing and re-saving the file each time the mode is switched), or a separate wrapper file the user instead points FLEx at (no hand-editing, but the first time any converter in this repo would import a sibling converter file — genuinely untested against a real FLEx Process, though the identical `sys.path`-from-`__file__` technique is already proven for FlexTools' own module-loading, per `AGENTS.md`'s FlexTools Module Conventions).

**User's call (2026-09-01): try the wrapper file.** The risk is bounded (worst case, it doesn't resolve the import and the fallback constant approach is simple to add later) and the reward is better — no hand-editing needed, and no risk of the FlexTools module accidentally inheriting a hand-edited default. This needs a real FLEx Process smoke test before being trusted; nothing in this repo's sandbox can verify that.

## What gets added

`chao-tone-letters/converters/diacritics2chao_attached.py` — a thin wrapper, following the existing header-comment and CLI conventions of every other converter in this project. Its `Convert(input_string)` forwards to `diacritics2chao.Convert(input_string, attached=True)`, importing that sibling via `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` before the import, the same technique `AGENTS.md:118` documents for a FlexTools module reaching its project's `converters/`.

It gets its own minimal CLI under `if __name__ == '__main__':` (so it's independently usable and testable, and because `AGENTS.md`'s Converter Conventions require one), but **no `--attached` flag** — the whole point of this file is that the choice is already made. It reuses the same fail-fast-on-a-terminal-with-no-input behaviour every converter's CLI now has (`AGENTS.md`'s CLI Script Conventions).

## What does not get added

No new transform logic, no approval-fixture corpus, and no full copy of `diacritics2chao.py`'s attached-output test suite. `AGENTS.md`'s Testing Approach explicitly warns against a second test re-asserting a pair an existing test already checks — this file contains zero independent logic, so its own tests only need to pin the delegation itself, not re-verify the attached-output rules `test_diacritics2chao.py` already covers.

## Tests

TDD, red before green:

- `chao-tone-letters/tests/test_diacritics2chao_attached.py` — a handful of `Convert(x) == diacritics2chao.Convert(x, attached=True)` assertions reusing existing representative examples from `test_diacritics2chao.py` (the spec example, a diphthong, a toneless word), plus one assertion that this file's `Convert` really is a distinct object forwarding to the real one (not an accidental re-implementation).
- `chao-tone-letters/tests/test_diacritics2chao_attached_cli.py` — a small CLI smoke test (one or two representative conversions via subprocess) plus the same real-pseudo-terminal "no arguments and no piped input" test every other converter's CLI test file has, copied from the established pattern (`chao-tone-letters/tests/test_diacritics2chao_cli.py`'s `test_no_arguments_and_no_piped_input_prints_usage_instead_of_hanging`). No approval-fixture pairs, for the reason above.

## Docs

- `chao-tone-letters/SPEC.md`'s existing "Attached output" paragraph gains a short addendum naming the wrapper file, stating it has no transform rules of its own and forwards to `Convert(input_string, attached=True)`, and that it exists specifically so a raw FLEx Process — which cannot pass keyword arguments — can select attached output by file choice instead. No new `##` section, since there is no new behaviour to specify beyond the forwarding itself.
- `README.md`'s `diacritics2chao.py` section gains a short paragraph pointing at the new file for FLEx Process use, folded into the existing section rather than a new one.
- The wrapper's own header comment carries the "this needs a real FLEx Process smoke test before being trusted" caveat, since that's a testing-status note about *this file specifically*, not a durable spec claim that belongs in `SPEC.md`.

## Verification

- `python -m pytest` from the repo root, confirming the new tests pass and nothing else regresses.
- Manual CLI checks: piped input, argument input, and the real-pseudo-terminal no-input case, mirroring what was done for the sibling converters' isatty fix.
- Real FLEx verification is out of scope for this sandbox and is the user's own follow-up step before relying on this in production.
