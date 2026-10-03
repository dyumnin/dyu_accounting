# TICKET-004: Document CSV parsing workflow and import process

**Status**: closed
**Type**: improvement
**Priority**: high
**Stage**: done
**Created**: 2026-09-29
**Completed**: 2026-10-03
**Parent**: none

## Current State

**Stage**: done. `CSV_IMPORT.md` has been written at the repo root per the Implementation Plan's 7-section outline, sourced from the actual `custom_init()` of all 6 importers (`ICICIBank.py`, `ICICICard.py`, `IDFC.py`, `SBI.py`, `Upworks.py`, `Account.py`), `importer_registry.py`'s discovery mechanism, and `Utilities/__init__.py::generate_import_module_code()` for the current `.import` convention. No source files were modified. Pending explicit human approval before this ticket can move to `done` (per pipeline hard boundary — implementer cannot self-approve even on a no-validation-required ticket).

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

- `CSV_IMPORT.md` (new, repo root, alongside `GUIDED_MODE.md`/`README.md`) — the only file this ticket creates/edits.
- No source files change. `--dry-run`/`--validate` CLI flags and `importers/custom_importer_template.py` from the original Design Notes are dropped — out of scope per Researcher's feasibility note (pure docs; no code changes). CSV_IMPORT.md embeds the custom-importer template inline as a code block instead of a separate skeleton file, since `dyu_accounting/gulp/*.py` auto-discovery (`importer_registry.py::discover_importers()`) requires the file to live in `dyu_accounting/gulp/`, not a generic `importers/` folder — a standalone template file elsewhere would be misleading.

## Implementation Notes

Created `CSV_IMPORT.md` at the repo root with the exact 7-section outline from the Implementation Plan (Overview → Importer Catalogue → Auto-Discovery → Creating a Custom Importer → Manual/Fallback → Reconciliation → See Also):

1. **Overview** — one paragraph positioning guided mode (`GUIDED_MODE.md`) as the primary path, linking to it without restating its workflow/example-session/reconciliation content.
2. **Importer Catalogue** — one 7-column table with exactly 6 rows (ICICIBank, ICICICard, IDFC, SBI, Upworks, Account), values pulled directly from each file's `custom_init()` (re-read all 6 source files to confirm, not copied from GUIDED_MODE.md's stale table). Added one sample-input-row + resulting-posting subsection per importer, calling out each importer's special-case handling (SBI's `petl.rowmap`/`_merge_amount_fragments` lakh-comma fix, ICICICard's comma-stripping + negation, IDFC/ICICIBank's Debit/Withdrawal negation with Credit/Deposit fallback, Account.py's `PAYMENT_ACCOUNT_MAP`/`PURPOSE_ACCOUNT_MAP` per-row routing and `build_metadata` receipt attachment).
3. **Auto-Discovery** — names `importer_registry.py::discover_importers()` and `introspect_importer()`, explains the `pkgutil.iter_modules` + `object.__new__(Importer)` + `custom_init()` mechanism, states the no-registration-step rule.
4. **Creating a Custom Importer** — embeds the Implementation Plan's code template verbatim (csvreader.Importer + banking.Importer, custom_init with filename_pattern_def/column_labels_line/header_identifier/header_map), citing `dyu_accounting/gulp/Account.py` by path, plus the two call-outs (must live under `dyu_accounting/gulp/`; header_identifier specificity) and the one-sentence pointer to `xlsreader`/`xlsxreader` via `ICICIBank.py`/`IDFC.py`.
5. **Manual/Fallback Path** — keyword-arg `.import` example (`Account.Importer(main_account="...")`), explicit caveat that `example/gulp/my.import`'s dict-wrapper style (`Account.Importer({'main_account': ...})`) is outdated, citing `Utilities/__init__.py::generate_import_module_code()` as source of truth, and the `bean-extract -f <module>.import <file>` invocation.
6. **Reconciliation** — links to `GUIDED_MODE.md`'s `## Reconciliation Report` section instead of re-describing it, plus the one-line manual-path reconciliation note (diff posted entry count/totals against source CSV row count/column sum).
7. **See Also** — links to `GUIDED_MODE.md`, `ANNUAL_WORKFLOW.md`, and `README.md`.

No deviations from the Implementation Plan. No source/code files touched; verified with `git status --short` that only `CSV_IMPORT.md` is new/untracked from this change (pre-existing unrelated uncommitted changes to `README.md` and other files from other in-flight tickets are untouched by this work).

Verification commands run:
- `git status --short` — confirmed `CSV_IMPORT.md` is the only file this ticket's work added.
- Manual cross-check of every table/template value in `CSV_IMPORT.md` against the live source: `cat dyu_accounting/gulp/{ICICIBank,ICICICard,IDFC,SBI,Upworks,Account}.py`, `cat dyu_accounting/importer_registry.py`, `cat example/gulp/my.import`, `grep -n generate_import_module_code -A 40 dyu_accounting/Utilities/__init__.py`.

