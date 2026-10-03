# Configuration Reference (config.json)

## Overview

`config.json` is loaded from the current working directory in **legacy mode
only** — i.e. when `account` is invoked without `--guided`
(`dyu_accounting/__init__.py:60-61`, inside `accounting()`). It is a plain
JSON file read with `json.load()` before any other CLI arguments are
processed; it holds the company identity, account-mapping, and GST
settings used across all report generators (balance sheet, P&L, GST,
journal, exchange-gain).

## Field Reference

| Field | Type | Required | Default | Source (file:line) | Description |
|---|---|---|---|---|---|
| `format` | string | No | `"html"` | `dyu_accounting/Utilities/__init__.py:67` | Template set used for report rendering: one of `tex`, `md`, `adoc`, `html` |
| `company.name` | string | Yes* | none | `balance_sheet`, `pnl`, `gst`, `journal` (via `cfg['company']`) | Company name shown in report headers/titles |
| `company.address` | string | Yes* | none | `balance_sheet`, `pnl`, `gst`, `journal` (via `cfg['company']`) | Company address shown in report headers |
| `ar` | string (account) | Yes* | none | `dyu_accounting/exchange_gain/__init__.py:34` | Beancount account receivable used when posting forex entries |
| `exchange_gain` | string (account) | Yes* | none | `dyu_accounting/exchange_gain/__init__.py:36` | Beancount account for forex exchange gain/loss postings |
| `cash_accounts` | list[string] | Yes* | none | `dyu_accounting/journal/__init__.py:22` | Accounts included in the cashbook/journal report |
| `gst.qrmp` | boolean | Yes* | none | `dyu_accounting/gst/__init__.py:19` | Whether GST is filed under the Quarterly Return Monthly Payment (QRMP) scheme |

`*` = accessed via an unguarded `cfg['key']` lookup (no `.get()` fallback)
— if the key is missing, `accounting()` raises a bare `KeyError`. There is
currently no `--validate-config` option to catch this ahead of time (see
`config.schema.json` below for future tooling in this direction).

`company` and `gst` are nested objects; their sub-fields are JSON-nested,
not dotted keys on disk:

```json
{
    "company": {
        "name": "...",
        "address": "..."
    },
    "gst": {
        "qrmp": true
    }
}
```

## CLI-Supplied Values (NOT config.json fields)

The following are injected into the in-memory `cfg` dict at runtime from
CLI arguments or internal state. They must **not** be added to
`config.json` — they have no effect there and are not read from the file:

- `fy` — from `--fy` (required CLI argument, the financial year to report on)
- `outdir` — from `--outdir` (CLI argument, defaults to `"Output"`)
- `texwriter` — internal file handle set up by `mkWriter(cfg)`; never user-set

## Scope Boundaries

### config.json vs .guided-config.json

`config.json` is the **global, legacy-mode** configuration file: one file
per repository checkout, read from the current working directory,
controlling report formatting, company identity, GST, and forex accounts
for the classic (non-guided) `account` CLI invocation.

`.guided-config.json` is a **per-financial-year, guided-mode** file,
written inside each `FYyyyy_yy/` folder by `account --guided`. It
remembers importer-to-account mappings so the next year's guided run can
pre-select the same choices. See
[GUIDED_MODE.md](GUIDED_MODE.md) for its structure and workflow.

These two files are disjoint in purpose and in keys — there is no overlap
or conflict between them.

### Not config.json: chart-of-accounts & depreciation

Chart-of-accounts classification (e.g. the `balance_sheet: "attribute"`
metadata) and the depreciation category table are **not** configured in
`config.json`. They are set as **beancount account metadata** directly in
the ledger file. See [README.md](README.md) for how to annotate accounts
with this metadata.

## Example

```json
{
    "format": "html",
    "company": {
        "name": "ABC Private Limited",
        "address": "1, XYZ Lane, Rampura  560001"
    },
    "ar": "Assets:INR:AccountReceivable",
    "exchange_gain": "Assets:INR:ExchangeGain",
    "cash_accounts": [
        "Assets:INR:Bank:Current",
        "Income:Customer:C"
    ],
    "gst": {
        "qrmp": true
    }
}
```

This exact template is available as [`config.json.example`](config.json.example)
— copy it to `config.json` and edit the placeholder values for your
company.

## Schema

A machine-readable JSON Schema is available at
[`config.schema.json`](config.schema.json) for editor autocompletion / future
`--validate-config` tooling.
