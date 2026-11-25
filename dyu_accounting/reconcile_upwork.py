"""
True up an Upwork withdrawal's provisional INR receivable once its real
bank-side settlement is known, posting the resulting USD/INR exchange gain
or loss.

Upwork withdrawals settle into the bank 1-2+ weeks later, at whatever rate
the bank actually used. dyu_accounting/gulp/Upworks.py books a *provisional*
value immediately, at the withdrawal date's own auto-fetched rate:

    Assets:USD:Upwork  -5498.19 USD @ 85.80 INR
    Assets:INR:Cash:AccountReceivable:Upwork  (auto-balances to ~471772 INR)

This module:

  1. Finds the named withdrawal transaction (by date) in the Upwork
     intermediate ledger and reads its already-booked (provisional)
     receivable value - no further changes are made to this transaction.
  2. Finds the matching single-leg deposit (by date) in the IDFC
     intermediate ledger - the real, actual INR amount.
  3. Completes that IDFC-side transaction with a posting that clears the
     provisional receivable amount, plus an auto-balancing
     Assets:INR:ExchangeGain posting for the expected-vs-actual difference.
"""

import datetime
import glob
import os
from typing import Optional, Tuple

from beancount.core import data

from dyu_accounting.reconcile_account import _load_transactions, _write_entries

EXCHANGE_GAIN_ACCOUNT = "Assets:INR:ExchangeGain"
RECEIVABLE_ACCOUNT = "Assets:INR:Cash:AccountReceivable:Upwork"


def reconcile_withdrawal(fy: str, withdrawal_date: datetime.date, idfc_date: datetime.date) -> None:
    """
    True up one Upwork withdrawal's provisional receivable using its
    matched IDFC deposit.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        withdrawal_date: Date of the Upwork withdrawal transaction
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

    all_upwork_entries = [e for p in upwork_paths for e in _load_transactions(p)]
    withdrawal = next(
        (e for e in all_upwork_entries
         if e.meta.get("upwork_withdrawal") and e.date == withdrawal_date),
        None
    )
    if withdrawal is None:
        print(f"No Upwork withdrawal transaction dated {withdrawal_date} found.")
        return

    expected_inr = next(
        (p.units.number for p in withdrawal.postings if p.account == RECEIVABLE_ACCOUNT),
        None
    )
    if expected_inr is None:
        print(f"Withdrawal on {withdrawal_date} has no {RECEIVABLE_ACCOUNT} posting "
              "to true up - nothing to do.")
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

    # The ExchangeGain posting's sign is forced by the other two (it's
    # whatever makes the transaction balance): actual_inr - expected_inr +
    # ExchangeGain = 0, so ExchangeGain = expected_inr - actual_inr. That
    # means it's *positive* for a loss (settled for less than the
    # provisional estimate) and *negative* for a gain - the inverse of what
    # the account's name suggests at a glance.
    new_postings = list(idfc_entry.postings) + [
        data.Posting(RECEIVABLE_ACCOUNT, data.Amount(-expected_inr, "INR"), None, None, None, None),
        data.Posting(EXCHANGE_GAIN_ACCOUNT, None, None, None, None, None),
    ]
    completed = idfc_entry._replace(postings=new_postings)
    idfc_entries_by_path[idfc_path] = [
        completed if e is idfc_entry else e for e in idfc_entries_by_path[idfc_path]
    ]
    _write_entries(idfc_path, idfc_entries_by_path[idfc_path])

    gain = actual_inr - expected_inr
    print(f"Trued up withdrawal {withdrawal_date} (provisional INR {expected_inr}) against "
          f"IDFC deposit {idfc_date} (actual INR {actual_inr}).")
    print(f"  {'Gain' if gain >= 0 else 'Loss'}: {abs(gain)} posted to {EXCHANGE_GAIN_ACCOUNT}")

    from dyu_accounting.guided_mode import generate_and_save_parent_ledger
    all_intermediate_paths = sorted(glob.glob(os.path.join(intermediate_dir, "*.beancount")))
    generate_and_save_parent_ledger(fy, all_intermediate_paths)
