# TICKET-003: Add annual user checklist and help screen

**Status**: closed
**Type**: feature
**Priority**: high
**Stage**: done
**Created**: 2026-09-29
**Completed**: 2026-10-03
**Parent**: none

## Current State

`ANNUAL_WORKFLOW.md` has been written at the repo root per the exact outline
in "Design Notes (Impl-Planner)": 6-step checklist (config.json review ->
`account --guided` -> reconciliation review -> `account
--infile/--fy/--outdir` report generation -> report review ->
troubleshooting), with per-step success-validation notes, explicit
depreciation-is-automatic callout, and "See Also" cross-references to
GUIDED_MODE.md and TICKET-004's CSV_IMPORT.md (not yet written as of this
pass) instead of duplicating their content. No code changes made;
`--help-annual` CLI flag remains explicitly out of scope. Validation
Required: no — pure documentation, no tests needed. Stage moved to
`awaiting-approval`; awaiting explicit human sign-off before closing per
pipeline policy (this ticket has no validator stage, but still requires a
human approval turn before being marked done).

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

- `ANNUAL_WORKFLOW.md` — new guide, 6-step checkbox checklist (config.json review → `account --guided` → reconciliation review → `account --infile/--fy/--outdir` → report review → troubleshooting). Cross-references GUIDED_MODE.md and CSV_IMPORT.md, does not duplicate their content. No other files are touched — `--help-annual` CLI flag is explicitly out of scope (see Researcher Findings / Design Notes (Impl-Planner)).

## Implementation Notes

Implemented exactly per the "Exact Outline for ANNUAL_WORKFLOW.md" in
Design Notes (Impl-Planner), with no deviation:

- Created `ANNUAL_WORKFLOW.md` at repo root with a 6-step checkbox
  checklist: (1) config.json/chart-of-accounts review, (2) `account
  --guided`, (3) reconciliation report review, (4) legacy `account
  --infile ... --fy ... --outdir ...` report generation, (5) generated
  report review, (6) troubleshooting.
- Used the correct flags `--infile`/`--outdir` (not `--in`/`--out`) per
  the impl-planner's confirmed correction against
  `dyu_accounting/__init__.py` lines 63-71.
- Step 4 explicitly states depreciation is computed automatically by
  `dyu_accounting.depreciation.Depreciation` during report generation —
  not a separate manual step.
- Each step includes a "Success validation" line describing what
  confirms the step succeeded (file existence, transaction counts,
  JSON validity, balance-sheet continuity, etc.).
