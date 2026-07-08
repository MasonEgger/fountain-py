# Lessons Learned

## Recent
<!-- 10 most recent lessons, newest first -->
- When documenting parser edge behavior, verify every prose claim by importing the library, not by intuition. Twice in this run a doc step asserted false "workarounds" for colon-bearing first lines (A3, D11): a leading blank line and a leading > do NOT bypass the line-one title-page heuristic; the only reliable body-context fix is a preceding action line. (2026-07-08)
- Stripping inline-markup delimiters requires re-indexing spans onto the cleaned text, not the source: resolve escapes to placeholders first (so an escaped delimiter is not consumed), mark delimiter chars for deletion, rebuild the clean string, then map each span through a kept-before prefix count. Exclude verbatim element types (notes, boneyard) from the strip so they keep their raw text. (2026-07-08)
- Ruff F841 does not flag a write-only collection: a `set()` that is assigned and `.add()`-ed but never read counts the `.add()` as a use, so dead accumulator sets slip past lint. Flag write-only collections in review by hand. (2026-07-08)
- Spec acceptance criteria can contradict earlier spec rules; E10 asked for bracket-stripped NOTE text while body rule 6 mandates verbatim brackets. Resolve toward the established contract (and its passing round-trip test) rather than the newer criterion's literal wording, and record the mismatch for the docs step. (2026-07-08)
- During a BPE run, a plan step can be non-atomic: the Python 3.10 floor bump coupled requires-python + ruff-target (which forces the Optional->X|None sweep) + the CI matrix into one commit, because just test runs lint before fix and would hard-fail otherwise. When a config bump surfaces a deferred sweep, fold the coupled pieces into one commit rather than shipping a broken intermediate (2026-07-08)
- When a `/bpe:plan` re-run finds plan.md already complete and spec-consistent, verify-and-report instead of regenerating; only rewrite on explicit format or scope direction (2026-07-08)
- Keep step numbering stable across a plan reformat so todo.md stays valid without a parallel rewrite; verify with a step-number diff between the two files (2026-07-08)
- `/bpe:goal` pre-flight refuses until `goal.md` is gitignored; add it alongside `commit-msg.md` before the run (2026-07-08)
- Read `.ai-sessions/` summaries before diffing a large uncommitted tree; the 2026-07-02 spec-pass note explained a 577-line spec.md diff in one screen (2026-07-03)
- Commit each plan batch as it finishes; three unrelated batches (API break, release prep, spec audit) piled into one 1,441-line working tree and had to be untangled after the fact (2026-07-03)

<!--
Category sections live below. Create each one only when at least one
lesson belongs to it. Use the most specific applicable category.
-->

## Spec
- Spec acceptance criteria can contradict earlier spec rules; E10 asked for bracket-stripped NOTE text while body rule 6 mandates verbatim brackets. Resolve toward the established contract (and its passing round-trip test) rather than the newer criterion's literal wording, and record the mismatch for the docs step. (2026-07-08)

## Tooling
- Ruff F841 does not flag a write-only collection: a `set()` that is assigned and `.add()`-ed but never read counts the `.add()` as a use, so dead accumulator sets slip past lint. Flag write-only collections in review by hand. (2026-07-08)

## Parsing
- When documenting parser edge behavior, verify every prose claim by importing the library, not by intuition. Twice in this run a doc step asserted false "workarounds" for colon-bearing first lines (A3, D11): a leading blank line and a leading > do NOT bypass the line-one title-page heuristic; the only reliable body-context fix is a preceding action line. (2026-07-08)
- Stripping inline-markup delimiters requires re-indexing spans onto the cleaned text, not the source: resolve escapes to placeholders first (so an escaped delimiter is not consumed), mark delimiter chars for deletion, rebuild the clean string, then map each span through a kept-before prefix count. Exclude verbatim element types (notes, boneyard) from the strip so they keep their raw text. (2026-07-08)

## BPE Workflow
- During a BPE run, a plan step can be non-atomic: the Python 3.10 floor bump coupled requires-python + ruff-target (which forces the Optional->X|None sweep) + the CI matrix into one commit, because just test runs lint before fix and would hard-fail otherwise. When a config bump surfaces a deferred sweep, fold the coupled pieces into one commit rather than shipping a broken intermediate (2026-07-08)
