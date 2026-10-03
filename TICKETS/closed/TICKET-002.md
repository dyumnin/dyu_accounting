# TICKET-002: Document config.json schema and options

**Status**: closed
**Type**: improvement
**Priority**: medium
**Stage**: done
**Created**: 2026-09-29
**Completed**: 2026-10-03
**Parent**: none

## Problem / Motivation

`config.json` is loaded in `__init__.py` but no documentation exists describing what fields are required, what they mean, or what valid values are. Users must reverse-engineer by reading code or examining example. This is error-prone and frustrating.

## Acceptance Criteria

- [ ] `CONFIG.md` exists at repo root with the outline in Design Notes: Overview, Field Reference table, CLI-Supplied Values, Scope Boundaries, Example, Schema pointer
- [ ] Field Reference table lists all 7 fields (`format`, `company.name`, `company.address`, `ar`, `exchange_gain`, `cash_accounts`, `gst.qrmp`) each with type, required Y/N, default, file:line source, and description
- [ ] CONFIG.md explicitly states `fy`/`outdir`/`texwriter` are CLI-supplied or internal, never config.json fields
- [ ] CONFIG.md explicitly distinguishes config.json (global/legacy) from .guided-config.json (per-FY/guided), with a cross-link to GUIDED_MODE.md
- [ ] CONFIG.md explicitly notes chart-of-accounts/depreciation are beancount account metadata, not config.json, with a cross-link to README.md
- [ ] `config.json.example` exists at repo root as valid, directly-loadable JSON containing all 7 fields with realistic placeholder values
- [ ] `config.schema.json` exists at repo root as valid JSON Schema (draft-07) encoding type/required constraints for all 7 fields
- [ ] Manual spot-check: `json.load(open("config.json.example"))` succeeds and the result satisfies every unguarded `cfg['key']` lookup CONFIG.md documents (no KeyError)

## Design Notes

