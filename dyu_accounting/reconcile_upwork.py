"""
Complete an Upwork withdrawal transaction once its real bank-side settlement
is known, and post the resulting USD/INR exchange gain or loss.

Upwork withdrawals settle into the bank 1-2+ weeks later, at whatever rate
the bank actually used - not knowable at CSV-extraction time (see
dyu_accounting/gulp/Upworks.py, which deliberately leaves these single-leg).
This module:

  1. Finds the named withdrawal transaction (by date) in the Upwork
     intermediate ledger, and the matching single-leg deposit (by date) in
     the IDFC intermediate ledger.
  2. Computes a blended "expected" USD/INR rate from every earning
     transaction between the previous withdrawal (exclusive) and this one
     (inclusive) - i.e. what the withdrawn principal would have been worth
     in INR if each dollar had been converted the day it was earned. The
     withdrawal's own fee is excluded from this base (it's a flat USD cost,
     never itself converted).
  3. Completes the withdrawal transaction with the IDFC deposit's actual INR
     amount and an auto-balancing Assets:INR:ExchangeGain posting - the
     expected-vs-actual difference - and removes the now-redundant IDFC-side
     entry (its content is now part of this one transaction).
"""

import datetime
import glob
import os
from decimal import Decimal
from typing import List, Optional, Tuple

from beancount.core import data
from beancount.core.amount import Amount

from dyu_accounting.reconcile_account import _load_transactions, _write_entries

EXCHANGE_GAIN_ACCOUNT = "Assets:INR:ExchangeGain"
IDFC_ACCOUNT = "Assets:INR:Cash:IDFC:Current"


