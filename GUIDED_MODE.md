# Guided Mode for Annual Statement Import

Guided mode provides an interactive workflow for importing annual bank statements and generating parent ledgers with reconciliation reports.

## Indian Financial Year Format

This tool uses the Indian Financial Year (FY) format, which runs from April to March. FY2025_26 represents the financial year from April 2025 to March 2026.

**Input Formats Accepted**:
- `2025-26` (hyphen-separated)
- `2025_26` (underscore-separated)
- `202526` (6-digit compact, no separator)

All formats normalize internally to `YYYY_YY` format (e.g., `2025_26`).

## Workflow Overview

The guided mode walks you through each step of the import process:

```
account --guided
├─ Financial year selection (accepts 2025-26, 2025_26, or 202526)
├─ Folder structure creation
├─ Importer selection (with pre-selection from previous year)
├─ File validation (filename pattern + header identifier)
├─ Import module generation
├─ Bean-extract invocation
├─ Parent ledger generation
├─ Reconciliation report generation
└─ Config persistence for next year
```

## File Structure

After running `account --guided` for FY2025_26, the following structure is created:

```
FY2025_26/
├── .guided-config.json              ← Importer selections and accounts (reused next year)
├── imports/                         ← You place your CSV/XLS files here
│   ├── icici_bank/                  (filename pattern: OpTrans*)
│   ├── icici_card/                  (filename pattern: CreditCard*)
│   ├── idfc_bank/                   (filename pattern: Statement*)
│   ├── sbi_bank/                    (filename pattern: Bnk*)
│   ├── upworks/                     (filename pattern: Earnings*)
│   └── account/                     (filename pattern: Manual*)
├── intermediate/                    ← Generated intermediate ledgers (one per file)
│   ├── icici_bank_OpTrans_2025_26_01.beancount
│   ├── icici_bank_OpTrans_2025_26_02.beancount
│   ├── icici_card_CreditCard_2025_26_01.beancount
│   └── ...
├── FY2025_26.import                 ← Auto-generated importer module for bean-extract
├── FY2025_26.beancount              ← Parent ledger (imports all intermediates)
└── reconciliation_FY2025_26.txt     ← Summary report
```

## Supported Importers

Guided mode supports 6 bank statement formats:

| Importer | Format | Filename Pattern | Sample Header |
|----------|--------|------------------|---------------|
| ICICI Bank | XLS | OpTrans* | DETAILED STATEMENT |
| ICICI Card | CSV | CreditCard* | Accountno: |
| IDFC Bank | CSV | Statement* | ValueDate |
| SBI Bank | CSV | Bnk* | Transaction |
| Upwork Earnings | CSV | Earnings* | Date |
| Manual Account | CSV | Manual* | Entry |

## Pre-selection Memory

When you run guided mode for a new year, it automatically loads your importer selections from the previous year:

```
Use same importers as FY2024_25? (Y/n): 
```

Answer `Y` to use the same importers, or `n` to select manually.

## Example Session

```
$ account --guided

Enter financial year (e.g., 2025-26, 2025_26, or 202526): 2025-26

Preparing guided import for FY 2025_26...
Created folder structure: FY2025_26/

Found 6 importers available

Importers used in FY2024_25:
  - ICICI Bank Importer
  - ICICI Bank Credit Card Importer

Use same importers as FY2024_25? (Y/n): Y

Selected 2 importers

ICICI Bank Importer:
  Filename pattern: OpTrans
  Format: CSV/XLS
  Place files in: FY2025_26/imports/icici_bank/
  Sample header: DETAILED STATEMENT
  Ready? Place files in FY2025_26/imports/icici_bank/ then press Enter (or 's' to skip): 
  [user places files and presses Enter]
  ✓ All 2 files validated successfully

ICICI Bank Credit Card Importer:
  Filename pattern: CreditCard
  Format: CSV/XLS
  Place files in: FY2025_26/imports/icici_card/
  Sample header: Accountno:
  Ready? Place files in FY2025_26/imports/icici_card/ then press Enter (or 's' to skip): 
  [user places files and presses Enter]
  ✓ All 1 file validated successfully

Generated import module: FY2025_26.import

Enter account for ICICI Bank Importer:
  Example: Assets:Bank:INR
  Account: Assets:Bank:ICICI:INR

Enter account for ICICI Bank Credit Card Importer:
  Example: Assets:Bank:INR
  Account: Liabilities:CreditCard:ICICI

Running bean-extract for 3 files...
✓ Generated 3 intermediate ledgers

Generated parent ledger: FY2025_26/FY2025_26.beancount
Generated reconciliation report: FY2025_26/reconciliation_FY2025_26.txt

Guided import complete!
  Parent ledger: FY2025_26/FY2025_26.beancount
  Reconciliation: FY2025_26/reconciliation_FY2025_26.txt
```

