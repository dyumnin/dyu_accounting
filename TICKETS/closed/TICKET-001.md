# TICKET-001: Add step-by-step setup guide for new users

**Status**: closed
**Type**: improvement
**Priority**: medium
**Stage**: done
**Created**: 2026-09-29
**Completed**: 2026-10-03
**Parent**: none

## Problem / Motivation

New users struggle to understand the initial setup process. The current README jumps to "install and run command" without explaining the prerequisites (chart of accounts, config.json structure, beancount file structure). A beginner needs a walkthrough from zero to first report generation.

## Acceptance Criteria

- [ ] Step-by-step guide document (SETUP.md) covers: prerequisites, folder structure, chart of accounts creation, config.json creation with explanations, initial transaction entry, and first report run
- [ ] Guide uses the example project as reference but walks through from scratch
- [ ] Code examples show before/after for each step
- [ ] Document includes common mistakes and troubleshooting
- [ ] Guide is accessible to someone with accounting knowledge but no beancount experience

## Design Notes

Create a new `SETUP.md` file in root directory that mirrors the annual user workflow but tailored for first-time setup. Should reference the existing example but not assume prior knowledge of beancount syntax.

**Validation Required**: no — pure documentation change (new .md file + one-line doc fix in README.md), no code or behavior change.

### SETUP.md outline (impl-planner, exact structure)

1. `# Setup Guide` (H1 title + 1-line intro: "From zero to your first financial report")
2. `## Prerequisites`
   - Python `>=3` (per `pyproject.toml`, do not assert a stricter version)
   - Basic double-entry accounting familiarity assumed; no beancount syntax assumed
