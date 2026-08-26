---
name: checking-a-converter-against-its-source
description: Reconcile a converter's mapping tables against the external document they came from — an orthography statement, a standard, a published chart — so a correspondence that was dropped while copying fails a test instead of surviving unnoticed. Use when building a converter from such a document, when that document is revised, or when a mapping turns out to be missing.
license: MIT
compatibility: any Python 3 environment with pytest installed; no FieldWorks or flextoolslib dependency
---

# Checking a converter against its source

Some converters implement a correspondence table that a human wrote down somewhere else — an orthography statement, an IPA chart, a standard. That document is the authority, and the converter's tables are a copy of it. **Copies lose rows, and a lost row is invisible unless something counts.**

This is not hypothetical. `zhire/converters/phonemic2orthography.py` was built from a Zhire orthography statement and shipped missing three of its correspondences (`/tʃ/ → c`, `/ŋmɡb/ → ngb`, `/ɾ/ → r`). All three were written down correctly in the statement. The plan that built the converter presented a 21-row consonant table where the statement had 32 rows, never stated the source's count, and so left no hole for anyone to notice. Two were found months later — one by the language consultant reading the source, one by a held-out word.

Treat copying a specification as a **data migration**, not as reading comprehension. Migrations get row counts and reconciliation.

## The procedure

1. **Read the source document from the file itself, never a pasted copy.** Pasting through a chat transport corrupts IPA and other non-ASCII characters, and the corruption then gets baked into the repository. If the file is on a shared drive, read it from there.

2. **Enumerate every row of every correspondence table — including the categories you expect to be out of scope.** Do not sample, and do not skip a table because you have already decided its rows don't apply. In the Zhire case the check skipped every row using modifier-letter notation as "out of scope", on the strength of an untested assumption that their plain-letter equivalents composed correctly. That assumption was true for four of them and false for the fifth, which was the one row the check declined to look at.

3. **Reconcile the counts, and account for every row explicitly.** State the source's row count, then place each row in exactly one bucket:
   - implemented directly as a table entry;
   - **produced by composing other entries** (e.g. a sequence whose output is its parts' outputs concatenated);
   - deliberately out of scope, with the reason recorded.

   Every row must land somewhere, and the buckets must sum to the source's total. `21 atomic + 11 accounted for = 32 rows in the source` is the sentence whose absence let three phonemes go missing. Write it out.

4. **Test the "produced by composition" bucket — never assert it.** This is the cheapest and highest-yield step: for each such row, run the converter on the source's input and compare with the source's stated output. It is a few lines of code. In the Zhire case two of eleven rows in that bucket were wrong, and both would have failed instantly.

5. **Build a fixture from the source's own correspondence columns, taking *both* sides from the source.** The input side is the source's input notation, the approved side is the source's stated output. Do not produce the approved side by promoting the converter's output — that makes the converter its own judge, and the test can then only ever confirm what the converter already does. This is the exception to the promote-only rule in [AGENTS.md's Testing Approach](../../../AGENTS.md#testing-approach); see [`adding-an-approval-fixture`](../adding-an-approval-fixture/SKILL.md) for the ordinary loop that applies everywhere else.

6. **Watch for a notation gap between the source and the real data.** A source document often writes correspondences in a more precise or more phonetic notation than the data a converter actually receives. Where they differ, decide deliberately, record the decision, and consider accepting both — do not silently rewrite the source's symbol to match the data, which is how `/ɾ/` became `r` in the Zhire tables with no trace of a decision having been made. Where the source's examples are in a different representation entirely (phonetic rather than phonemic, say), they are **not** usable as fixture input without a conversion step whose rules may not be settled.

7. **Record the derivation in the project's `SPEC.md`**: which document, which of its tables, and any transliteration applied. A parser for one document's format is usually not worth writing — the next source will be a different shape — so the enumeration may well be manual, and then the written-down derivation is the only thing that makes it repeatable.

8. **Report the reconciliation to the human, not just the verdict.** "Your statement has 32 consonant rows; here are all 32 and where each one went" is reviewable. A tidy table that looks complete is not, because nothing in it states what complete would be. This is what makes a domain expert's review cheap and high-yield instead of requiring them to diff the source by eye.

## What this cannot catch

A source-derived check verifies the converter against what the document says. It is silent about **what the document doesn't say**.

Zhire's `/l/` was missing from the converter *and* from the orthography statement — it enters the language through loanwords that the statement had not yet covered. No amount of checking against the statement would ever have surfaced it; a held-out real word did, immediately.

So this procedure and real-data testing are complementary, and fail in opposite directions:

- **Source-derived fixture** — catches correspondences lost in copying, and drift when the document is revised. Blind to gaps in the document itself.
- **Real or held-out data** — catches what the document omits. Blind to anything the data happens not to contain, which is exactly how `/tʃ/` survived a 99-word corpus containing no `tʃ`.

Neither alone is sufficient. When a mapping gap is found by either route, ask which net should have caught it and whether that net needs widening.

## When the source document changes

The fixture is a snapshot and cannot know a row was added. Re-run this procedure whenever the source is revised — that dependency is on the human who edits the document, so make sure the project's `SPEC.md` says so plainly.
