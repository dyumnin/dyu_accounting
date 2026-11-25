"""
Reconcile the Account (Google Form) importer's entries against the real
bank/credit-card intermediate ledgers for the same FY, instead of booking
both independently (which double-counts the same real-world transaction
once under the manually-logged Account entry and once under the bank's own
statement entry).

For each Account entry (Payment column -> source account, Purpose column ->
expense account, Receipt column -> metadata):
  - "Cash" entries have no corresponding bank/card statement at all, so
    they're written out as-is (already a complete double-entry transaction)
    to FY{fy}/intermediate/cash.beancount.
  - All other entries are matched against the bank/credit-card intermediate
    ledger for that same account (by date window + amount), and when a
    unique match is found, the bank-side transaction (which only has a
    single, unbalanced posting - no importer here fills in a target account)
    has its second leg added using the Account entry's Purpose-mapped
    account, and the receipt URL attached as metadata. The bank transaction
    stays in its own file; the duplicate Account-side entry is dropped.
  - Entries that can't be matched are left behind for manual review rather
    than silently dropped.
"""

import glob
import os
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from beancount import loader
from beancount.core import data
from beancount.parser import printer

from dyu_accounting.gulp.Account import Importer as AccountImporter

MATCH_WINDOW_DAYS = 2
AMOUNT_TOLERANCE = Decimal('0.01')

CASH_ACCOUNT = AccountImporter.PAYMENT_ACCOUNT_MAP['cash']


def reconcile_fy(fy: str) -> None:
    """
    Reconcile FY{fy}'s Account (Google Form) intermediate ledger(s) against
    its other (bank/credit-card) intermediate ledgers, in place.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
    """
    intermediate_dir = f"FY{fy}/intermediate"
    account_paths = sorted(glob.glob(os.path.join(intermediate_dir, "account_*.beancount")))
    if not account_paths:
        print(f"No account_*.beancount intermediate ledgers found under {intermediate_dir}/ "
              "- nothing to reconcile.")
        return

    account_basenames = {os.path.basename(p) for p in account_paths}
    source_paths = sorted(
        p for p in glob.glob(os.path.join(intermediate_dir, "*.beancount"))
        if os.path.basename(p) not in account_basenames
        and os.path.basename(p) != "cash.beancount"
    )

    source_entries_by_path = {p: _load_transactions(p) for p in source_paths}

    # Index single-posting (unbalanced, not-yet-categorized) source
    # transactions by the account they post to, so each Account entry only
    # needs to search the candidates that could plausibly be it.
    index: Dict[str, List[Tuple[str, data.Transaction]]] = {}
    for path, entries in source_entries_by_path.items():
        for entry in entries:
            if len(entry.postings) == 1:
                index.setdefault(entry.postings[0].account, []).append((path, entry))

    cash_entries = []
    leftover_entries = []
    matched_count = 0
    modified_paths = set()

    for account_path in account_paths:
        for entry in _load_transactions(account_path):
            if len(entry.postings) < 2:
                # Not a well-formed Account entry (e.g. fallback account with
                # no Purpose match); don't silently drop it.
                leftover_entries.append(entry)
                continue

            payment_posting, purpose_posting = entry.postings[0], entry.postings[1]

            if payment_posting.account == CASH_ACCOUNT:
                cash_entries.append(entry)
                continue

            candidates = index.get(payment_posting.account, [])
            match = _find_match(entry, payment_posting, candidates)
            if match is None:
                leftover_entries.append(entry)
                continue

            path, source_entry = match
            data.create_simple_posting(source_entry, purpose_posting.account, None, None)
            receipt = entry.meta.get('receipt')
            if receipt:
                source_entry.meta['receipt'] = receipt
            modified_paths.add(path)
            matched_count += 1
            candidates.remove(match)

    cash_path = os.path.join(intermediate_dir, "cash.beancount")
    # Merge with whatever's already there: a cash entry only shows up in
    # cash_entries the one run where it's still sitting in account_*.beancount
    # (it's moved out of there once reconciled), so a later re-run - say,
    # after importing more files - would otherwise overwrite this file with
    # only *this* run's (possibly empty) cash entries and lose everything a
    # previous run already wrote here.
    existing_cash_entries = _load_transactions(cash_path) if os.path.exists(cash_path) else []
    _write_entries(
        cash_path, existing_cash_entries + cash_entries,
        header="Cash transactions reconciled from the Account (Google Form) log"
    )

    for path in modified_paths:
        _write_entries(path, source_entries_by_path[path])

    # Leftovers (unmatched, non-cash entries) go in the first account file;
    # every account_*.beancount file is rewritten so the parent ledger's
    # existing `include` directives keep pointing at real files.
    _write_entries(
        account_paths[0], leftover_entries,
        header="Unmatched Account (Google Form) entries - review manually"
    )
    for path in account_paths[1:]:
        _write_entries(
            path, [],
            header="(entries merged into cash.beancount or the matching source ledger)"
        )

    print(f"Reconciled {matched_count} Account entries into {len(modified_paths)} "
          f"source ledger(s).")
    print(f"Wrote {len(cash_entries)} cash transactions to {cash_path}")
    if leftover_entries:
        print(f"Warning: {len(leftover_entries)} Account entries could not be matched "
              f"to a source transaction - left in {account_paths[0]} for manual review.")


def _find_match(
    account_entry: data.Transaction,
    payment_posting: data.Posting,
    candidates: List[Tuple[str, data.Transaction]]
) -> Optional[Tuple[str, data.Transaction]]:
    """Find the closest-dated candidate within the amount tolerance and date window."""
    if payment_posting.units is None:
        return None
    target_amount = abs(payment_posting.units.number)
    target_currency = payment_posting.units.currency

    best = None
    best_delta_days = None
    for path, source_entry in candidates:
        source_posting = source_entry.postings[0]
        if source_posting.units is None or source_posting.units.currency != target_currency:
            continue
        if abs(abs(source_posting.units.number) - target_amount) > AMOUNT_TOLERANCE:
            continue
        delta_days = abs((source_entry.date - account_entry.date).days)
        if delta_days > MATCH_WINDOW_DAYS:
            continue
        if best is None or delta_days < best_delta_days:
            best = (path, source_entry)
            best_delta_days = delta_days
    return best


def _load_transactions(path: str) -> List[data.Transaction]:
    """
    Load an intermediate ledger's Transaction entries directly (not through
    the parent ledger), so missing `open` directives for its accounts don't
    block reading it back. beancount's loader collects such issues as
    non-fatal errors and still returns the parsed entries.

    Also revives entries bean-extract's own de-duplication has commented out
    (beancount.ingest.extract.print_extracted_entries prefixes every line of
    an entry it believes already exists in the target ledger with '; '). If
    an intermediate file gets re-extracted after the parent ledger already
    includes its (possibly already-reconciled) entries, every one of them
    comes back commented out on the next run - otherwise invisible to
    beancount's parser, and permanently unmatchable here even though they're
    still real transactions, just already recorded elsewhere too.
    """
    with open(path) as f:
        raw = f.read()
    revived = '\n'.join(
        line[len('; '):] if line.startswith('; ') else line
        for line in raw.splitlines()
    )
    entries, _errors, _options = loader.load_string(revived)
    return [e for e in entries if isinstance(e, data.Transaction)]


def _write_entries(path: str, entries: List[data.Transaction], header: Optional[str] = None) -> None:
    with open(path, 'w') as f:
        if header:
            f.write(f";; {header}\n\n")
        printer.print_entries(entries, file=f)