3. `## Installation`
   - ```
     pip3 install dyu_accounting
     ```
   - Dev/latest-from-source variant (mirror README's git clone + `pip install .`)
4. `## Folder Structure`
   - Show minimal working-directory layout before first run:
     ```
     my-company/
     ├── config.json
     ├── accounts.beancount      (chart of accounts + opening entries)
     └── ledger.beancount        (transactions; includes accounts.beancount)
     ```
   - Note: `config.json` must exist in the CWD the `account` command is invoked from (bare `open()` call, unhandled `FileNotFoundError` if missing) — call this out explicitly, it's also covered in Troubleshooting.
5. `## Step 1: Create Your Chart of Accounts`
   - Explain `balance_sheet: "<category>"` metadata requirement on every balance-sheet account (required for the account to appear in the Balance Sheet / financial statements).
   - Explain `depreciation_category: "<category>"` metadata on depreciable assets — list the 6 valid values (Furniture, OfficeEquipment, Phone, Server, Laptop, Electrical), matching the table already in README.md's "Setting up your chart of accounts" section (do not duplicate the full MCA/IT rate table — link to that README section instead).
   - Before/after snippet: a bare beancount `open` directive vs. the same directive with required metadata added, pulled from `example/accounts.beancount` (e.g. the `Assets:INR:Cash` and `Assets:INR:Equipment:Furniture` entries).
   - Link out to the full `balance_sheet` attribute list already documented in README.md rather than repeating it.
6. `## Step 2: Create config.json`
   - Minimum fields needed for a first report, each with a one-line explanation: `format`, `company.name`, `company.address`, `ar`, `exchange_gain`, `cash_accounts`, `gst.qrmp`.
   - Full worked example lifted directly from `example/config.json`.
   - Explicit callout: `"format": "tex"` only writes a `.tex` file — nothing in the codebase invokes `pdflatex`, so no PDF is produced unless the user separately installs a LaTeX toolchain. Recommend `"format": "md"` or `"format": "html"` for a dependency-free first report; document `tex` as advanced/optional.
   - Defer full config.json field reference to TICKET-002/CONFIG.md (link placeholder, don't inline the whole schema here).
7. `## Step 3: Enter Your First Transactions`
   - Short, minimal transaction example (not the full example ledger) showing a beancount transaction referencing accounts opened in Step 1.
8. `## Step 4: Generate Your First Report`
   - Primary path — guided mode:
     ```
     account --guided
     ```
     One paragraph summary + link to `GUIDED_MODE.md` for full detail. Note clearly that `--guided` only imports statements and builds the parent ledger + reconciliation report; it does NOT create the chart of accounts or `config.json` (those are Steps 1–2 above, still required first).
   - Manual/legacy fallback path, with CORRECT flags:
     ```
     mkdir -p reports/2019
     account --infile ledger.beancount --fy 2019 --outdir reports/2019/
     ```
   - Note `--outdir` defaults to `Output` if omitted; `--infile` and `--fy` are required.
9. `## Common Mistakes & Troubleshooting`
   - Missing `config.json` in CWD → unhandled `FileNotFoundError` on startup; fix: run `account` from the folder containing `config.json`.
   - Account missing `balance_sheet:` metadata → account silently excluded from balance sheet; fix: add metadata per Step 1.
   - Wrong flag names (`--in`/`--out` instead of `--infile`/`--outdir`) → `unrecognized arguments` error; this is a historical doc bug, now fixed here and in README.md.
   - `depreciation_category` value not matching one of the 6 valid categories → fix: use exact match (case-sensitive) from the list in Step 1.
   - Using `"format": "tex"` without LaTeX installed → `.tex` file is produced but no PDF; fix: use `md`/`html`, or install a LaTeX toolchain separately.
10. `## Next Steps`
    - Link to `GUIDED_MODE.md` (annual re-import workflow) and to TICKET-002/CONFIG.md (full config reference) once available.

### Source material to pull examples from (do not re-derive, copy/adapt verbatim where noted)

- `example/accounts.beancount` — chart-of-accounts before/after snippets (Step 1)
- `example/config.json` — full config.json example (Step 2)
- `GUIDED_MODE.md` — guided-mode summary + link target (Step 4); note GUIDED_MODE.md's own CLI Reference and Backward Compatibility sections still show the buggy `--in ledger.beancount --fy 2026 --out reports/` form — this ticket's Files Affected only covers README.md, so GUIDED_MODE.md's copy of the same bug is left as-is (out of scope here; flag separately if it should be fixed too).
- README.md's existing "Setting up your chart of accounts" section — link target for the full `balance_sheet` attribute list, don't duplicate it in SETUP.md

### README.md fix (exact location)

File: `README.md`, lines 34-40, section `# Generation reports`.

Before:
```
# Generation reports

Once you have installed this package and generated a compliant Accounting file (see example directory) you can generate the required reports by running 

```
mkdir reports/2019
account --in ledger.beancount --fy 2019 --out reports/2019/  
```
```

After:
```
# Generation reports

Once you have installed this package and generated a compliant Accounting file (see example directory) you can generate the required reports by running 

```
mkdir reports/2019
account --infile ledger.beancount --fy 2019 --outdir reports/2019/
```

See [SETUP.md](SETUP.md) for a full step-by-step walkthrough.
```

Also add a one-line pointer to SETUP.md near the top of README.md (in the introduction, before the "Installation" section) per the existing Files Affected note, e.g.: "New to this project? See [SETUP.md](SETUP.md) for a step-by-step guide from zero to your first report."

## Files Affected

- `SETUP.md` — new comprehensive setup guide; outline specified in Design Notes above
- `README.md` — two changes: (1) add one-line pointer to SETUP.md in the introduction, (2) fix lines 34-40 `# Generation reports` example from `--in`/`--out` to `--infile`/`--outdir` (pre-existing CLI flag bug)

## Implementation Notes

Implemented exactly per the Design Notes outline:

- Created `SETUP.md` at repo root with all 10 planned sections (Prerequisites, Installation, Folder Structure, Step 1 Chart of Accounts, Step 2 config.json, Step 3 First Transactions, Step 4 First Report, Common Mistakes & Troubleshooting, Next Steps).
  - Chart-of-accounts before/after snippet and metadata explanation sourced from `example/accounts.beancount` (`Assets:INR:Cash`, `Assets:INR:Equipment:Furniture`); links out to README.md's existing `balance_sheet` attribute list rather than duplicating it.
  - config.json section lists the 7 minimum fields (`format`, `company.name`, `company.address`, `ar`, `exchange_gain`, `cash_accounts`, `gst.qrmp`) with one-line explanations, full example copied verbatim from `example/config.json`, and an explicit callout that `"format": "tex"` produces no PDF without a separately-installed LaTeX toolchain — `md`/`html` recommended for a dependency-free first report. Full config reference deferred to TICKET-002/CONFIG.md (noted as "once available," since CONFIG.md doesn't exist yet).
  - First-report section documents `account --guided` as the primary path (linking to GUIDED_MODE.md, noting it does not create the chart of accounts or config.json) and the manual/legacy fallback with the correct flags `--infile`/`--fy`/`--outdir` (confirmed against `dyu_accounting/__init__.py` argparse setup), noting `--outdir` defaults to `Output`.
  - Troubleshooting section covers: missing config.json (FileNotFoundError), accounts missing `balance_sheet:` metadata, wrong flag names (`--in`/`--out`), mismatched `depreciation_category` values, and the tex/no-PDF gotcha.
- Fixed `README.md`:
  - Lines 34-40 (`# Generation reports` section): corrected `--in ledger.beancount --fy 2019 --out reports/2019/` to `--infile ledger.beancount --fy 2019 --outdir reports/2019/`, and added a pointer to SETUP.md immediately after the example.
  - Added a one-line pointer to SETUP.md in the introduction, before the "Installation" section, as specified in Files Affected.
- Left `GUIDED_MODE.md`'s copy of the same `--in`/`--out` bug untouched, per Design Notes' explicit note that it's out of scope for this ticket.

No code changes; no tests to run (pure documentation, Validation Required: no). Verified by reading the rendered files back and cross-checking flag names against `dyu_accounting/__init__.py:65-70`.

Commands run to verify:
```
grep -n "infile\|outdir\|--in \|--out " README.md SETUP.md
sed -n '55,80p' dyu_accounting/__init__.py   # confirmed argparse flag names
```

## Testing

Verify guide by following it step-by-step with fresh setup in test environment.


## Requirements (Researcher-Refined)

### Critical Bug Found: Wrong CLI Flags in Existing Docs

README.md and GUIDED_MODE.md both document `account --in ledger.beancount --fy 2019 --out reports/2019/` — **but this is WRONG**. Actual argparse flags (`dyu_accounting/__init__.py:65-70`) are `--infile` (required), `--fy` (required, int), `--outdir` (default "Output"). Running the documented command fails with "unrecognized arguments".

**SETUP.md must use correct flags. README.md's example should also be fixed** (separate quick doc fix, still in scope).

### Key Findings

1. **Two independent CLI paths**: `account --guided` only imports statements and builds parent ledger + reconciliation report. It does NOT create chart of accounts or config.json. Legacy `account --infile <ledger> --fy <YYYY> --outdir <dir>` generates actual reports (Balance Sheet, P&L, etc.) and requires config.json to exist (bare `open()`, unhandled FileNotFoundError if missing).

2. **Chart of accounts requires metadata**: Every balance-sheet account needs `balance_sheet: "<category>"` metadata; depreciable assets need `depreciation_category: "<category>"` matching one of 6 hardcoded categories (Furniture/OfficeEquipment/Phone/Server/Laptop/Electrical). Reference `example/accounts.beancount`.

3. **config.json minimum fields** for first report: format, company.name/address, ar, exchange_gain, cash_accounts, gst.qrmp (full reference deferred to TICKET-002).

4. **Undocumented LaTeX dependency**: `"format": "tex"` only writes a `.tex` file — no code invokes pdflatex. User following tex path won't get a PDF without separately installing LaTeX. Recommend `"format": "md"` or `"html"` for dependency-free first report.

5. **No strict Python version**: pyproject.toml says `>=3`, don't assert stricter.

### Feasibility: ✅ Pure documentation, no code changes required

### Acceptance Criteria

- [ ] SETUP.md: installation + Python requirement (per pyproject.toml, `>=3`)
- [ ] SETUP.md: chart-of-accounts walkthrough with required `balance_sheet:`/`depreciation_category:` metadata (ref example/accounts.beancount)
- [ ] SETUP.md: minimum config.json fields for first report, defer full reference to TICKET-002/CONFIG.md
- [ ] SETUP.md: `account --guided` as primary path, link to GUIDED_MODE.md for detail
- [ ] SETUP.md: manual fallback path with CORRECT flags (`--infile`/`--outdir`, not `--in`/`--out`)
- [ ] SETUP.md: first report recommends `md`/`html` format (dependency-free); `tex` documented as advanced/optional requiring separate LaTeX install
- [ ] Troubleshooting section: missing config.json, unclassified accounts, flag name mistakes
- [ ] README.md legacy-mode example corrected to `--infile`/`--outdir` (doc-only fix)

## Researcher Findings

Pure documentation task. Found and will document: CLI flag bug (pre-existing in README/GUIDED_MODE.md) and undeclared LaTeX dependency risk.

## Current State

**Stage**: done. SETUP.md written (all 10 sections per outline) and README.md fixed (intro pointer + corrected `--infile`/`--outdir` flags in the Generation reports example). No code changes, no tests needed (Validation Required: no). Awaiting explicit human approval before this ticket can move to `done`.


### Human Approval (2026-10-03)

Approved. Documentation reviewed and accepted.

