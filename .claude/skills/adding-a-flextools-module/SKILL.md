---
name: adding-a-flextools-module
description: Wrap an existing converter in a project folder with a FlexTools module, starting from __Template_converter_module.py. Use when a converter should run over a whole FLEx lexicon, not only from the command line.
license: MIT
compatibility: FlexTools module files require Python .NET / IronPython to run for real, but this procedure and the resulting file can be edited and unit-tested (with a stubbed flextoolslib) on any Python 3 environment
---

# Adding a FlexTools module

A FlexTools module is a thin wrapper that reads a FLEx field, calls a converter's `convert()`, and
reports or writes the result. See [AGENTS.md's FlexTools Module
Conventions](../../../AGENTS.md#flextools-module-conventions) and [Data
Safety](../../../AGENTS.md#data-safety) for the rules this procedure follows, and
`chao-tone-letters/Extract_Chao_tone_letters_from_tone_diacritics.py` for the worked example this
skill's steps produce.

This assumes the converter already exists in a project folder (see the
[`adding-a-project`](../adding-a-project/SKILL.md) skill if not).

## Steps

1. **Copy the template into the project folder**, dropping the leading `__`:

   ```
   cp __Template_converter_module.py <project>/<What_it_does>.py
   ```

   The template lives at the repository root because it isn't specific to any one project. The
   leading `__` is what keeps FlexTools from importing the template itself as a module — a copy must
   not keep it, or FlexTools will never find your copy either.

2. **Point the import at your converter.** In the copy, the `sys.path` bootstrap already resolves
   `converters/` relative to the module file's own location, so once the file lives inside
   `<project>/`, it finds `<project>/converters/` automatically. Just change:

   ```python
   from my_converter import convert
   ```

   to your converter's actual module name, e.g. `from diacritics2chao import convert`.

3. **Fill in the marked places**: the header comment block (title, one-line purpose, your name, month
   and year, `Platforms: Python .NET and IronPython`), and the `docs` dict (`FTM_Name`,
   `FTM_Synopsis`, `FTM_Description`). Leave `FTM_ModifiesDB: False` and `FTM_Version: 0.1` for now.

4. **Leave `MainFunction` read-only for the first pass.** The template's version reads every entry's
   lexeme form, calls `convert()`, and reports the result via `report.Info` — it writes nothing and
   needs no custom field, so it's safe to run against a real project immediately.

5. **Verify the read-only report**, on any platform, with a project-level test using the stubbed
   `flextoolslib` pattern. Add a `flextoolslib` stub and a module-loading fixture to
   `<project>/tests/conftest.py` (see `chao-tone-letters/tests/conftest.py`'s
   `_install_flextoolslib_stub` and `chao_module` fixture), then write
   `<project>/tests/test_<module_name>.py` driving `MainFunction` with a fake `project` and `report`,
   following `chao-tone-letters/tests/test_extract_chao_tone_letters_module.py`.

6. **Run it in FlexTools itself** before writing anything: copy the project folder (not the whole
   repository — see [AGENTS.md's What This Repository Is
   section](../../../AGENTS.md#what-this-repository-is)) into your FlexTools `Modules` folder, and
   confirm the dry-run report against a real project looks right.

7. **Only once that looks right, uncomment the "Writing the result back" block** and delete the
   read-only `MainFunction` above it. Follow the three traps called out in the template's comments —
   pass the writing system explicitly to `LexiconSetFieldText`, never use `LexiconAddTagToField`, and
   skip empty results so a hand-entered value isn't cleared — and set `FTM_ModifiesDB: True`.

8. **Add the module's section to `<project>/SPEC.md`**: what it reads, the transform, what it writes
   and to which writing system, its prerequisites, and what it reports — following the shape of
   `chao-tone-letters/SPEC.md`'s existing module section.

9. **Add a README section** for the module, and back up your FLEx project before testing writes for
   real — see [AGENTS.md's Data Safety section](../../../AGENTS.md#data-safety).

10. **Bump `FTM_Version`** whenever you come back and change the module's behaviour later.
