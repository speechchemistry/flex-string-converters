---
name: adding-a-project
description: Scaffold a new project folder (SPEC.md, converters/, tests/) for a new converter or topic, and register it in the root SPEC.md index. Use when starting work on a converter that doesn't belong in any existing project folder.
license: MIT
compatibility: any Python 3 environment with pytest installed; no FieldWorks or flextoolslib dependency
---

# Adding a project

This repository groups converters into project folders at the repository root, one per topic or
language community (e.g. `chao-tone-letters/`) — see [AGENTS.md's What This Repository Is
section](../../../AGENTS.md#what-this-repository-is). This procedure scaffolds a new one.

## Steps

1. **Pick a name.** Name the folder after the topic if the converter(s) inside it are useful beyond
   any one language (like `chao-tone-letters`), or after the language or community if the work is
   specific to it. Use a short kebab-case name; it becomes the folder name and appears throughout
   `SPEC.md`, `AGENTS.md` examples, and the README.

2. **Create the folder structure:**

   ```
   mkdir -p <project>/converters <project>/tests/fixtures
   ```

3. **Write `<project>/SPEC.md`.** Follow the shape of `chao-tone-letters/SPEC.md`: an opening
   paragraph pointing to [the root `SPEC.md`](../../../SPEC.md) and [AGENTS.md's Specification
   section](../../../AGENTS.md#specification), then one `##` section per converter once it exists.
   Per [AGENTS.md's Specification section](../../../AGENTS.md#specification), do not speculatively
   write rules for a converter that doesn't exist yet — write the spec section only once you've built
   the thing it describes, in the same change.

4. **Write the converter.** Add `<project>/converters/<what_it_converts>.py` following [AGENTS.md's
   Converter Conventions](../../../AGENTS.md#converter-conventions): a `convert(input_string)`
   function, a command line interface, and no `flextoolslib` or FieldWorks import.

5. **Write `<project>/tests/conftest.py`.** Adapt `chao-tone-letters/tests/conftest.py`:

   ```python
   PROJECT_ROOT = Path(__file__).resolve().parent.parent
   REPO_ROOT = PROJECT_ROOT.parent
   sys.path.insert(0, str(PROJECT_ROOT / "converters"))
   sys.path.insert(0, str(REPO_ROOT / "tests"))
   ```

   The second `sys.path` entry makes the repository-wide shared `tests/approval.py` harness
   importable as `approval` once you add CLI approval tests (see step 7). Leave out the
   `flextoolslib` stub and any module-loading fixture until this project actually has a FlexTools
   module — see the [`adding-a-flextools-module`](../adding-a-flextools-module/SKILL.md) skill for
   that.

6. **Write `<project>/tests/test_<what_it_converts>.py`** covering `convert()` directly, per
   [AGENTS.md's Testing Approach](../../../AGENTS.md#testing-approach).

7. **Add approval tests once the CLI's output is realistic or awkward to assert inline** — see the
   [`adding-an-approval-fixture`](../adding-an-approval-fixture/SKILL.md) skill.

8. **Register the project in the root `SPEC.md`.** Add one line to its Projects list, linking to
   `<project>/SPEC.md` with a short description of what the project covers.

9. **Update `README.md`** with a section for the new converter, following the shape of the existing
   `chao-tone-letters` sections.

10. **Run `python -m pytest`** from the repository root to confirm the new project's tests are
    discovered and pass alongside every other project's.