No tests were run — pure documentation, no code paths changed (Validation Required: no).

Per pipeline rules, this ticket is being set to `awaiting-approval` rather than `done`: an implementer cannot self-approve a ticket even when no validation stage applies. Awaiting explicit human sign-off before moving to `TICKETS/closed/` and `done`.

## Testing

Test each CSV type and custom importer with sample data. Verify entries merge cleanly into ledger without duplicates or conflicts.


## Requirements (Researcher-Refined)

### All 6 Importers Documented (from actual source, not stale GUIDED_MODE.md table)

| Importer | File | Format | Filename pattern | Header identifier | Currency | Special handling |
|---|---|---|---|---|---|---|
| ICICI Bank | ICICIBank.py | XLS | `OpTrans.*` | `DETAILED STATEMENT` | INR | Signed amount from Withdrawal/Deposit |
| ICICI Credit Card | ICICICard.py | CSV | `CreditCard` | `"Accountno:"` | INR | Indian comma-formatted amounts, negates debit |
| IDFC Bank | IDFC.py | XLSX | `IDFC.*` | `STATEMENT OF ACCOUNT` | INR | Negates Debit, falls back to Credit |
| SBI Bank | SBI.py | CSV | `SBI` | `Account Name` | INR | Custom petl.rowmap fix for lakh-style commas |
| Upwork | Upworks.py | CSV | `Upworks.*` | `Date` | USD | Straightforward, no sign fixup |
| Account (Google Forms) | Account.py | CSV | `Accounts.*` | `Timestamp,Date,Amount,Purpose,Payment,Receipt` | INR | Payment→source, Purpose→expense via PAYMENT/PURPOSE_ACCOUNT_MAP (TICKET-009) |

**Note**: GUIDED_MODE.md's importer table has stale patterns (SBI/IDFC/Upworks) that don't match actual code — new doc should source from actual `custom_init()`, not copy stale table.

### Dynamic Discovery Mechanism

`importer_registry.py::discover_importers()` walks `dyu_accounting/gulp` via `pkgutil.iter_modules`, requires module-level `Importer` class. **Any new file with a working `custom_init()` is automatically discovered — no registration step needed.**

### Custom Importer Template

`Account.py` is the best reference: subclass `csvreader.Importer` + `banking.Importer`, minimal `custom_init()`, optionally override `get_main_account`/`get_target_account`/`build_metadata` for per-row dynamic routing.

### Manual Fallback Path

`example/gulp/my.import` shows hand-written `.import` module + `bean-extract -f <module>.import <file>` CLI invocation.

**Note**: Use keyword-arg constructor style (`XImport(main_account="...")`, per `Utilities/__init__.py::generate_import_module_code`) as current convention — example file's dict-wrapper style predates this.

### Feasibility: ✅ Pure documentation, no code changes

Scope narrowed from original (generic workflow guide, now covered by guided mode) to: importer format catalogue + custom-importer authoring guide + manual fallback. Don't duplicate GUIDED_MODE.md.

### Acceptance Criteria (impl-planner refined, checkable)

- [ ] `CSV_IMPORT.md` exists at repo root with the 7 sections listed in Implementation Plan's outline, in that order
- [ ] Section 1 contains a link to `GUIDED_MODE.md` and does not restate its `## Workflow Overview`/`## Example Session` content
- [ ] Section 2 table has exactly 6 rows (ICICIBank, ICICICard, IDFC, SBI, Upworks, Account) with columns Importer/Source file/Format/Filename pattern/Header identifier/Currency/Notes, values matching this ticket's Requirements table
- [ ] Section 2 includes one sample input row + resulting beancount posting per importer
- [ ] Section 3 names `importer_registry.py::discover_importers()` and `introspect_importer()` and states the no-registration-needed rule
- [ ] Section 4 contains the exact code template from Implementation Plan (csvreader.Importer + banking.Importer subclass, custom_init with filename_pattern_def/column_labels_line/header_identifier/header_map), citing `dyu_accounting/gulp/Account.py` by path
- [ ] Section 5 shows a keyword-arg-style `.import` module example and the `bean-extract -f <module>.import <file>` command, with an explicit caveat that `example/gulp/my.import`'s dict-wrapper style is outdated
- [ ] Section 6 links to GUIDED_MODE.md's `## Reconciliation Report` section rather than re-describing it, and adds the one-line manual-path reconciliation note
- [ ] No source files are modified by this ticket (`git diff --stat` shows only `CSV_IMPORT.md` added)

## Researcher Findings

Pure documentation task drawing on already-implemented, tested code (TICKET-005-009). No open feasibility risks.


## Implementation Plan (impl-planner)

**Validation Required**: no — pure documentation addition (new `CSV_IMPORT.md`); no behavior, code path, or output changes for any importer or CLI command.

### Exact outline for CSV_IMPORT.md

