# CSV Import Guide

## 1. Overview

This document is the reference and cookbook for CSV/XLS/XLSX import in this
repo: the catalogue of built-in importers, how auto-discovery finds them, how
to write a new importer, and the manual `bean-extract` fallback for when you
don't want to go through guided mode. For the primary, recommended workflow
for importing a full financial year's worth of statements, see
**[GUIDED_MODE.md](GUIDED_MODE.md)** — it drives `account --guided`, which
discovers importers, prompts for files/accounts, runs extraction, and
generates a reconciliation report for you. This document does not restate
that workflow, its example session, or its CLI reference; read it here only
for catalogue/authoring/fallback details.

## 2. Importer Catalogue

All importers live under `dyu_accounting/gulp/` and are built on top of
[`beancount_reds_importers`](https://github.com/redstreet/beancount_reds_importers)
reader/transaction-builder base classes. Values below are taken directly from
each importer's `custom_init()`.

| Importer | Source file | Format | Filename pattern | Header identifier | Currency | Notes |
|---|---|---|---|---|---|---|
| ICICI Bank | `dyu_accounting/gulp/ICICIBank.py` | XLS | `OpTrans.*` | `DETAILED STATEMENT` | INR | Signed amount derived from Withdrawal/Deposit columns |
| ICICI Credit Card | `dyu_accounting/gulp/ICICICard.py` | CSV | `CreditCard` | `"Accountno:"` | INR | Parses Indian comma-formatted amounts (e.g. `1,23,456.78`), negates debit |
| IDFC Bank | `dyu_accounting/gulp/IDFC.py` | XLSX | `IDFC.*` | `STATEMENT OF ACCOUNT` | INR | Negates Debit, falls back to Credit when Debit is absent/zero |
| SBI Bank | `dyu_accounting/gulp/SBI.py` | CSV | `SBI` | `Account Name` | INR | Custom `petl.rowmap` fix re-joins amount fields split by unquoted lakh-style commas |
| Upwork | `dyu_accounting/gulp/Upworks.py` | CSV | `Upworks.*` | `Date` | USD | Straightforward column mapping, no sign fixup |
| Account (Google Forms) | `dyu_accounting/gulp/Account.py` | CSV | `Accounts.*` | `Timestamp,Date,Amount,Purpose,Payment,Receipt` | INR | Per-row double-entry routing: `Payment` column picks the source/credit account, `Purpose` column picks the expense/debit account, via `PAYMENT_ACCOUNT_MAP`/`PURPOSE_ACCOUNT_MAP` (see TICKET-009) |

### ICICI Bank (`ICICIBank.py`)

Sample input row (`OpTrans*.xls`, columns per `column_labels_line`):

```
S No.=1, Value Date=01/04/2025, Transaction Remarks=ATM WDL, Withdrawal Amount (INR )=5000, Deposit Amount (INR )=, Balance (INR )=45000
```

Resulting posting (withdrawal negated):

```beancount
2025-04-01 * "" "ATM WDL"
  Assets:INR:Bank:ICICI  -5000.00 INR
  Expenses:Uncategorized  5000.00 INR
```

### ICICI Credit Card (`ICICICard.py`)

Sample input row:

```
Date=01-Apr-25, Sr.No.=1, Transaction Details=AMAZON, Amount(in Rs)=1,234.50
```

The importer strips the Indian comma grouping (`1,234.50` → `1234.50`) and
negates the amount (CSV debits are positive, credits are negative; beancount
convention is the opposite):

```beancount
2025-04-01 * "" "AMAZON"
  Liabilities:INR:CreditCard  -1234.50 INR
  Expenses:Uncategorized       1234.50 INR
```

### IDFC Bank (`IDFC.py`)

Sample input row:

```
Value Date=01-Apr-2025, Particulars=NEFT TRANSFER, Debit=2000, Credit=, Balance=48000
```

Debit is negated; if Debit is blank/zero, Credit is used as-is:

```beancount
2025-04-01 * "" "NEFT TRANSFER"
  Assets:INR:Bank:IDFC  -2000.00 INR
  Expenses:Uncategorized  2000.00 INR
```

### SBI Bank (`SBI.py`)

Sample input row (note the unquoted lakh-style comma, which an ordinary CSV
parser would split into extra fields — `_fix_split_amounts`/`_merge_amount_fragments`
re-join them before the amount is computed):

```
Txn Date=01 Apr 2025, Description=UPI/TRANSFER, Debit=1,770.00, Credit=, Balance=50,000.00
```

```beancount
2025-04-01 * "" "UPI/TRANSFER"
  Assets:INR:Bank:SBI    -1770.00 INR
  Expenses:Uncategorized  1770.00 INR
```

### Upwork (`Upworks.py`)

Sample input row:

```
Date=Apr 01, 2025, Description=Fixed Price, Amount=500.00, Balance=1500.00
```

```beancount
2025-04-01 * "" "Fixed Price"
  Assets:USD:Upwork  500.00 USD
  Income:Uncategorized  -500.00 USD
```

### Account / Google Forms (`Account.py`)

Sample input row:

```
Timestamp=2025-04-01 10:00:00, Date=01/04/2025, Amount=500, Purpose=Food, Payment=Cash, Receipt=https://...
```

`Payment=Cash` → `Assets:INR:Cash:CashInHand` (source), `Purpose=Food` →
`Expenses:Food` (target), via `PAYMENT_ACCOUNT_MAP`/`PURPOSE_ACCOUNT_MAP`
(unmatched values fall back to `Assets:Uncategorized` /
`Expenses:Uncategorized` respectively); the `Receipt` column is attached as
transaction metadata by an overridden `build_metadata()`:

```beancount
2025-04-01 * "" "Food"
  meta: receipt: "https://..."
  Assets:INR:Cash:CashInHand  -500.00 INR
  Expenses:Food                500.00 INR
```

## 3. How Auto-Discovery Works

Guided mode (and any other code that needs to enumerate available importers)
uses `dyu_accounting/importer_registry.py`, specifically:

- `discover_importers()` walks `dyu_accounting/gulp/` with
  `pkgutil.iter_modules`, imports every non-private top-level module in that
  package, and for each module that defines an `Importer` class, calls
  `introspect_importer(module_name, module)`.
- `introspect_importer()` creates a bare instance via
  `object.__new__(Importer)` (skipping `__init__`), calls `custom_init()` on
  it, and reads off `filename_pattern_def`, `header_identifier`,
  `column_labels_line`, and `currency` (plus `IMPORTER_NAME`) to build an
  `ImporterMetadata` record used by the catalogue/guided-mode picker.

**The rule this gives you**: any `.py` file dropped into
`dyu_accounting/gulp/` that defines a module-level `Importer` class with a
working `custom_init()` is automatically discovered — there is no
registration step, and `importer_registry.py` itself never needs editing.

## 4. Creating a Custom Importer

To add support for a new CSV source:

1. Create a new file under `dyu_accounting/gulp/`, e.g.
   `dyu_accounting/gulp/YourSource.py`.
2. Subclass `csvreader.Importer` and `banking.Importer` (or another reader
   base class — see the note below) and fill in `custom_init()`.
3. Optionally override `get_main_account`/`get_target_account`/
   `build_metadata` if the source/target account or extra metadata needs to
   be derived per-row rather than fixed per imported file.

`dyu_accounting/gulp/Account.py` is the best real, working reference for
this pattern (per-row dynamic account routing via `PAYMENT_ACCOUNT_MAP`/
`PURPOSE_ACCOUNT_MAP`, metadata attachment via `build_metadata`). The
template below follows it:

```python
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Your Source Name"

    def custom_init(self):
        self.currency = 'INR'  # or 'USD', etc.
        self.filename_pattern_def = 'YourSource.*'  # regex matched against filename
        self.column_labels_line = 'Col1,Col2,Col3'  # exact CSV header line, used to locate the header row
        self.header_identifier = 'Col1,Col2,Col3'   # string/regex identifying this file type (checked by identify())
        self.date_format = '%d/%m/%Y'
        self.header_map = {
            'Col1': 'date',
            'Col2': 'memo',
            'Col3': 'amount',
        }
        # self.skip_transaction_types = [...]  # optional, see Account.py

    # Optional: override when the source/target account is fixed per file
    # (the default) vs. derived per-row from a column (see Account.py's
    # get_main_account/get_target_account for the per-row pattern, driven by
    # self.config["main_account"] otherwise).

    # Optional: override build_metadata() to attach extra fields (e.g. a
    # receipt URL/id column) as beancount metadata — see Account.py.
```

Notes:

- The file **must** live under `dyu_accounting/gulp/` (not a generic
  `importers/` folder) for `importer_registry.py::discover_importers()` and
  guided mode to pick it up automatically — see section 3.
- `header_identifier` is what `identify()` uses to confirm a file actually
  matches this importer when multiple importers' `filename_pattern_def`
  values could otherwise collide; keep it as specific as the real header
  line (or a unique substring of the file, as ICICICard.py does with
  `"Accountno:"`).
- The template above subclasses `csvreader.Importer`. For non-CSV sources,
  other reader base classes exist — `xlsreader.Importer` (used by
  `ICICIBank.py`) for legacy `.xls` files, and `xlsxreader.Importer` (used by
  `IDFC.py`) for `.xlsx` files — the rest of the pattern (custom_init,
  header_map, optional per-row overrides) is the same.

## 5. Manual / Fallback Path (bean-extract CLI)

If you don't want to go through guided mode, you can write a `.import`
module by hand and run `bean-extract` directly. Every importer here
subclasses `beancount_reds_importers`' `banking.Importer`, whose
`__init__(self, config)` takes a single positional config **dict** — it does
not accept `main_account` as a keyword argument. The convention, matching
what `Utilities/__init__.py::generate_import_module_code()` generates for
guided mode, is:

```python
from dyu_accounting.gulp import Account

CONFIG = [
    Account.Importer({"main_account": "Assets:INR:Bank"}),
]
```

**Caveat**: do not write `Account.Importer(main_account="Assets:INR:Bank")`
(keyword-argument style) — it compiles fine but raises
`TypeError: Importer.__init__() got an unexpected keyword argument
'main_account'` at run time, since none of these importer classes override
`__init__` to accept keyword arguments.

Run it with:

```sh
bean-extract -f <module>.import <file>
```

## 6. Reconciliation

For the guided-mode path, reconciliation is handled for you: see
[GUIDED_MODE.md's "## Reconciliation Report"](GUIDED_MODE.md#reconciliation-report)
section for what `reconciliation_FY{yyyy}_{yy}.txt` contains (transaction
counts, accounts touched, per-importer stats, date ranges).

For the manual/fallback path above, no reconciliation report is generated
automatically — reconcile by diffing the posted entry count/totals in the
`bean-extract` output against the source CSV's row count/column sum.

## 7. See Also

- [GUIDED_MODE.md](GUIDED_MODE.md) — the primary, recommended import workflow
  (`account --guided`), its CLI reference, and the reconciliation report
  format.
- [ANNUAL_WORKFLOW.md](ANNUAL_WORKFLOW.md) — the broader annual close
  workflow this import step feeds into.
- [README.md](README.md) — repo overview and setup.
