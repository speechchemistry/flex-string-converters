# AGENTS.md

Guidance for human and AI contributors working in this repository.

## Scope

- This file applies to the whole repository.

## What This Repository Is

- **The converter is the product; a FlexTools module is one of several ways to run it.** Each converter is a plain Python 3 file with a `convert()` function taking and returning a string, with no FieldWorks dependency, so the same conversion runs from the command line, as a FLEx Process, and from FlexTools.
- **The repository groups converters into project folders at its root**, one per topic or language community — e.g. `chao-tone-letters/`. A project folder is self-contained: its own `SPEC.md`, its own `converters/` subdirectory, its own `tests/`, and (when one exists) the FlexTools module file(s) that wrap its converters. See [the root SPEC.md](SPEC.md) for the current list of projects.
- **A project folder doubles as a FlexTools module folder**: copy that project's folder alone into the FlexTools `Modules` folder and the module files at its top level are picked up, with its `converters/` alongside them. See [FlexTools Module Conventions](#flextools-module-conventions) for why that works, and don't copy the whole repository checkout in — the scanner would find nothing, since module files no longer sit at the repository root.
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

- The root `SPEC.md` is just an index: a short link list of the project folders that exist today. Each project's own `<project>/SPEC.md` is the source of truth for what its converters and modules do and guarantee: the transform rules, the FLEx fields a module reads and writes, and its prerequisites.
- Whenever a change alters or clarifies a rule a project's `SPEC.md` covers, update that `SPEC.md` in the same change — do not let it drift out of sync with the code.
- If code and a project's `SPEC.md` disagree, that is a bug: fix whichever is wrong, do not silently favour one.
- Do not speculatively extend a project's `SPEC.md` to cover converters or behaviours that aren't implemented yet; add to it incrementally as each is actually built (see e.g. [`chao-tone-letters/SPEC.md`'s Not Yet Specified section](chao-tone-letters/SPEC.md#not-yet-specified)). The same restraint applies to the root `SPEC.md`'s project list: add a project's entry once its converter actually exists, not before.
- **Split of concerns:** `AGENTS.md` documents how to work in this repo (process, conventions, workflow) and applies across every project. A project's `SPEC.md` documents what that project's converters and modules do and guarantee. Repo-wide engineering conventions that happen to describe behaviour (e.g. reporting through the `report` object, honouring `modifyAllowed`) stay in `AGENTS.md` since they apply uniformly; a project's `SPEC.md` is reserved for that project's own contract specifically.

## Skills

Task-specific procedures live under `.claude/skills/<name>/SKILL.md` rather than in this file, so `AGENTS.md` stays a set of always-applicable rules. Add a new skill when a procedure is followed occasionally rather than always.

The directory name is Claude Code's (it discovers skills only there), but the files are not tool-specific and every agent can use them:

- Write each one to the [Agent Skills](https://agentskills.io) open format: YAML frontmatter using only the six standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`), then plain Markdown instructions. Tool-specific frontmatter fields and body features are rejected or ignored outside the tool that added them.
- List every skill below with a link. Other agents don't scan `.claude/skills/`, and many file searches skip dot-directories, so this list is how anything other than Claude Code finds them.
- Keep `.claude/skills/` committed to git. If a `.gitignore` is ever added to cover it, do not ignore `.claude/` wholesale, or the procedures become invisible to everyone else.
- Any agent or person can be pointed straight at a `SKILL.md` and told to follow it; nothing in the format requires a particular tool.

Skills in this repository:

- [`adding-an-approval-fixture`](.claude/skills/adding-an-approval-fixture/SKILL.md) — add a new approval-test fixture (or approve a changed one) for a converter's CLI output.
- [`adding-a-project`](.claude/skills/adding-a-project/SKILL.md) — scaffold a new project folder (`SPEC.md`, `converters/`, `tests/`) for a new converter or topic.
- [`adding-a-flextools-module`](.claude/skills/adding-a-flextools-module/SKILL.md) — wrap an existing converter in a project with a FlexTools module, starting from `__Template_converter_module.py`.

## Plans

- A plan in `plans/` is a historical record of what was approved, never a source of truth for how the repo works. Where a plan disagrees with the current code, `SPEC.md`, or `AGENTS.md`, those win — read them instead, and do not "fix" the plan to match.
- Keep re-syncing a plan while it is still being planned and implemented (see [Working Style](#working-style)). Once implementation is complete the plan freezes: don't rewrite it, renumber it, or restate later decisions inside it.
- Give each plan a status line under its title recording when it was approved and whether it has been implemented, so a reader knows immediately whether it describes the present or the past.
- When decisions changed after approval, append a short list of those changes to the end of the plan rather than editing the body. Appending keeps the record honest; editing destroys it.
- **Move a plan to `plans/old/` once it is implemented**, so the top level of `plans/` shows only what is still in flight and nobody has to read status lines to tell the two apart. Move it with `git mv` so the rename stays visible in history. The move is the moment the plan freezes, so do it in the same change that finishes the implementation — an implemented plan left at the top level is the thing this rule exists to prevent, and `plans/` containing nothing but `old/` is the correct, honest state when no plan is in flight.
- Moving a plan deepens it by one directory, so **fix its relative links in the same commit**: an up-one-level link target becomes up-two-levels. Also update anything pointing at the plan (a project's `SPEC.md`, a source-file comment). Repairing a link path is mechanical upkeep, not a rewrite, so it is not covered by the freeze rule above — but a link whose *target* has since been renamed or moved is part of the historical record and stays as written, per the "do not 'fix' the plan to match" rule.

## Markdown Conventions

- **Don't number Markdown headings** (`## 2. Pitch field`, `## 1. Decide the match rule`) in any file in this repo — `SPEC.md`, skills (`SKILL.md`), and other reference docs — unless there's a specific reason a given file needs it. A numbered heading shifts whenever a section is inserted or reordered above it, silently breaking every cross-reference to it.
- **Reference a heading elsewhere by Markdown anchor link and its actual name, not a number**: `[chao-tone-letters/SPEC.md's Not Yet Specified section](chao-tone-letters/SPEC.md#not-yet-specified)`, not `SPEC.md §3`. An anchor link survives reordering; only a heading rename breaks it, and that's a one-time, greppable fix (`grep -rn '#anchor-slug'`) rather than a renumbering cascade.
- **Don't hard-wrap prose.** Write one line per paragraph, list item, or table row, and let the editor soft-wrap it — as `AGENTS.md`, `README.md`, `chao-tone-letters/SPEC.md` and the skills already do. Markdown joins consecutive lines into one paragraph anyway, so a manual line break buys nothing and costs a readable diff: editing one word reflows the rest of the paragraph, so the diff shows several changed lines instead of one and `git blame` attributes untouched sentences to the wrong commit. Fixed-width breaks also fight every different window width they are read at.
- Existing hard-wrapped files are fine to reflow as a deliberate change, **except the frozen plans in `plans/old/`** — reflowing those would rewrite the whole file for no benefit and bury their real history, the same reasoning that keeps a moved plan's stale link targets as written (see [Plans](#plans)).

## Working Style

- Before changing behaviour, check existing patterns in nearby files and follow them.
- When behaviour changes are non-trivial, ask for confirmation before implementing.
- If a requirement is ambiguous and could alter behaviour, ask a clarifying yes/no question first.
- Ask clarifying questions in plain chat text, not via a multiple-choice/quick-answer UI widget.
- Save non-trivial implementation plans to `plans/<descriptive-name>.md` in the repo (not only wherever the tool's own ephemeral plan-mode file lives), so they're preserved and reviewable via git history. This is not a one-time save: whenever the plan is revised (e.g. new information surfaces mid-planning), re-sync `plans/<name>.md` with the latest approved version before or immediately after implementation starts. A plan stays at the top level of `plans/` only while it is in flight; once implemented it moves to `plans/old/` — see [Plans](#plans).

## Libraries And Dependencies

- Reuse existing dependencies and idioms already present in the repo when possible.
- Add a new package only when it clearly improves reliability, readability, or maintainability.
- Prefer widely adopted packages over hand-rolled implementations.
- This repository is not pip-installable and has no `pyproject.toml`; it is distributed by copying the checkout. Keep a converter's dependencies few and name them in `README.md`.

## Converter Conventions

A converter is the reusable part, so it carries the constraints:

- One converter per file in its project's `converters/` directory (e.g. `chao-tone-letters/converters/`), named after what it converts, opening with a header comment block: title, one-line purpose, author, month and year, and `Platforms: any Python 3 (this file has no flextoolslib or FLEx dependency)`.
- **Never import `flextoolslib` or anything from FieldWorks in a project's `converters/`.** Those install only on Windows alongside FieldWorks; the whole point of the folder is that it runs anywhere and can be tested anywhere.
- The entry point must be a module-level function called `convert(input_string)` taking and returning a plain string, so it can be used as an SIL FLEx Process unchanged.
- Give each converter a command line interface under `if __name__ == '__main__':`, following [CLI Script Conventions](#cli-script-conventions), so the conversion is usable outside FlexTools without any FLEx installation.
- Add brief comments for non-obvious logic so future readers can follow intent.

## FlexTools Module Conventions

Module files are the thin FlexTools wrapper around a converter; they are loaded and run by [FlexTools](https://github.com/cdfarrow/flextools) against a live FLEx project, not from the command line. The conventions below replace the usual CLI stdout/stderr rules.

- Each module is a single self-contained `.py` file **at the top level of its project folder** (e.g. `chao-tone-letters/Extract_Chao_tone_letters_from_tone_diacritics.py`), named after what it does, opening with a header comment block: title, one-line purpose, author, month and year, and `Platforms: Python .NET and IronPython`.
- Keep the module thin. Domain logic belongs in the project's `converters/`; the module's job is reading the field, calling `convert()`, and writing the result. `__Template_converter_module.py` (kept at the repository root, since it isn't specific to any one project) is the starting point — copy it into the target project folder and change the marked places. It starts read-only (`FTM_ModifiesDB: False`, no custom field required): writing the result back is a commented-out block you uncomment deliberately once the read-only report looks right. See the [`adding-a-flextools-module`](.claude/skills/adding-a-flextools-module/SKILL.md) skill for the full procedure.
- The FlexTools scanner lists `*.py` at the **top level of each module folder only** and never recurses, so a project's own `converters/` and `tests/` are invisible to it, and this repository's `plans/` at the repository root plays no part since it sits outside every project folder; non-`.py` files are ignored; and files whose name starts with `__` are skipped *before* import, which is why the template is safe to ship. A copy of the template must therefore not keep the `__` prefix. This is also why the folder you point FlexTools at must be the project folder itself, not the repository root — see [What This Repository Is](#what-this-repository-is).
- Import the converter by adding the project's `converters/` to `sys.path` from `__file__`, as the template does: FlexTools imports a module by path, which does not put the module's own folder on `sys.path`.
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

- Use `pytest`, with each project's tests under its own `<project>/tests/`, run as `python -m pytest` from the repo root, which discovers every project's tests in one run.
- The repository root also keeps a shared `tests/` directory holding only cross-project test infrastructure — currently `tests/approval.py`, the approval-testing harness (see below). It has no test files of its own; project-specific tests live inside that project's folder, not here.
- Test each converter's `convert()` directly — it needs no FLEx project, so those tests run on any platform. Each project's own `<project>/tests/conftest.py` puts that project's `converters/` on `sys.path` so `from diacritics2chao import convert` works, and puts the repository's shared `tests/` on `sys.path` so `tests/approval.py` can be imported the same way.
- `flextoolslib` only installs on Windows alongside FieldWorks, so importing a module file fails elsewhere at its top-level `from flextoolslib import *`. A project's `tests/conftest.py` stubs `flextoolslib` in `sys.modules` and loads module files by path, so `MainFunction` can be driven with fake `project` and `report` objects on any platform.
- Those fakes cover the module's decisions, not FLEx itself, so still verify a changed module by running it in FlexTools with modification disabled before enabling it.
- Prefer small parametrized assertions while a converter's output is short strings. Switch to approval testing when output becomes large or awkward to assert inline: the checked-in artifact is the approved one, a mismatch produces a received artifact for review, and changes are never auto-accepted without explicit confirmation.
- **Don't let the two layers duplicate each other.** An inline unit test pins one behavioural rule, with whatever example (synthetic or real) makes that rule clearest in isolation. The approval corpus is the real-word regression net for the CLI as a whole. If a rule is already covered by a general-purpose unit test (e.g. "an unrelated diacritic survives in the base text"), a new real-world example demonstrating that same rule belongs in the approval corpus, not as a second unit test reasserting the identical input/output pair the corpus already checks — that's two tests failing for one bug, not two checks. Before adding a unit test for a new example, check whether it's about to assert exactly what a fixture file already asserts.
- **Approval testing convention** (see `chao-tone-letters/tests/test_diacritics2chao_cli.py` and `chao-tone-letters/tests/fixtures/diacritics2chao/` for the worked example): input fixtures live in `<project>/tests/fixtures/<converter>/inputs/*.txt`, approved outputs in `<project>/tests/fixtures/<converter>/approved/<stem>.approved.txt`, and a mismatch (or a fixture with no approved file yet) is written to `<project>/tests/fixtures/<converter>/received/<stem>.received.txt`. The shared `tests/approval.py` harness takes the calling project's own `tests/` directory explicitly, so fixture pairing and promotion work the same way in every project without duplicating that harness per project. Adding a fixture and approving a changed one are the same loop: drop or edit a `.txt` in `inputs/`, run `python -m pytest`, read the failure's received file, and — only once it looks right — promote it with the `cp` command the failure prints. Never write into `approved/` any other way.
- **The one exception: a fixture whose approved side is ground truth from an external specification.** Where the expected output comes from a source document rather than from the converter — as `zhire/tests/fixtures/phonemic2orthography/orthography_statement_phonemes` takes both sides from the Zhire orthography statement's own phoneme and grapheme columns — the promote loop is actively wrong, because promoting makes the converter its own judge and the test can then only ever confirm what the converter already does. Write both sides from the specification instead, and say in the project's `SPEC.md` where they came from and how they were derived, so the fixture can be re-derived when the specification changes. This is the same reasoning that makes a hand-authored expectation stronger than a snapshot, not a licence to hand-edit ordinary approved files.
- **Prefer attested real-world data for a fixture, but a rule can't wait forever on data that doesn't exist yet.** When no genuine example is at hand, a linguistically plausible constructed one is acceptable — but the fixture's filename must say so (e.g. a `_simulated` suffix, or a name like `simulated_<what_it_covers>.txt`), since a fixture has no comment lines to carry that distinction and the filename is the only label it gets. Prefer searching for a real attested example first; fall back to a constructed one, labelled, only once that search comes up empty.
- For a converter whose output is plain text, compare the approved file and the actual output **exactly**: no scrubbing, no Unicode normalisation, and no comment or label lines inside a fixture (the filename is the label). Normalising would hide a real regression whenever normalisation is itself part of what the converter guarantees, as NFC/NFD handling is for `diacritics2chao.py`.
- A few traps that make an approval suite look green while testing nothing, worth checking for in review: a fixture with no approved counterpart must fail loudly rather than being skipped or silently passing; `*.received.*` must stay gitignored so a received file can never be committed as though it were approved; drive a CLI subprocess with an explicit `encoding="utf-8"` rather than `text=True`, since the locale code page can mangle non-ASCII output; and an editor can silently strip trailing whitespace or re-normalise Unicode in a fixture file, corrupting an exact comparison — keep whitespace and normalisation-sensitive cases away from line ends.
- Keep approved artifacts human-reviewable and deterministic so diffs are meaningful.
- Follow TDD for behaviour changes: add or extend the test and confirm it fails first (red), write the minimum implementation to make it pass (green), then refactor with the tests as a safety net. For an approval test this means adding the fixture first and confirming the received output is wrong before implementing, then promoting the received file once it's right — the same reason a first approval must be read, never accepted on trust.

## Documentation

- `README.md` is the user-facing description of each converter and module. A new converter or module, or a behaviour change to an existing one, updates its README section in the same change.
- When a converter or module incorporates third-party code, name the author and licence in the source header, and record the resulting combined licence in the README's Attributions line.
