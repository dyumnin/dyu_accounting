# Annual Workflow

This is the yearly checklist for a returning user, start to finish, from
chart-of-accounts review through final reports. See GUIDED_MODE.md for the
import step in detail, and CSV_IMPORT.md for per-importer CSV format
reference (TICKET-004).

## Annual Checklist

### Step 1: Review config.json and chart of accounts
- [ ] Confirm `config.json` exists in the directory you will run `account` from
      (legacy report mode fails with an unhandled `FileNotFoundError` if
      missing — see Troubleshooting)
- [ ] Review `company`, `ar`, `exchange_gain`, `cash_accounts`, `gst.qrmp`
      fields for changes this year (new bank accounts, new cash accounts,
      GST scheme change)
- Success validation: `config.json` parses as valid JSON and every account
  referenced in it exists in your chart of accounts for the new FY

### Step 2: Run guided import (`account --guided`)
- [ ] Run `account --guided` to create the FY folder, select importers, place
      statement files, and generate the parent ledger
- (Full walkthrough: see GUIDED_MODE.md — not duplicated here)
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
  `dyu_accounting.depreciation.Depreciation` during this step — there is no
  separate manual depreciation step
- Success validation: command exits without a traceback; `reports/{year}/`
  contains `index.html` plus depreciation/P&L/journal/balance-sheet/GST
  report files

### Step 5: Review generated reports
- [ ] Open `reports/{year}/index.html`
- [ ] Spot-check Balance Sheet opening balances match prior year's closing
      balances
- [ ] Spot-check P&L depreciation line matches the depreciation report total
- [ ] Spot-check GST report quarter/period totals against the `qrmp` setting
      in `config.json`
- Success validation: prior-year closing balance sheet figures equal this
  year's opening figures; no $0 / blank sections that should have data

### Step 6: Troubleshooting
- **`config.json` not found**: the legacy `account` command must be run from
  a directory containing `config.json`; it raises a raw `FileNotFoundError`
  with no custom message if the file is missing. This is expected current
  behavior, not a bug to fix here — copy or symlink `config.json` into the
  invocation directory before running Step 4.
- **FY boundary issues**: guided mode's reconciliation report (Step 3) is the
  place to catch statements that bleed across Apr 1; fix by re-exporting a
  trimmed statement from the bank/source and re-running guided import for the
  affected importer
- **GST period mismatches**: check `config.json`'s `gst.qrmp` flag matches
  your actual GST filing scheme (QRMP vs monthly) before trusting the GST
  report's period grouping
- **Depreciation looks wrong**: depreciation is computed automatically from
  ledger entries (see Step 4 note) — if a figure looks wrong, the fix is in
  the underlying asset entries in the ledger, not a manual override step

## See Also
- GUIDED_MODE.md — full guided import walkthrough
- CSV_IMPORT.md — per-importer CSV format reference (TICKET-004)