Create `CONFIG.md` in root and provide a commented template config.json. Consider adding a `--validate-config` CLI option to help users catch config errors early. (Future work — not in this ticket's scope; see Files Affected.)

**Validation Required**: no — pure documentation/reference-file addition; no code or behavior changes, nothing to empirically test. `## Testing` below is reduced to a manual spot-check, not an automated suite.

### Implementation Plan (impl-planner, 2026-10-02)

**1. `CONFIG.md` outline** (root-level, markdown, follow `GUIDED_MODE.md` heading style — `#`/`##`, fenced code blocks for JSON/paths):

```
# Configuration Reference (config.json)

## Overview
  - one paragraph: config.json is loaded from CWD in legacy mode only
    (dyu_accounting/__init__.py:60-61, inside accounting(), triggered
    when --guided is NOT passed)

## Field Reference
  - table: | Field | Type | Required | Default | Source (file:line) | Description |
  - one row per each of the 7 fields (format, company.name, company.address,
    ar, exchange_gain, cash_accounts, gst.qrmp) — copy content directly from
    ticket's "All 7 Config Fields" table above (Design Notes/Requirements
    section already has the exact file:line references, no re-research needed)
  - nested fields (company.name, company.address, gst.qrmp) shown as
    dotted-path rows under their parent key's JSON shape, with a small
    JSON snippet showing the nesting

## CLI-Supplied Values (NOT config.json fields)
  - explicit subsection listing `fy` (from --fy), `outdir` (from --outdir,
    default "Output"), `texwriter` (internal, never user-set) — state
    plainly these must NOT be added to config.json

## Scope Boundaries
  - subsection: "config.json vs .guided-config.json" — one paragraph each,
    cross-link to GUIDED_MODE.md (global/legacy vs per-FY/guided, disjoint keys)
  - subsection: "Not config.json: chart-of-accounts & depreciation" — these
    are beancount account metadata (balance_sheet: "attribute", depreciation
    category), documented in README.md, not config.json — one-line pointer
    + cross-link to README.md

## Example
  - fenced ```json block, full contents of config.json.example (see below)

## Schema
  - one line: "A machine-readable JSON Schema is available at
    config.schema.json for editor autocompletion / future
    `--validate-config` tooling."
```

**2. `config.json.example` content** — JSON has no comment syntax, so this
file stays valid, directly-usable JSON (copy-paste ready), matching the
style already used in `example/config.json`. Annotation/documentation
lives in CONFIG.md's Field Reference table, not inline in this file.
Exact contents:

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

(`format` set to `"html"` here, the coded default per
Utilities/__init__.py:67, to make the example a working drop-in default —
CONFIG.md documents `"tex"`/`"md"`/`"adoc"` as the other valid values.)

**3. `config.schema.json`** — root-level, JSON Schema draft-07,
`additionalProperties: false` at the top level (config.json should only
ever contain these 7 fields' structure), `required` listing the 6
unguarded-lookup fields (`format` excluded from required — it has a coded
`.get()`-style default):

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "dyu_accounting config.json",
    "type": "object",
    "properties": {
        "format": { "type": "string", "enum": ["tex", "md", "adoc", "html"], "default": "html" },
        "company": {
            "type": "object",
            "properties": {
                "name": { "type": "string" },
                "address": { "type": "string" }
            },
            "required": ["name", "address"]
        },
        "ar": { "type": "string" },
        "exchange_gain": { "type": "string" },
        "cash_accounts": { "type": "array", "items": { "type": "string" } },
        "gst": {
            "type": "object",
            "properties": {
                "qrmp": { "type": "boolean" }
            },
            "required": ["qrmp"]
        }
    },
    "required": ["company", "ar", "exchange_gain", "cash_accounts", "gst"],
    "additionalProperties": false
}
```

This schema is reference/tooling scaffolding only in this ticket — wiring
it into a `--validate-config` CLI flag is explicitly future work, not
built here.

## Files Affected

- `CONFIG.md` — new, root-level configuration reference (see outline below)
- `config.json.example` — new, root-level valid-JSON template (all 7 fields populated with realistic placeholder values, matching style of `example/config.json`)
- `config.schema.json` — new, root-level JSON Schema (draft-07) encoding required/type constraints for the 7 fields
- No code files touched. `dyu_accounting/__init__.py:60-61` is referenced in CONFIG.md as the load site but is NOT modified (KeyError fragility / `--validate-config` wiring is explicitly out of scope — flagged as future work, not part of this ticket).

## Implementation Notes

Implemented exactly per the impl-planner's outline, no deviations:

- `CONFIG.md` (repo root) — Overview, Field Reference table (all 7 fields
  with type/required/default/file:line/description), CLI-Supplied Values
  section (`fy`/`outdir`/`texwriter`), Scope Boundaries (config.json vs
  `.guided-config.json` with cross-link to GUIDED_MODE.md; chart-of-accounts
  & depreciation are beancount metadata, cross-link to README.md), Example
  (full `config.json.example` contents), and a one-line Schema pointer to
  `config.schema.json`.
- `config.json.example` (repo root) — valid, directly-loadable JSON with
  all 7 fields, `format` defaulting to `"html"` per the coded default in
  `Utilities/__init__.py:67`, based on `example/config.json`'s style.
- `config.schema.json` (repo root) — JSON Schema draft-07, `required`
  lists the 6 unguarded-lookup fields (`format` excluded, has a coded
  default), `additionalProperties: false` at top level, nested `required`
  for `company.{name,address}` and `gst.qrmp`.
- No code files touched; `dyu_accounting/__init__.py:60-61` referenced in
  CONFIG.md as the load site only.

Verification run:

```
python3 -c "
import json
cfg = json.load(open('config.json.example'))
assert cfg['format'] == 'html'
assert cfg['company']['name']
assert cfg['company']['address']
assert cfg['ar']
assert cfg['exchange_gain']
assert isinstance(cfg['cash_accounts'], list) and cfg['cash_accounts']
assert isinstance(cfg['gst']['qrmp'], bool)
print('config.json.example: all 7 fields present and correctly typed, OK')
schema = json.load(open('config.schema.json'))
print('config.schema.json: valid JSON, OK')
"
```
Output: both files load and all 7 fields check out (no KeyError).

Additionally cross-checked `config.json.example` against
`config.schema.json` with the `jsonschema` package
(`jsonschema.validate(cfg, schema)`) — validates cleanly.

## Current State

Stage: awaiting-approval. All three new files (`CONFIG.md`,
`config.json.example`, `config.schema.json`) are written at repo root and
spot-checked (valid JSON, schema validates example, no KeyError against
CONFIG.md's documented fields). No code changes. Awaiting human approval
to commit and close.

## Testing

No automated test suite — Validation Required: no (pure documentation).
Manual spot-check only: load `config.json.example` with `json.load()` and
confirm every field referenced in CONFIG.md's Field Reference table is
present and correctly typed.


## Requirements (Researcher-Refined)

### Investigation Summary

config.json is loaded in `dyu_accounting/__init__.py:60-61`, in `accounting()` (legacy mode only — triggered when `--guided` is NOT passed). Loaded via `json.load()` from a file literally named `config.json` in CWD.

**Runtime-injected (NOT user config fields)**: `cfg['fy']` (from `--fy` CLI arg), `cfg['outdir']` (from `--outdir`, default `"Output"`), `cfg['texwriter']` (internal file handle, never mention to users).

### All 7 Config Fields (found via grep across dyu_accounting/)

| Field | Type | Required | Default | Used in | Purpose |
|---|---|---|---|---|---|
| `format` | string | No | `"html"` | Utilities/__init__.py:67 | Template set: tex, md, adoc, html |
| `company.name` | string | Yes* | none | balance_sheet, pnl, gst, journal | Report header/title |
| `company.address` | string | Yes* | none | same cfg['company'] dict | Report header |
| `ar` | string (account) | Yes* | none | exchange_gain/__init__.py:34 | Account receivable for forex posting |
| `exchange_gain` | string (account) | Yes* | none | exchange_gain/__init__.py:36 | Forex exchange gain/loss account |
| `cash_accounts` | list[string] | Yes* | none | journal/__init__.py:22 | Accounts in cashbook/journal report |
| `gst.qrmp` | boolean | Yes* | none | gst/__init__.py:19 | GST Quarterly Return Monthly Payment flag |

`*` = unguarded `cfg['key']` lookup, no `.get()` fallback — missing key raises bare `KeyError`.

### Example config.json (from example/config.json)

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

### NOT part of config.json (don't conflate)

Chart-of-accounts classification (`balance_sheet: "attribute"` metadata) and depreciation category table are set via **beancount account metadata** (documented in README.md), not config.json.

### config.json vs .guided-config.json — Confirmed Distinct

- **config.json**: global, CWD, legacy-mode-only, controls report formatting/company identity/GST/forex
- **.guided-config.json**: per-FY, inside `FYyyyy_yy/` folder, guided-mode-only, importer→account mapping memory for pre-selection
- No overlap, no conflict, disjoint keys

### Feasibility: ✅ Primarily documentation task

**Risk flagged**: Every field except `format` accessed via unguarded `cfg['key']` — missing field crashes with bare `KeyError`. Ticket's existing AC for optional JSON Schema/`--validate-config` has real value; keep that scope but implementing the validator is impl-planner's job, not spec work.

### Acceptance Criteria

- [ ] `CONFIG.md` documents all 7 fields with type, required/optional, file:line reference
- [ ] Explicitly states `fy`/`outdir` are CLI-supplied, not config.json fields
- [ ] Explicitly distinguishes config.json from .guided-config.json (cross-ref GUIDED_MODE.md)
- [ ] Explicitly notes chart-of-accounts/depreciation are beancount metadata, not config.json
- [ ] `config.json.example` fully annotated template
- [ ] JSON Schema encoding required/optional/type constraints for future validation tooling

## Researcher Findings

All fields enumerated from source, cross-checked against example. Pure documentation task; KeyError fragility flagged for impl-planner via existing validation AC.


### Human Approval (2026-10-03)

Approved. Documentation reviewed and accepted.

