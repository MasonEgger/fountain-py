# Lessons Learned

## Recent
<!-- 10 most recent lessons, newest first -->
- During a BPE run, a plan step can be non-atomic: the Python 3.10 floor bump coupled requires-python + ruff-target (which forces the Optional->X|None sweep) + the CI matrix into one commit, because just test runs lint before fix and would hard-fail otherwise. When a config bump surfaces a deferred sweep, fold the coupled pieces into one commit rather than shipping a broken intermediate (2026-07-08)
- When a `/bpe:plan` re-run finds plan.md already complete and spec-consistent, verify-and-report instead of regenerating; only rewrite on explicit format or scope direction (2026-07-08)
- Keep step numbering stable across a plan reformat so todo.md stays valid without a parallel rewrite; verify with a step-number diff between the two files (2026-07-08)
- `/bpe:goal` pre-flight refuses until `goal.md` is gitignored; add it alongside `commit-msg.md` before the run (2026-07-08)
- Read `.ai-sessions/` summaries before diffing a large uncommitted tree; the 2026-07-02 spec-pass note explained a 577-line spec.md diff in one screen (2026-07-03)
- Commit each plan batch as it finishes; three unrelated batches (API break, release prep, spec audit) piled into one 1,441-line working tree and had to be untangled after the fact (2026-07-03)
- To split one file's hunks across commits, save `git diff -- <file>` to a patch, trim it, and `git apply --cached` the remainder (2026-07-03)

<!--
Category sections live below. Create each one only when at least one
lesson belongs to it. Use the most specific applicable category.
-->

## BPE Workflow
- During a BPE run, a plan step can be non-atomic: the Python 3.10 floor bump coupled requires-python + ruff-target (which forces the Optional->X|None sweep) + the CI matrix into one commit, because just test runs lint before fix and would hard-fail otherwise. When a config bump surfaces a deferred sweep, fold the coupled pieces into one commit rather than shipping a broken intermediate (2026-07-08)