- Troubleshooting section documents the `config.json` `FileNotFoundError`
  failure mode as expected current behavior (no code change made, per
  the impl-planner's resolution of the open question — out of scope),
  plus FY-boundary and GST-period-mismatch guidance.
- "See Also" section links to `GUIDED_MODE.md` and `CSV_IMPORT.md`
  (TICKET-004) instead of duplicating their content. Note: `CSV_IMPORT.md`
  does not exist yet as of this writing (TICKET-004 is still
  `ready-to-implement`); the link is forward-referencing per plan and will
  resolve once TICKET-004 lands.
- No code changes, no `--help-annual` CLI flag (explicitly out of scope
  per Design Notes). No tests added — pure documentation,
  Validation Required: no.

Verification performed: manual proofreading of `ANNUAL_WORKFLOW.md`
against the Design Notes outline (diffed line-by-line) and against
`dyu_accounting/__init__.py` for the `--infile`/`--fy`/`--outdir` flag
names. No automated tests apply to this change.

## Testing

Test workflow end-to-end with a multi-year example (FY 2019 → FY 2020).


## Requirements (Researcher-Refined)

### Investigation Summary

Guided mode (`account --guided`, TICKET-005–009) already handles: FY folder creation, importer discovery/selection, file validation, bean-extract invocation, and parent-ledger + reconciliation report generation. It stops after the reconciliation report — it never calls into the legacy report pipeline.

The legacy report pipeline lives in `dyu_accounting/__init__.py::accounting()` (`account --in ledger.beancount --fy YYYY --out reports/`). It requires a hand-authored `config.json` and runs, in order: Depreciation report, Exchange Gain calc, P&L, Journal, Balance Sheet (prior + current year), GST report, then renders `index.html`.

**Genuinely uncovered part of the annual workflow**:
1. Chart-of-accounts/`config.json` review for the year
2. Invoking legacy `account --in --fy --out` against the guided-mode-produced parent ledger
3. Reviewing generated reports/index.html
4. GST-period-boundary and FY-boundary sanity checks

**Correction to original scope**: "Running depreciation" is NOT a manual step — `dyu_accounting.depreciation.Depreciation` computes it automatically during report generation. Original AC was inaccurate on this point.

No existing `--help-annual` flag or interactive help screen exists in the codebase.

### Feasibility: ✅ Primarily documentation task

Guided mode already provides the only interactive portion needed. Remaining steps (config.json review, legacy report invocation, report review) are non-interactive, file-editing/single-command steps — building a second interactive CLI mode would duplicate `--guided`'s UX for no benefit.

**Risk flagged**: legacy `account` command requires `config.json` in invocation directory with no error handling if missing — raises unhandled `FileNotFoundError`. Checklist must flag this requirement.

### Acceptance Criteria

- [ ] `ANNUAL_WORKFLOW.md` documents full annual cycle as checkbox checklist:
  1. Review/update `config.json` and chart-of-accounts attributes for new FY
  2. Run `account --guided` (cross-reference GUIDED_MODE.md, don't duplicate)
  3. Review `reconciliation_FY{year}.txt` for unexpected transactions/accounts
  4. Run `account --in FY{year}.beancount --fy {year} --out reports/{year}/` to generate reports
  5. Review generated `index.html` and individual reports
  6. Troubleshooting section for FY-boundary and GST-period issues
- [ ] Explicitly states depreciation is automatic (not manual) — corrects original assumption
- [ ] Each checklist step states what validates success
- [ ] Cross-references GUIDED_MODE.md instead of re-describing guided-mode UX
- [ ] Notes relationship to TICKET-004 (CSV importer docs) without duplicating scope
- [ ] `--help-annual` CLI flag explicitly OUT OF SCOPE — only markdown checklist required

### Design Notes

**Scope narrowed** from original ticket (pre-dated guided mode) to: write ANNUAL_WORKFLOW.md chaining config.json review → `account --guided` → reconciliation review → `account --in/--fy/--out` → report review, with troubleshooting.

**Open question for impl-planner**: Whether to also patch `dyu_accounting/__init__.py` to fail with a clear error (rather than raw FileNotFoundError) if config.json is missing — flagged for impl-planner decision, not part of this spec's acceptance criteria.

**Prior art**: GUIDED_MODE.md is the template/style to follow (numbered workflow, example session, troubleshooting section).

### Design Notes (Impl-Planner)

**CLI flag correction**: `dyu_accounting/__init__.py::accounting()` legacy mode uses `--infile` and `--outdir`, NOT `--in`/`--out` as written in earlier draft text. The document must use the real flags:
```
account --infile FY{year}/FY{year}.beancount --fy {year} --outdir reports/{year}/
```
(confirmed against `dyu_accounting/__init__.py` lines 63-71).

**config.json open question resolved**: Stays pure documentation — no patch to `__init__.py`. Document the `config.json`-must-exist-in-cwd requirement and raw `FileNotFoundError` failure mode explicitly in Step 1 and in Troubleshooting, rather than changing code. A separate bug ticket can be filed later if better error handling is wanted; out of scope here.

**Validation Required**: no — pure documentation change, no behavior/output of the system changes.

#### Exact Outline for ANNUAL_WORKFLOW.md

```markdown
# Annual Workflow

(1-2 sentence intro: this is the yearly checklist for a returning user,
start to finish, from chart-of-accounts review through final reports.
Cross-links: GUIDED_MODE.md for the import step, CSV_IMPORT.md for importer
details per TICKET-004.)

## Annual Checklist

### Step 1: Review config.json and chart of accounts
- [ ] Confirm `config.json` exists in the directory you will run `account` from
      (legacy report mode fails with an unhandled FileNotFoundError if missing
      — see Troubleshooting)
- [ ] Review `company`, `ar`, `exchange_gain`, `cash_accounts`, `gst.qrmp` fields
      for changes this year (new bank accounts, new cash accounts, GST scheme
      change)
- Success validation: `config.json` parses as valid JSON and every account
  referenced in it exists in your chart of accounts for the new FY

### Step 2: Run guided import (`account --guided`)
- [ ] Run `account --guided` to create the FY folder, select importers, place
      statement files, and generate the parent ledger
- (Full walkthrough: see GUIDED_MODE.md — do not duplicate here)
- Success validation: `FY{year}/FY{year}.beancount` and
  `FY{year}/reconciliation_FY{year}.txt` both exist; guided mode printed
  "Guided import complete!"

### Step 3: Review reconciliation report
- [ ] Open `FY{year}/reconciliation_FY{year}.txt`
- [ ] Check transaction counts per importer look reasonable (compare to prior
      year / bank statement count)
- [ ] Check the account list for unexpected or misspelled accounts
- [ ] Check each importer's date range falls fully inside the FY boundary
      (no stray Mar/Apr transactions from adjacent years)
- Success validation: every account in the list is a real, intended account;
  no date range crosses the Apr 1 FY boundary unexpectedly

### Step 4: Generate reports (legacy `account` command)
- [ ] Run:
  ```
  account --infile FY{year}/FY{year}.beancount --fy {year} --outdir reports/{year}/
  ```
- [ ] Note: depreciation is computed automatically by
  `dyu_accounting.depreciation.Depreciation` during this step — no separate
  manual depreciation step is needed
- Success validation: command exits without traceback; `reports/{year}/`
  contains `index.html` plus depreciation/P&L/journal/balance-sheet/GST
  report files

### Step 5: Review generated reports
- [ ] Open `reports/{year}/index.html`
- [ ] Spot-check Balance Sheet opening balances match prior year's closing
      balances
- [ ] Spot-check P&L depreciation line matches the depreciation report total
- [ ] Spot-check GST report quarter/period totals against qrmp setting in
      config.json
- Success validation: prior-year closing balance sheet figures equal this
  year's opening figures; no $0 / blank sections that should have data

### Step 6: Troubleshooting
- **`config.json` not found**: legacy `account` command must be run from a
  directory containing `config.json`; raises raw `FileNotFoundError` with no
  custom message — copy/symlink `config.json` into the invocation directory
- **FY boundary issues**: guided mode's reconciliation report (Step 3) is the
  place to catch statements that bleed across Apr 1; fix by re-exporting a
  trimmed statement from the bank/source and re-running guided import for the
  affected importer
- **GST period mismatches**: check `config.json`'s `gst.qrmp` flag matches
  your actual GST filing scheme (QRMP vs monthly) before trusting the GST
  report's period grouping
- **Depreciation looks wrong**: depreciation is automatic from ledger entries
  (see Step 4 note) — if a figure looks wrong, the fix is in the underlying
  asset entries in the ledger, not a manual override step

## See Also
- GUIDED_MODE.md — full guided import walkthrough
- CSV_IMPORT.md — per-importer CSV format reference (TICKET-004)
```

## Researcher Findings

Feasibility confirmed as documentation task. No new CLI command required. Ready for implementation planning.


### Human Approval (2026-10-03)

Approved. Documentation reviewed and accepted.