def reconcile_withdrawal(fy: str, withdrawal_date: datetime.date, idfc_date: datetime.date) -> None:
    """
    Complete one Upwork withdrawal using its matched IDFC deposit.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        withdrawal_date: Date of the Upwork withdrawal transaction to complete
        idfc_date: Date of the matching IDFC bank deposit
    """
    intermediate_dir = f"FY{fy}/intermediate"
    upwork_paths = sorted(glob.glob(os.path.join(intermediate_dir, "upworks_*.beancount")))
    idfc_paths = sorted(glob.glob(os.path.join(intermediate_dir, "idfc_bank_*.beancount")))
    if not upwork_paths:
        print(f"No upworks_*.beancount intermediate ledgers found under {intermediate_dir}/")
        return
    if not idfc_paths:
        print(f"No idfc_bank_*.beancount intermediate ledgers found under {intermediate_dir}/")
        return

    upwork_entries_by_path = {p: _load_transactions(p) for p in upwork_paths}
    all_upwork_entries = [e for entries in upwork_entries_by_path.values() for e in entries]

    withdrawals = sorted(
        (e for e in all_upwork_entries if e.meta.get("upwork_withdrawal")),
        key=lambda e: e.date
    )
    target_path, target = _find_by_date(upwork_entries_by_path, withdrawals, withdrawal_date)
    if target is None:
        print(f"No Upwork withdrawal transaction dated {withdrawal_date} found.")
        return
    if len(target.postings) > 2:
        print(f"Withdrawal on {withdrawal_date} already has {len(target.postings)} postings "
              "- looks already reconciled. Skipping.")
        return

    idfc_entries_by_path = {p: _load_transactions(p) for p in idfc_paths}
    all_idfc_entries = [(path, e) for path, entries in idfc_entries_by_path.items() for e in entries]
    idfc_candidates = [
        (path, e) for path, e in all_idfc_entries
        if e.date == idfc_date and len(e.postings) == 1 and e.postings[0].units.number > 0
    ]
    if not idfc_candidates:
        print(f"No unresolved IDFC deposit dated {idfc_date} found.")
        return
    if len(idfc_candidates) > 1:
        idfc_candidates.sort(key=lambda pe: abs(pe[1].postings[0].units.number), reverse=True)
        print(f"Warning: {len(idfc_candidates)} unresolved IDFC entries on {idfc_date}; "
              "using the largest.")
    idfc_path, idfc_entry = idfc_candidates[0]
    actual_inr = idfc_entry.postings[0].units.number

    prev_withdrawal_date = max(
        (w.date for w in withdrawals if w.date < withdrawal_date), default=None
    )
    blended_rate = _blended_expected_rate(all_upwork_entries, prev_withdrawal_date, withdrawal_date)
    if blended_rate is None:
        print(f"No earning transactions found to compute an expected rate for {withdrawal_date} "
              "- can't reconcile.")
        return

    principal_posting = target.postings[0]
    fee_postings = target.postings[1:]

    new_postings = [
        data.Posting(principal_posting.account, principal_posting.units, None,
                     Amount(blended_rate, "INR"), principal_posting.flag, principal_posting.meta)
    ]
    for p in fee_postings:
        new_postings.append(
            data.Posting(p.account, p.units, None, Amount(blended_rate, "INR"), p.flag, p.meta)
        )
    new_postings.append(data.Posting(IDFC_ACCOUNT, Amount(actual_inr, "INR"), None, None, None, None))
    new_postings.append(data.Posting(EXCHANGE_GAIN_ACCOUNT, None, None, None, None, None))

    completed = target._replace(postings=new_postings)
    upwork_entries_by_path[target_path] = [
        completed if e is target else e for e in upwork_entries_by_path[target_path]
    ]
    idfc_entries_by_path[idfc_path] = [e for e in idfc_entries_by_path[idfc_path] if e is not idfc_entry]

    _write_entries(target_path, upwork_entries_by_path[target_path])
    _write_entries(idfc_path, idfc_entries_by_path[idfc_path])

    withdrawn_principal = abs(principal_posting.units.number)
    expected_inr = blended_rate * withdrawn_principal
    gain = actual_inr - expected_inr
    actual_rate = actual_inr / withdrawn_principal
    print(f"Reconciled withdrawal {withdrawal_date} (USD {withdrawn_principal}) against "
          f"IDFC deposit {idfc_date} (INR {actual_inr}).")
    print(f"  Blended expected rate: {blended_rate}  Actual rate: {actual_rate}")
    print(f"  Expected INR: {expected_inr}  Actual INR: {actual_inr}  "
          f"{'Gain' if gain >= 0 else 'Loss'}: {abs(gain)}")

    from dyu_accounting.guided_mode import generate_and_save_parent_ledger
    import glob as _glob
    all_intermediate_paths = sorted(_glob.glob(os.path.join(intermediate_dir, "*.beancount")))
    generate_and_save_parent_ledger(fy, all_intermediate_paths)


def _find_by_date(entries_by_path, candidates, target_date):
    for e in candidates:
        if e.date == target_date:
            path = next(p for p, entries in entries_by_path.items() if e in entries)
            return path, e
    return None, None


def _blended_expected_rate(
    all_upwork_entries: List[data.Transaction],
    prev_withdrawal_date: Optional[datetime.date],
    withdrawal_date: datetime.date,
) -> Optional[Decimal]:
    """
    Weighted-average USD/INR rate across every earning transaction's net
    (gross minus fees) wallet contribution, from just after the previous
    withdrawal up to and including this one. Excludes the withdrawal
    transaction itself (its fee is a flat USD cost, never converted).
    """
    total_usd = Decimal(0)
    total_weight = Decimal(0)
    for e in all_upwork_entries:
        if e.meta.get("upwork_withdrawal"):
            continue
        if prev_withdrawal_date is not None and e.date <= prev_withdrawal_date:
            continue
        if e.date > withdrawal_date:
            continue
        for p in e.postings:
            if p.account.startswith("Assets:USD:Upwork") and p.price is not None:
                total_usd += p.units.number
                total_weight += p.units.number * p.price.number
    if total_usd == 0:
        return None
    return total_weight / total_usd
