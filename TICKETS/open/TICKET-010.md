# TICKET-010: Preserve manual categorizations across re-runs of --guided

**Status**: open
**Type**: feature
**Priority**: medium
**Stage**: needs-spec
**Created**: 2026-11-25
**Parent**: none

## Problem / Motivation

Several of this project's importers (IDFC, SBI, ICICIBank, ICICICard,
Upworks) only ever produce a single-leg posting — the bank/card side —
with no target/expense account, since none of these sources carry
enough information on their own to categorize a transaction. The user
routinely completes these by hand, directly editing the generated
`FY{fy}/intermediate/*.beancount` files to add the missing second leg
(and, for a couple of large Upwork-matched entries, to reconcile them
against `--reconcile-upwork`).

`account --guided` regenerates every `FY{fy}/intermediate/*.beancount`
file from scratch on each run (via `gulp_runner.py::run_bean_extract()`,
which re-invokes `bean-extract` per file and overwrites the output).
Re-running guided mode on an FY that already has manual categorization
work in it — e.g. to pick up newly-arrived statement rows, or an
importer bug fix — silently discards all of that manual work with no
warning.

This was surfaced directly during a real editing session: the user had
hand-added legs to `idfc_bank_*.beancount` and
`icici_card_*.beancount` and explicitly said "it is not feasible to
delete everything and restart" when something else needed fixing.

## Acceptance Criteria

- [ ] Re-running `account --guided` (or just the extraction step) for an
      FY that already has manually-categorized intermediate files does
      not lose the manual second-leg postings/metadata a human added.
- [ ] Genuinely new source rows (e.g. a statement re-downloaded with
      more recent transactions appended) still get extracted and
      appended/merged correctly.
- [ ] A transaction that already has a completed (2+ posting) structure
      is left alone by re-extraction, rather than being overwritten
      back to its single-leg form.
- [ ] Behavior is predictable and communicated to the user — e.g. a
      printed summary of how many transactions were preserved vs.
      newly extracted vs. (if ever necessary) require manual conflict
      resolution.
- [ ] Covered by a real end-to-end test: extract once, hand-edit an
      entry (simulating manual categorization), re-run extraction, and
      assert the hand-edit survives while new rows still appear.

## Design Notes

Not yet designed. Some approaches to evaluate:

- **Diff-and-merge by a stable key** (date + payee/narration + amount,
  or a hash of the original uncategorized posting) — match
  newly-extracted single-leg entries against what's already on disk;
  if an existing entry with the same key already has 2+ postings, keep
  the existing (manually-completed) one instead of the freshly
  extracted single-leg one.
- **Only append, never overwrite** — track the last-processed
  row/date per source file and only extract rows after that point on
  subsequent runs. Simpler, but doesn't handle a statement being
  re-downloaded with corrections to already-imported rows.
- Needs to interact sensibly with `reconcile_account.py` and
  `reconcile_upwork.py`, which already rewrite these same intermediate
  files (and already have their own idempotency guards worth reusing
  as a model).

## Files Affected

- `dyu_accounting/gulp_runner.py` — `run_bean_extract()` currently
  unconditionally overwrites each intermediate file.
- Possibly a new module (e.g. `dyu_accounting/merge_intermediate.py`)
  rather than cramming merge logic into `gulp_runner.py` directly.

## Implementation Notes

(fill in during implementation)

## Testing

(fill in during implementation)
