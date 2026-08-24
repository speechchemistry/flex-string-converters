# Split the repository into per-project folders

Status: approved and implemented 2026-08-24.

## Why

A new converter was being planned for the Zhire `[zhi]` language community — a phonemic-to-orthographic
conversion specific to that community, unlike the existing Chao-tone-letters converters, which aren't
tied to any one language. A single repo-root `SPEC.md`, `converters/`, and flat set of FlexTools
module files at the root no longer cleanly represented that: two unrelated topics were sharing one
namespace, and the natural next step (an eventual third project) would only make that worse.

## Decision

Group converters into **project folders at the repository root**, one per topic or language
community. Each project folder is self-contained:

```
<project>/
  SPEC.md
  converters/
    <what_it_converts>.py
  tests/
    conftest.py
    test_<what_it_converts>.py
    test_<what_it_converts>_cli.py       # once approval-tested
    fixtures/<what_it_converts>/{inputs,approved,received}/
  <FlexTools module file(s)>.py          # only if this project has one
```

The repository root keeps: `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, `__Template_converter_module.py`
(not project-specific), `plans/`, a root `SPEC.md` that is now just an index of project folders, and a
root `tests/` holding only the shared cross-project approval-testing harness (`tests/approval.py`) —
no test files of its own.

Three explicit choices made along the way:

- **Flat at the repository root**, not nested under a `projects/` parent — project folders sit
  directly alongside `AGENTS.md`, `README.md`, etc.
- **Tests move into each project folder too** (not just `SPEC.md` and `converters/`), so a project is
  fully self-contained apart from the one shared piece of test infrastructure (`tests/approval.py`)
  worth keeping DRY across projects.
- **FlexTools's install model changes**: a user now copies the *specific project folder* they want
  into their FlexTools `Modules` folder, not the whole repository checkout. This was accepted because
  FlexTools is the least likely use case for this repository, and the FlexTools scanner's "top level
  of the folder only, never recurses" behaviour makes it impossible to nest module files inside project
  folders while still supporting the old "copy the whole repo" install story.

Two new skills were added to make the recurring procedures repeatable:

- [`adding-a-project`](../../.claude/skills/adding-a-project/SKILL.md) — scaffold a new project folder.
- [`adding-a-flextools-module`](../../.claude/skills/adding-a-flextools-module/SKILL.md) — wrap a
  converter in an existing project with a FlexTools module, from `__Template_converter_module.py`.

## What moved

The existing `chao-tone-letters` work — `converters/diacritics2chao.py`, `converters/chao2diacritics.py`,
`Extract_Chao_tone_letters_from_tone_diacritics.py`, `SPEC.md`, and all of their tests and fixtures —
became the first project folder, `chao-tone-letters/`, via `git mv` (history preserved). The shared
approval-testing harness `tests/approval.py` was generalized to take the calling project's own `tests/`
directory as an explicit argument, rather than assuming one repo-wide `tests/fixtures/` location.

`AGENTS.md` and `README.md` were updated throughout to describe the per-project structure in place of
the old single-`converters/`, single-root-`SPEC.md` model.

## What did not move (yet)

The Zhire phonemic-to-orthography converter that motivated this split was not created in this change —
its actual conversion rules are linguistic domain knowledge that still needs to be supplied. Suggested
naming, for whenever that work starts: a project folder named `zhire` (so any future Zhire-specific
converter can share it), with this first converter as `zhire/converters/phonemic2orthography.py`.