## Reconciliation Report

The generated `reconciliation_FY2025_26.txt` contains:

- Total transaction count across all importers
- Accounts touched during import
- Per-importer statistics:
  - Transaction count
  - Date range (earliest to latest)
  - Number of unique accounts
- Complete list of all accounts

## Parent Ledger

The generated `FY2025_26.beancount` includes all intermediate ledgers in alphabetical order:

```beancount
;; FY 2025_26 Parent Ledger
;; Automatically generated - do not edit

include "FY2025_26/intermediate/account_Accounts_2025_26_01.beancount"
include "FY2025_26/intermediate/icici_bank_OpTrans_2025_26_01.beancount"
include "FY2025_26/intermediate/icici_bank_OpTrans_2025_26_02.beancount"
include "FY2025_26/intermediate/icici_card_CreditCard_2025_26_01.beancount"
include "FY2025_26/intermediate/idfc_bank_IDFC_2025_26_01.beancount"
include "FY2025_26/intermediate/sbi_bank_Bnk_2025_26_01.beancount"
```

## Configuration

User selections are saved to `.guided-config.json` for automatic pre-selection next year:

```json
{
  "ICICIBank": "Assets:Bank:ICICI:INR",
  "ICICICard": "Liabilities:CreditCard:ICICI",
  "IDFC": "",
  "SBI": "",
  "Upworks": "",
  "Account": ""
}
```

Empty values indicate an importer was not used. Remove unwanted entries or add new ones to adjust selections for the next year.

## File Validation

Each file is validated against:

1. **Filename pattern**: Must contain the importer's pattern (e.g., "OpTrans" for ICICI Bank)
2. **Header identifier**: Must contain the importer's header (e.g., "DETAILED STATEMENT" for ICICI Bank)

If validation fails, you'll see:

```
Validation failed for OpTrans_2026_01.xls:
  - Filename pattern 'OpTrans' not found in filename
  - Header identifier 'DETAILED STATEMENT' not found in file

Fix files and press Enter to retry (or 's' to skip): 
```

Fix the file and press Enter to retry, or press `s` to skip it.

## Backward Compatibility

The legacy `account` command still works:

```bash
account --in ledger.beancount --fy 2026 --out reports/
```

This is unchanged and continues to generate reports as before.

## Troubleshooting

### File validation keeps failing

- Check filename matches the pattern exactly (e.g., "OpTrans_2026.xlsx" for ICICI Bank)
- Open the file in a text editor and search for the header identifier
- Ensure the file is from the correct bank/importer

### Account syntax error

When prompted for an account, use standard beancount account syntax:

- Correct: `Assets:Bank:ICICI:INR`
- Incorrect: `Assets/Bank/ICICI/INR`

Accounts must:
- Start with an account type (Assets, Liabilities, Equity, Income, Expenses)
- Use colons (:) as separators
- Use only letters, numbers, and hyphens

### No files found in import folder

The workflow pauses at the importer validation step waiting for you to place files:

```
Ready? Place files in FY2025_26/imports/icici_bank/ then press Enter (or 's' to skip):
```

- Navigate to `FY2025_26/imports/{bank_name}/` in your file explorer
- Copy bank statement files there
- Return to the terminal and press Enter

### Parent ledger includes wrong files

The parent ledger sorts includes alphabetically by filename. If ordering matters:

- Edit `.guided-config.json` or generated intermediate filenames
- Or manually edit `FY2025_26/FY2025_26.beancount` to reorder includes

## Best Practices

1. **Organize files by year**: Keep FY2024_25 and FY2025_26 statements in separate folders
2. **Rename statements consistently**: Use the expected pattern (e.g., "OpTrans_2025_26.xlsx")
3. **Run annually**: Re-run guided mode for each fiscal year to maintain pre-selected importers
4. **Review reconciliation**: Always check `reconciliation_FY2025_26.txt` for unexpected transactions
5. **Validate before merging**: Keep intermediate ledgers separate until manual review is complete

## CLI Reference

```bash
# Start guided import workflow
account --guided

# When prompted, enter financial year as:
#   - 2025-26 (hyphen-separated)
#   - 2025_26 (underscore-separated)
#   - 202526 (6-digit compact)

# Legacy report generation (still supported)
account --in ledger.beancount --fy 2026 --out reports/
```

## See Also

- Beancount documentation: https://beancount.io/
- Bean-extract usage: `bean-extract --help`
- Bean-identify usage: `bean-identify --help`
