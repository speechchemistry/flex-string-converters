# Make the FlexTools module template read-only

Status: approved 2026-08-19, implemented same day. Optional smoke-test section was declined.

## Context

`__Template_converter_module.py` is the file you copy to start a new FlexTools module. Before
this change it was a copy of the full Chao module: it looked up an entry-level custom field,
wrote the converted result into it, and set `FTM_ModifiesDB: True`.

That made the first run of a fresh copy fail on setup rather than on anything to do with the
converter. Until the author had created a custom field in FLEx (Tools > Configure > Custom
Fields…) and named it in `TARGET_FIELD_NAME`, the module reported `The entry-level <field> field
is missing` and degraded to read-only. Requiring that before you can see whether the module reads
the right field and converts correctly is backwards — and it made "modifies the database" the
default posture in a repo whose README warns that FLEx has no undo across a FlexTools run.

The intended outcome: a template that runs against any FLEx project as soon as it is copied,
reads the lexeme form of every entry, reports `<form> -> <result>` for each, and writes nothing.
Writing becomes something the author adds deliberately, guided by a commented block that names
the traps.

`Extract_Chao_tone_letters_from_accent_notation.py` is unchanged by this. It keeps writing to
`Pitch`; it is the worked example the template points at.

## Approach

### Rewrite `__Template_converter_module.py`

Keep the standard shape `AGENTS.md` requires, in the same order: `# -*- coding: utf-8 -*-`
header, `from flextoolslib import *`, the `sys.path` bootstrap to `converters/`, the `docs` dict,
`MainFunction(project, report, modifyAllowed)`, and `FlexToolsModule = FlexToolsModuleClass(...)`
last. Keep the `__` prefix and the paragraph explaining why copies must drop it.

Changes:

- **Header comment**: say plainly that the template only reports what the conversion would
  produce, writes nothing, and needs no custom field — and point at the "Writing the result back"
  block at the bottom.
- **`docs`**: `FTM_ModifiesDB: False`. `FTM_Description` describes a read-only report instead of
  the replace-vs-accumulate wording, which no longer applies.
- **Delete** `TARGET_FIELD_NAME`, `TARGET_WS`, and `targetWritingSystem()`. Nothing in the
  read-only path needs them; they reappear in the commented block below.
- **`MainFunction`**: keep the fixed three-argument signature (FlexTools calls it that way) and
  note in a comment that `modifyAllowed` is unused because nothing is written. Body becomes:
  one `report.Info` naming the vernacular writing system the lexeme forms are read from — a
  wrong writing system is the failure that looks most like a no-op, so it is worth the two lines
  even in a preview — then `LexiconNumberOfEntries`, `ProgressStart`, the loop over
  `LexiconAllEntries` with `ProgressUpdate` and `LexiconGetLexemeForm`, one `report.Info` per
  entry, and a closing count of how many entries produced a non-empty result.
- **Add a commented "Writing the result back" section** between `MainFunction` and the
  `FlexToolsModule` assignment. Commented-out code, not live code, covering: setting
  `FTM_ModifiesDB` to `True`; `LexiconGetEntryCustomFieldNamed` with a `report.Error` and
  degrade-to-read-only rather than raising; resolving the writing system from
  `GetDefaultVernacularWS()`; and the guarded `LexiconSetFieldText(entry, field, result, ws)`
  call. Then name the three traps in one line each, since each one fails silently:
  - `LexiconSetFieldText` defaults to the default *analysis* writing system, so pass the writing
    system explicitly or the text lands where a vernacular field never displays it.
  - `LexiconAddTagToField` reads the field back with no writing system and raises
    `AttributeError` on a multi-string custom field, so don't use it.
  - Skip empty results, or a value the user typed by hand gets cleared.

  Close with a pointer to `Extract_Chao_tone_letters_from_accent_notation.py` as the full worked
  example.

### Documentation

- **`README.md`** — the `__Template_converter_module.py` section: state that the template reads
  and reports only, needs no custom field, and that writing back is a commented block you
  uncomment. Nothing else in the README changes; the Chao module's section still describes its
  `Pitch` requirement accurately.
- **`AGENTS.md`** — under [FlexTools Module Conventions](../../AGENTS.md#flextools-module-conventions),
  extend the existing "`__Template_converter_module.py` is the starting point" bullet to say it
  starts read-only and that writes are added deliberately. The `LexiconSetFieldText` bullet stays
  exactly as it is: it is a rule for modules generally, not for the template.
- **`SPEC.md`** — no change. `SPEC.md` covers converters and the modules that wrap them; the
  template is neither, and the Chao module's contract is untouched.

## Files changed

- `__Template_converter_module.py` — rewritten (the whole change of substance)
- `README.md` — template section
- `AGENTS.md` — one bullet under FlexTools Module Conventions

## Verification

1. `python -m pytest` from the repo root — the existing converter and Chao module tests must all
   still pass. Nothing this change touches is on their path.
2. Read the rewritten template top to bottom against
   `Extract_Chao_tone_letters_from_accent_notation.py`: the order of the standard shape matches,
   `FlexToolsModule` is spelled exactly, and the `sys.path` bootstrap is intact.
3. `python3 -c "import ast; ast.parse(open('__Template_converter_module.py').read())"` — the file
   cannot be imported off Windows or without a real `my_converter`, so parse it instead to catch a
   syntax error in the rewrite.
4. Confirm the commented block stays commented: `grep -n 'LexiconSetFieldText'
   __Template_converter_module.py` should show only lines beginning with `#`.
5. In FlexTools (Windows, needs FieldWorks): copy the template to a scratch name without the `__`
   prefix, point its import at `chao_tones`, and run it over a project with modification
   **disabled** and then **enabled**. Both runs must produce identical output and leave the
   project unmodified. Confirm FlexTools shows it as not modifying the database.
