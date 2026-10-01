# TICKET-009: Modify Google Forms importer columns and mapping

**Status**: open
**Type**: feature
**Priority**: high
**Stage**: ready-to-implement
**Created**: 2026-10-01
**Parent**: none

## Problem / Motivation

What problem does this solve, or what capability does it add? Why is it needed?

## Acceptance Criteria

- [ ] Criterion 1 — specific, testable condition that must be true when done
- [ ] Criterion 2
- [ ] Criterion 3

## Design Notes

Key decisions, constraints, or approach chosen before implementation starts.
If multiple approaches were considered, note why this one was chosen.

## Files Affected

List the files expected to change (fill in before starting, update if scope changes).

- `path/to/file.ext` — reason

## Implementation Notes

Filled in during / after implementation. Surprises, deviations from design, follow-up items.

## Testing

How to verify this works. Command to run, expected output, edge cases checked.

## Problem / Motivation

The existing Account (Google Forms) importer needs to be modified to support a specific column set and transaction mapping:

**Required columns:**
- Timestamp
- Date
- Amount
- Purpose
- Payment
- Receipt

**Current vs. Desired mapping:**
| Current | Desired |
|---------|---------|
| Transaction Title | Purpose (transaction description) |
| Credit to Account | Purpose (use Purpose column) |

This maps Google Forms responses to beancount transaction fields correctly.

## Scope

**File to modify**: `/prj/dyumnin_projects/accounting/beancount-scripts/dyu_accounting/gulp/Account.py`

Changes needed:
- Update column definitions (header_identifier, column field names)
- Modify transaction title extraction (use Purpose instead of Transaction Title)
- Modify credit account mapping (use Purpose column)
- Update filename_pattern_def if needed
- Ensure custom_init() properly initializes with new column structure

## Acceptance Criteria

- [ ] Importer accepts CSV with columns: Timestamp, Date, Amount, Purpose, Payment, Receipt
- [ ] Transaction description field populated from Purpose column
- [ ] Credit account populated from Purpose column
- [ ] All existing tests still pass (no regression)
- [ ] Google Forms CSV can be successfully imported using guided mode

## Implementation Notes

(To be filled during implementation)


## Requirements (Researcher-Refined)

### Key Findings

**Current Account.py structure** (7 columns):
- `Timestamp,Date,Transaction Title,Amount,Paid from Account,Credit to Account,Receipt`
- `Credit to Account` column exists but is **never read** by importer
- Target account comes from static `config.get("target_account")`, not from CSV
- Transaction Title maps to memo/narration via `header_map`

**Critical Challenge**: Using Purpose column to populate credit account requires **sanitization**. Real sample data contains:
- `"1947 food"` ← invalid Beancount account name
- `"USB cables, boxes, snacks"` ← contains commas, invalid for account names
- `"अरायभवन unknown date"` ← non-ASCII, free-form text

Free-text Purpose values cannot become valid Beancount account names without explicit sanitization or lookup table.

### Open Design Questions for Impl-Planner

1. **Purpose → Credit Account mapping strategy**:
   - Option A: Sanitize Purpose text (remove special chars, truncate, etc.)
   - Option B: Lookup Purpose against chart-of-accounts, fallback to `Expenses:Uncategorized`
   - Option C: Something else?
   - **Must be explicitly documented** — no guessing

2. **Payment column semantics**: What should it represent?
   - Payment method (e.g., "Cash", "Card", "Check")?
   - Paid from account (the old column name)?
   - Payment tracking metadata?
   - **Decision needed before implementation**

3. **Receipt column semantics**: What should it represent?
   - Receipt URL/attachment?
   - Receipt number/confirmation?
   - Transaction metadata?
   - **Decision needed before implementation**

4. **Backward compatibility**:
   - Support old 7-column format alongside new 6-column?
   - Clean cutover only (old files must be re-exported)?
   - **Scope decision needed**

### Acceptance Criteria

- [ ] Header changed to: `Timestamp,Date,Amount,Purpose,Payment,Receipt` (6 columns)
- [ ] Purpose populates transaction narration (via header_map)
- [ ] Purpose populates credit account via overridden `get_target_account()` with documented sanitization/lookup strategy
- [ ] Payment and Receipt columns handled per documented design decision
- [ ] Test fixtures updated to new 6-column format
- [ ] All existing tests pass (no regression to other importers)

### Design Notes

**This is not a simple rename**. Requires:
1. Update `header_identifier` and `column_labels_line` (trivial)
2. Update `header_map` to use Purpose instead of Transaction Title (trivial)
3. Override `get_target_account(ot)` to derive account from Purpose (non-trivial, needs sanitization strategy)
4. Define behavior for Payment and Receipt columns (non-trivial, needs semantics decision)
5. Update test fixtures and add test coverage for new logic

**Flagged for human/impl-planner decision**: Payment/Receipt semantics, Purpose sanitization strategy, backward compatibility approach.

## Researcher Findings

Technical feasibility confirmed. Architecture understood. Open design questions flagged for explicit resolution before implementation.


### Design Clarifications (User, 2026-10-01)

**Purpose → Account Mapping Strategy**:
- Create lookup table mapping Purpose strings to chart-of-accounts entries
- Example mappings:
  - "payments company card" → Assets:IDFC (or account in setup.beancount)
  - "cash" → Assets:Cash
  - "credit card" → Liabilities:ICICICard (or ICICI Credit Card account)
- Lookup is case-insensitive, flexible matching
- Fallback: `Expenses:Uncategorized` if no match found

**Receipt Handling**:
- Use Receipt column value as document link/metadata
- Store as transaction metadata or document reference in beancount posting

**Payment Column**:
- For future use or metadata tracking (not currently in scope)

**Backward Compatibility**:
- Clean cutover — no support for old format
- Only new 6-column format: `Timestamp,Date,Amount,Purpose,Payment,Receipt`

**Pre-implementation**:
- Commit current code with git tag before starting edits
- Keep old Account.py implementation as reference

