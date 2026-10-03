# Setup Guide

From zero to your first financial report.

## Prerequisites

- Python `>=3` (this project does not require a specific minor version; see `pyproject.toml`).
- Basic double-entry accounting familiarity is assumed. No prior experience with beancount syntax is required — this guide introduces the pieces you need as you go.

## Installation

```
pip3 install dyu_accounting
```

For the latest, untested version, install from this git repo instead:

```
git clone <repo name>
cd <repo name>
pip install .
```

## Folder Structure

Before running anything, set up a working directory like this:

```
my-company/
├── config.json
├── accounts.beancount      (chart of accounts + opening entries)
└── ledger.beancount        (transactions; includes accounts.beancount)
```

**Important**: `config.json` must exist in the directory you invoke the `account` command from. The tool opens it with a bare `open("config.json", ...)` call — if it's missing, you'll get an unhandled `FileNotFoundError`. See [Common Mistakes & Troubleshooting](#common-mistakes--troubleshooting) below.

## Step 1: Create Your Chart of Accounts

Every account you want to appear on your Balance Sheet needs a `balance_sheet: "<category>"` metadata line on its `open` directive. Without it, the account is silently excluded from the Balance Sheet.

**Before** (a plain beancount `open`, no metadata):

```
2018-07-01 open Assets:INR:Cash              INR
```

**After** (with the required metadata, from `example/accounts.beancount`):

```
2018-07-01 open Assets:INR:Cash              INR
	balance_sheet: "assets.cash"
```

Depreciable assets additionally need a `depreciation_category:` metadata value, matching one of six hardcoded categories: `Furniture`, `OfficeEquipment`, `Phone`, `Server`, `Laptop`, `Electrical`. For example:

```
2018-07-01 open Assets:INR:Equipment:Furniture              INR
	balance_sheet: "assets.tangible"
	depreciation_category: "Furniture"
```

The full list of valid `balance_sheet:` attribute values (and the depreciation rate table for each category) is already documented in [README.md's "Setting up your chart of accounts" section](README.md#setting-up-your-chart-of-accounts-for-use-with-this-package) — refer there rather than duplicating it here.

Use `example/accounts.beancount` as a complete reference chart of accounts to copy from and adapt.

## Step 2: Create config.json

At minimum, a first report needs these fields:

| Field             | Purpose                                                        |
| ----------------- | ---------------------------------------------------------------|
| `format`          | Output report format (`md`, `html`, or `tex` — see note below) |
| `company.name`    | Your company's legal name, printed on reports                  |
| `company.address` | Your company's registered address, printed on reports          |
| `ar`              | Account used for Accounts Receivable                           |
| `exchange_gain`   | Account used to post foreign exchange gain/loss                |
| `cash_accounts`   | List of accounts treated as cash-equivalent for reporting       |
| `gst.qrmp`        | Whether you're enrolled in the GST QRMP scheme (`true`/`false`)|

Full worked example (from `example/config.json`):

```json
{
	"format":"tex",
	"company":{
		"name":"ABC Private Limited",
		"address":"1, XYZ Lane, Rampura  560001"
	},
	"ar":"Assets:INR:AccountReceivable",
	"exchange_gain":"Assets:INR:ExchangeGain",
	"cash_accounts":[
		"Assets:INR:Bank:Current",
		"Income:Customer:C"
		],
		"gst":{
			"qrmp":true
		}
}
```

**Note on `format`**: `"format": "tex"` only writes a `.tex` file — nothing in this codebase invokes `pdflatex`, so you will **not** get a PDF unless you separately install and run a LaTeX toolchain. For your first report, use `"format": "md"` or `"format": "html"` instead — both are dependency-free. Treat `tex` as an advanced/optional path.

A full config.json field reference is planned separately (see TICKET-002 / `CONFIG.md`, once available) — this section only covers what you need for a first report.

## Step 3: Enter Your First Transactions

Add a transaction to `ledger.beancount` (which should `include` your `accounts.beancount`) referencing accounts you opened in Step 1:

```
include "accounts.beancount"

2024-04-01 * "Initial capital contribution"
	Assets:INR:Bank:Current       100000.00 INR
	Equity:INR:ShareCapital       -100000.00 INR
```

## Step 4: Generate Your First Report

### Guided mode (recommended for importing bank/card statements)

```
account --guided
```

This walks you interactively through selecting a financial year, picking importers for your bank/card statements, and generating a parent ledger plus a reconciliation report. See [GUIDED_MODE.md](GUIDED_MODE.md) for full detail.

**Guided mode does not create your chart of accounts or `config.json`** — those are Steps 1–2 above, and are still required before `--guided` (or any report generation) will work.

### Manual / legacy mode

Once you have a ledger and `config.json` in place, generate reports directly:

```
mkdir -p reports/2019
account --infile ledger.beancount --fy 2019 --outdir reports/2019/
```

- `--infile` (required) — path to your ledger file.
- `--fy` (required) — financial year, e.g. `2019` (starts 1st April).
- `--outdir` (optional) — output folder; defaults to `Output` if omitted.

## Common Mistakes & Troubleshooting

- **`FileNotFoundError` on startup** — `config.json` is missing from the current directory. Run `account` from the folder that contains `config.json` (see [Folder Structure](#folder-structure)).
- **Account missing from the Balance Sheet** — the account's `open` directive is missing `balance_sheet:` metadata. Add it per [Step 1](#step-1-create-your-chart-of-accounts).
- **`unrecognized arguments` error** — you're using the old `--in`/`--out` flag names. The correct flags are `--infile` and `--outdir` (this was a historical documentation bug, now fixed here and in README.md).
- **Depreciation not calculated for an asset** — `depreciation_category` value doesn't exactly match one of the six valid categories (`Furniture`, `OfficeEquipment`, `Phone`, `Server`, `Laptop`, `Electrical`). Matching is case-sensitive.
- **`"format": "tex"` produces no PDF** — this is expected; the tool only writes the `.tex` file. Use `md` or `html` instead, or install a LaTeX toolchain separately to render the `.tex` file yourself.

## Next Steps

- [GUIDED_MODE.md](GUIDED_MODE.md) — full detail on the annual guided import/re-import workflow.
- TICKET-002 / `CONFIG.md` — full `config.json` field reference (once available).
