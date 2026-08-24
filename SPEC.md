# SPEC.md

An index of the per-project specs. Each project in this repository groups a related set of converters (and any FlexTools module wrapping one) that share a topic or a language community; each project's own `SPEC.md` is the source of truth for what its converters and modules do and guarantee — the transform rules, the FLEx fields a module reads and writes, and its prerequisites. See [AGENTS.md's Specification section](AGENTS.md#specification) for how a project's `SPEC.md` and `AGENTS.md` divide up.

This file records only projects that exist today. Add a new entry once a project's converter is actually built, rather than speculatively.

## Projects

- [`chao-tone-letters/SPEC.md`](chao-tone-letters/SPEC.md) — converting between tone diacritics and Chao tone letters, and extracting Chao tone letters into a FLEx `Pitch` field. Not specific to any one language.
- [`zhire/SPEC.md`](zhire/SPEC.md) — converting a Zhire `[zhi]` phonemic transcription to its orthographic spelling.