```
# CSV Import Guide

## 1. Overview
   - One paragraph: guided mode (`GUIDED_MODE.md`) is the primary, recommended
     path for annual-statement import; this doc is the reference/cookbook for
     (a) the importer catalogue, (b) writing a new importer, (c) the manual
     bean-extract fallback. Link to GUIDED_MODE.md, do not restate its
     workflow/CLI/reconciliation-report sections.

## 2. Importer Catalogue
   - One table (sourced from actual custom_init() in each dyu_accounting/gulp/*.py
     file, not GUIDED_MODE.md's stale table):
     | Importer | Source file | Format | Filename pattern | Header identifier | Currency | Notes |
     Rows: ICICIBank, ICICICard, IDFC, SBI, Upworks, Account — values exactly as
     captured in this ticket's Requirements table above.
   - One short subsection per importer (or a merged subsection where trivial)
     giving: a sample input row/line, the resulting beancount posting, and any
     special-case handling called out in the Notes column (e.g. Account.py's
     PAYMENT_ACCOUNT_MAP/PURPOSE_ACCOUNT_MAP routing, SBI's lakh-comma petl
     rowmap fix, ICICICard/IDFC sign negation on Debit).

## 3. How Auto-Discovery Works
   - Explain importer_registry.py::discover_importers(): walks
     dyu_accounting/gulp via pkgutil.iter_modules, imports each non-private
     top-level module, requires a module-level `Importer` class, calls
     custom_init() on a bare `object.__new__(Importer)` instance to pull
     filename_pattern_def / header_identifier / column_labels_line / currency
     for the catalogue/guided-mode picker.
   - State the one hard rule: "any .py file dropped into dyu_accounting/gulp/
     with a working custom_init() and an `Importer` class is auto-discovered —
     no registration step, no edits to importer_registry.py needed."

## 4. Creating a Custom Importer
   - Step-by-step: copy the template below into
     dyu_accounting/gulp/<YourSource>.py, fill in custom_init(), adjust
     header_map, optionally override get_main_account/get_target_account/
     build_metadata for per-row dynamic account routing.
   - Embed the code template (see below) with Account.py cited as the
     real, working reference implementation (link/name the file explicitly:
     dyu_accounting/gulp/Account.py).
   - Note: template subclasses csvreader.Importer + banking.Importer from
     beancount_reds_importers; other reader base classes exist
     (xlsreader/xlsxreader used by ICICIBank.py/IDFC.py respectively) for
     non-CSV sources — one sentence pointing this out with those two files
     as examples, not full worked examples.

## 5. Manual / Fallback Path (bean-extract CLI)
   - Show a minimal hand-written `.import` module using the current
     keyword-arg constructor convention, e.g.:
     ```python
     from dyu_accounting.gulp import Account
     CONFIG = [
         Account.Importer(main_account="Assets:INR:Bank"),
     ]
     ```
   - Note explicitly: example/gulp/my.import predates this convention and
     uses the older dict-wrapper style (`Account.Importer({'main_account': ...})`)
     — do not copy it as-is; cite Utilities/__init__.py::generate_import_module_code
     as the source of truth for the current generated-code shape.
   - Give the CLI invocation: `bean-extract -f <module>.import <file>`.

## 6. Reconciliation
   - One short paragraph + link to GUIDED_MODE.md's "## Reconciliation Report"
     section (reconciliation_FY{year}.txt: transaction counts, accounts
     touched, per-importer stats, date ranges) rather than re-documenting it.
   - One line: for the manual/fallback path (no guided-mode reconciliation
     report generated), reconcile by diffing posted entry count/totals in the
     bean-extract output against source CSV row count/column sum.

## 7. See Also
   - Link to GUIDED_MODE.md and README.md.
```

### Exact code template for "Creating a Custom Importer" (section 4)

Based on `dyu_accounting/gulp/Account.py` (confirmed working pattern):

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

   - Call out: file must live under `dyu_accounting/gulp/` (not a generic
     `importers/` folder) for `importer_registry.py::discover_importers()` and
     guided mode to pick it up automatically.
   - Call out: `header_identifier` is what `identify()` uses to confirm a file
     matches this importer when multiple importers' filename patterns could
     collide — keep it as specific as the real header line.

### Source references for implementer to pull exact details from
- `dyu_accounting/gulp/ICICIBank.py`, `ICICICard.py`, `IDFC.py`, `SBI.py`,
  `Upworks.py`, `Account.py` — one real sample row + custom_init() values each.
- `dyu_accounting/importer_registry.py` — discover_importers()/introspect_importer() for section 3.
- `example/gulp/my.import` — base for section 5, annotated with the caveat above.
- `GUIDED_MODE.md` — section 1 and 6 links/summaries only, do not duplicate its `## Workflow Overview`, `## Example Session`, or `## Reconciliation Report` content.


### Human Approval (2026-10-03)

Approved. Documentation reviewed and accepted.

