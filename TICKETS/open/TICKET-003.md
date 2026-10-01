# TICKET-003: Add annual user checklist and help screen

**Status**: open
**Type**: feature
**Priority**: high
**Stage**: needs-spec
**Created**: 2026-09-29
**Parent**: none

## Problem / Motivation

For a returning user generating reports annually, the process is unclear. They need to know: (1) what files to prepare/update, (2) in what order to run imports, (3) what checks to perform before generating reports, (4) how to validate the output. Currently no guided workflow exists.

## Acceptance Criteria

- [ ] Interactive help screen (`account --help-annual` or similar) that walks through annual workflow
- [ ] Checklist covers: reviewing/updating chart of accounts, preparing CSV exports, importing transactions, reconciling accounts, running depreciation, generating reports
- [ ] Each step includes validation checks (e.g., "confirm all transactions imported", "verify opening balances")
- [ ] Help screen prompts for missing files and provides clear next steps
- [ ] Document (ANNUAL_WORKFLOW.md) describes the full process for reference
- [ ] Includes troubleshooting for common annual issues (FY boundary, depreciation dates, GST reset)

## Design Notes

Create both an interactive CLI mode (for guided workflow) and a markdown document (for quick reference). CLI should check for required files and validate inputs before proceeding.

## Files Affected

- `ANNUAL_WORKFLOW.md` — new guide for returning users
- `dyu_accounting/__init__.py` — add `--help-annual` flag and workflow guidance
- `dyu_accounting/Utilities/` — add validation/checklist helper functions

## Implementation Notes

(To be filled during implementation)

## Testing

Test workflow end-to-end with a multi-year example (FY 2019 → FY 2020).

