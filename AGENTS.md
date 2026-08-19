# AGENTS.md

Guidance for human and AI contributors working in this repository.

## Scope

- This file applies to the whole repository.

## What This Repository Is

- **The converter is the product; a FlexTools module is one of several ways to run it.** Each converter in `converters/` is a plain Python 3 file with a `convert()` function taking and returning a string, with no FieldWorks dependency, so the same conversion runs from the command line, as a FLEx Process, and from FlexTools.
- The repository root doubles as a **FlexTools module folder**: copy the whole checkout into the FlexTools `Modules` folder and the module files at the root are picked up, with `converters/` alongside them. See [FlexTools Module Conventions](#flextools-module-conventions) for why that works.
- Anything that has to walk the FLEx model rather than transform a string does not belong here. It belongs in [flextools_modules](https://github.com/speechchemistry/flextools_modules), whose value is the traversal, not a string function.

## Agent Agnosticism

- This repository targets no particular agent or vendor. `AGENTS.md` is the single source of truth for contributor guidance: add every rule here, not to a tool-specific file.
- A tool-specific entry point is a pointer, never a second copy. `CLAUDE.md` exists only because Claude Code reads `CLAUDE.md` and not `AGENTS.md`; it holds one import of this file and no guidance of its own. If another tool needs its own entry point, add the same kind of one-line pointer.
- Where a procedure has to live in a tool-specific location (`.claude/skills/`), keep it a procedure — occasional, task-triggered steps. Anything always-applicable stays here, so an agent or person reading only this file still gets every rule that matters.

## Core Principles

- Prefer common, well-maintained libraries and packages over custom ad hoc logic.
- Keep changes focused and minimal for the requested task.
- Do not modify unrelated files.

## Specification

- `SPEC.md` is the source of truth for what each converter and module does and guarantees: the transform rules, the FLEx fields a module reads and writes, and its prerequisites.
- Whenever a change alters or clarifies a rule `SPEC.md` covers, update `SPEC.md` in the same change — do not let it drift out of sync with the code.
- If code and `SPEC.md` disagree, that is a bug: fix whichever is wrong, do not silently favour one.
- Do not speculatively extend `SPEC.md` to cover converters or behaviours that aren't implemented yet; add to it incrementally as each is actually built (see [SPEC.md's Not Yet Specified section](SPEC.md#not-yet-specified)).
- **Split of concerns:** `AGENTS.md` documents how to work in this repo (process, conventions, workflow). `SPEC.md` documents what the converters and modules do and guarantee. Repo-wide engineering conventions that happen to describe behaviour (e.g. reporting through the `report` object, honouring `modifyAllowed`) stay in `AGENTS.md` since they apply uniformly; `SPEC.md` is reserved for the per-converter and per-module contract specifically.

## Skills

Task-specific procedures live under `.claude/skills/<name>/SKILL.md` rather than in this file, so `AGENTS.md` stays a set of always-applicable rules. Add a new skill when a procedure is followed occasionally rather than always.

The directory name is Claude Code's (it discovers skills only there), but the files are not tool-specific and every agent can use them:

- Write each one to the [Agent Skills](https://agentskills.io) open format: YAML frontmatter using only the six standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`), then plain Markdown instructions. Tool-specific frontmatter fields and body features are rejected or ignored outside the tool that added them.
- List every skill below with a link. Other agents don't scan `.claude/skills/`, and many file searches skip dot-directories, so this list is how anything other than Claude Code finds them.
- Keep `.claude/skills/` committed to git. If a `.gitignore` is ever added to cover it, do not ignore `.claude/` wholesale, or the procedures become invisible to everyone else.
- Any agent or person can be pointed straight at a `SKILL.md` and told to follow it; nothing in the format requires a particular tool.

Skills in this repository:

- [`adding-an-approval-fixture`](.claude/skills/adding-an-approval-fixture/SKILL.md) — add a new approval-test fixture (or approve a changed one) for a converter's CLI output.

## Plans

- A plan in `plans/` is a historical record of what was approved, never a source of truth for how the repo works. Where a plan disagrees with the current code, `SPEC.md`, or `AGENTS.md`, those win — read them instead, and do not "fix" the plan to match.
- Keep re-syncing a plan while it is still being planned and implemented (see [Working Style](#working-style)). Once implementation is complete the plan freezes: don't rewrite it, renumber it, or restate later decisions inside it.
- Give each plan a status line under its title recording when it was approved and whether it has been implemented, so a reader knows immediately whether it describes the present or the past.
- When decisions changed after approval, append a short list of those changes to the end of the plan rather than editing the body. Appending keeps the record honest; editing destroys it.

## Markdown Conventions

- **Don't number Markdown headings** (`## 2. Pitch field`, `## 1. Decide the match rule`) in any file in this repo — `SPEC.md`, skills (`SKILL.md`), and other reference docs — unless there's a specific reason a given file needs it. A numbered heading shifts whenever a section is inserted or reordered above it, silently breaking every cross-reference to it.
- **Reference a heading elsewhere by Markdown anchor link and its actual name, not a number**: `[SPEC.md's Not Yet Specified section](SPEC.md#not-yet-specified)`, not `SPEC.md §3`. An anchor link survives reordering; only a heading rename breaks it, and that's a one-time, greppable fix (`grep -rn '#anchor-slug'`) rather than a renumbering cascade.

## Working Style

- Before changing behaviour, check existing patterns in nearby files and follow them.
- When behaviour changes are non-trivial, ask for confirmation before implementing.
- If a requirement is ambiguous and could alter behaviour, ask a clarifying yes/no question first.
- Ask clarifying questions in plain chat text, not via a multiple-choice/quick-answer UI widget.
- Save non-trivial implementation plans to `plans/<descriptive-name>.md` in the repo (not only wherever the tool's own ephemeral plan-mode file lives), so they're preserved and reviewable via git history. This is not a one-time save: whenever the plan is revised (e.g. new information surfaces mid-planning), re-sync `plans/<name>.md` with the latest approved version before or immediately after implementation starts.

## Libraries And Dependencies

- Reuse existing dependencies and idioms already present in the repo when possible.
- Add a new package only when it clearly improves reliability, readability, or maintainability.
- Prefer widely adopted packages over hand-rolled implementations.
- This repository is not pip-installable and has no `pyproject.toml`; it is distributed by copying the checkout. Keep a converter's dependencies few and name them in `README.md`.

## Converter Conventions

A converter is the reusable part, so it carries the constraints:

- One converter per file in `converters/`, named after what it converts, opening with a header comment block: title, one-line purpose, author, month and year, and `Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)`.
- **Never import `flextoolslib` or anything from FieldWorks in `converters/`.** Those install only on Windows alongside FieldWorks; the whole point of the folder is that it runs anywhere and can be tested anywhere.
- The entry point must be a module-level function called `convert(input_string)` taking and returning a plain string, so it can be used as an SIL FLEx Process unchanged.
- Give each converter a command line interface under `if __name__ == '__main__':`, following [CLI Script Conventions](#cli-script-conventions), so the conversion is usable outside FlexTools without any FLEx installation.
- Add brief comments for non-obvious logic so future readers can follow intent.

## FlexTools Module Conventions

Module files are the thin FlexTools wrapper around a converter; they are loaded and run by [FlexTools](https://github.com/cdfarrow/flextools) against a live FLEx project, not from the command line. The conventions below replace the usual CLI stdout/stderr rules.

- Each module is a single self-contained `.py` file **at the repository root**, named after what it does, opening with a header comment block: title, one-line purpose, author, month and year, and `Platforms: Python .NET and IronPython`.
- Keep the module thin. Domain logic belongs in `converters/`; the module's job is reading the field, calling `convert()`, and writing the result. `__Template_converter_module.py` is the starting point — copy it and change the marked places. It starts read-only (`FTM_ModifiesDB: False`, no custom field required): writing the result back is a commented-out block you uncomment deliberately once the read-only report looks right.
- The FlexTools scanner lists `*.py` at the **top level of each module folder only** and never recurses, so `converters/`, `tests/` and `plans/` are invisible to it; non-`.py` files are ignored; and files whose name starts with `__` are skipped *before* import, which is why the template is safe to ship. A copy of the template must therefore not keep the `__` prefix.
- Import the converter by adding `converters/` to `sys.path` from `__file__`, as the template does: FlexTools imports a module by path, which does not put the module's own folder on `sys.path`.
- Keep the standard shape, in this order: `# -*- coding: utf-8 -*-`, `from flextoolslib import *`, a `docs` dict (`FTM_Name`, `FTM_Version`, `FTM_ModifiesDB`, `FTM_Synopsis`, `FTM_Help`, `FTM_Description`), `MainFunction(project, report, modifyAllowed)`, and finally `FlexToolsModule = FlexToolsModuleClass(runFunction = MainFunction, docs = docs)`. FlexTools looks up that last name exactly, so it must be spelled as written.
- Bump `FTM_Version` in `docs` whenever a module's behaviour changes.
- Honour `modifyAllowed`: when it is false, do the same reading and reporting but write nothing, so a preview run is a genuine dry run (see the `[DRY RUN]` prefix in the template).
- Report through the `report` object (`report.Info`, `report.Warning`, `report.Error`), never `print` — this is the FlexTools counterpart of separating result output from diagnostics. Use `report.ProgressStart` and `report.ProgressUpdate` for passes over the whole lexicon.
- Fail gracefully on missing prerequisites (e.g. a required custom field): `report.Error` and degrade to read-only rather than raising.
- Reach FLEx data through the `flextoolslib` project helpers (`LexiconAllEntries`, `LexiconNumberOfEntries`, `LexiconGetLexemeForm`, `LexiconGetEntryCustomFieldNamed`, `LexiconSetFieldText`, …) in preference to walking raw LCM attributes. Where the model may not hold an object, guard with `getattr(obj, "Name", None)` and skip rather than assume.
- **Write with `LexiconSetFieldText` and pass the writing system explicitly.** `LexiconAddTagToField` reads the field back with no writing system, which raises `AttributeError` on a multi-string custom field; and `LexiconSetFieldText` otherwise defaults to the default *analysis* writing system, which stores text a vernacular field never displays — indistinguishable from doing nothing. Report which writing system was used.

## Data Safety

- These modules modify a live FLEx project, and FLEx has no undo across a FlexTools run. Keep every write behind `modifyAllowed`.
- Prefer narrowly scoped edits over broad rewrites, and don't let a converter's empty result clear a field a user filled in by hand.
- Keep the README's standing instruction that users back up their FLEx project before running these modules; don't remove or soften it.

## CLI Script Conventions

- For scripts that emit machine-readable output:
  - Write result content only to stdout.
  - Write progress, diagnostics, and errors to stderr.
- Read and write UTF-8 explicitly rather than leaving it to the console code page, which is not UTF-8 by default on Windows.

## Testing Approach

- Use `pytest`, with tests under `tests/`, run as `python -m pytest` from the repo root.
- Test each converter's `convert()` directly — it needs no FLEx project, so those tests run on any platform. `tests/conftest.py` puts `converters/` on `sys.path` so `from chao_tones import convert` works.
- `flextoolslib` only installs on Windows alongside FieldWorks, so importing a module file fails elsewhere at its top-level `from flextoolslib import *`. `tests/conftest.py` stubs `flextoolslib` in `sys.modules` and loads module files by path, so `MainFunction` can be driven with fake `project` and `report` objects on any platform.
- Those fakes cover the module's decisions, not FLEx itself, so still verify a changed module by running it in FlexTools with modification disabled before enabling it.
- Prefer small parametrized assertions while a converter's output is short strings. Switch to approval testing when output becomes large or awkward to assert inline: the checked-in artifact is the approved one, a mismatch produces a received artifact for review, and changes are never auto-accepted without explicit confirmation.
- **Approval testing convention** (see `tests/test_chao_tones_cli.py` and `tests/fixtures/chao_tones/` for the worked example): input fixtures live in `tests/fixtures/<converter>/inputs/*.txt`, approved outputs in `tests/fixtures/<converter>/approved/<stem>.approved.txt`, and a mismatch (or a fixture with no approved file yet) is written to `tests/fixtures/<converter>/received/<stem>.received.txt`. Adding a fixture and approving a changed one are the same loop: drop or edit a `.txt` in `inputs/`, run `python -m pytest`, read the failure's received file, and — only once it looks right — promote it with the `cp` command the failure prints. Never write into `approved/` any other way.
- For a converter whose output is plain text, compare the approved file and the actual output **exactly**: no scrubbing, no Unicode normalisation, and no comment or label lines inside a fixture (the filename is the label). Normalising would hide a real regression whenever normalisation is itself part of what the converter guarantees, as NFC/NFD handling is for `chao_tones.py`.
- A few traps that make an approval suite look green while testing nothing, worth checking for in review: a fixture with no approved counterpart must fail loudly rather than being skipped or silently passing; `*.received.*` must stay gitignored so a received file can never be committed as though it were approved; drive a CLI subprocess with an explicit `encoding="utf-8"` rather than `text=True`, since the locale code page can mangle non-ASCII output; and an editor can silently strip trailing whitespace or re-normalise Unicode in a fixture file, corrupting an exact comparison — keep whitespace and normalisation-sensitive cases away from line ends.
- Keep approved artifacts human-reviewable and deterministic so diffs are meaningful.
- Follow TDD for behaviour changes: add or extend the test and confirm it fails first (red), write the minimum implementation to make it pass (green), then refactor with the tests as a safety net. For an approval test this means adding the fixture first and confirming the received output is wrong before implementing, then promoting the received file once it's right — the same reason a first approval must be read, never accepted on trust.

## Documentation

- `README.md` is the user-facing description of each converter and module. A new converter or module, or a behaviour change to an existing one, updates its README section in the same change.
- When a converter or module incorporates third-party code, name the author and licence in the source header, and record the resulting combined licence in the README's Attributions line.
