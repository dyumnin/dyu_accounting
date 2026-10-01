# TICKET-004: Document CSV parsing workflow and import process

**Status**: open
**Type**: improvement
**Priority**: high
**Stage**: needs-spec
**Created**: 2026-09-29
**Parent**: none

## Problem / Motivation

The beancounter CLI in the dyu package parses CSVs (Upwork, Razorpay) but users don't know: (1) where these importers live, (2) how to create custom importers for their data sources, (3) how to integrate generated entries into the main ledger, (4) what the CSV format requirements are. Documentation jumps from "here's the command" to "here's the output" without explaining the middle.

## Acceptance Criteria

- [ ] CSV_IMPORT.md documents the overall workflow: export CSVs from source → run importer → validate entries → merge into ledger
- [ ] Document maps which fields in each CSV source map to beancount entry fields
- [ ] Examples show sample CSV inputs and their corresponding beancount outputs
- [ ] Instructions cover: how to run Upwork importer, how to run Razorpay importer, where output goes, how to review before committing
- [ ] Guide includes creating a custom importer for other data sources (template + example)
- [ ] Reconciliation guidance: how to verify imported entries match source data, how to handle discrepancies

## Design Notes

Create CSV_IMPORT.md with both reference sections (field mappings, format specs) and a cookbook section (step-by-step examples). Consider adding a `--dry-run` flag to importers so users can preview output before writing to files.

## Files Affected

- `CSV_IMPORT.md` — new import workflow guide
- `importers/custom_importer_template.py` — skeleton for users to create their own
- `src/dyu/beancounter.py` — optionally add `--dry-run` and `--validate` modes
- `dyu_accounting/__init__.py` — document integration points with dyu.beancounter

## Implementation Notes

(To be filled during implementation)

## Testing

Test each CSV type and custom importer with sample data. Verify entries merge cleanly into ledger without duplicates or conflicts.

