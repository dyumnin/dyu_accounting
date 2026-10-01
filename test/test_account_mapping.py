"""
test_account_mapping.py
========================

VALIDATION PROTOTYPE -- NOT PRODUCTION CODE.

This file is a standalone, self-contained proof of correctness for the
account-mapping design described in TICKET-009. It exists to validate the
mapping rules (Payment -> source/credit account, Purpose -> expense/debit
account) BEFORE they are wired into the real importer at
``dyu_accounting/gulp/Account.py``.

Nothing in ``dyu_accounting/gulp/Account.py`` is imported or modified by
this file. The reference implementation below (``PAYMENT_ACCOUNT_MAP``,
``PURPOSE_ACCOUNT_MAP``, ``map_payment_to_account``, ``map_purpose_to_account``,
``build_posting_pair``) is a throwaway prototype whose only job is to prove
the mapping/matching rules are sound against both synthetic cases and the
real exported Google Forms CSV at ``/prj/ip/claude/Accounts.csv``.

Once this test suite passes and a human approves the go/no-go recommendation,
the *real* implementer will port this logic (or an equivalent) into
``Account.py``'s ``get_target_account`` / ``build_metadata`` / header-map
code. The implementer is free to restructure, but the behavioral contract
(case-insensitivity, whitespace-collapse, fallback accounts, double-entry
sign convention) proven here should be preserved.

Design decisions made in this prototype that were NOT explicitly pinned
down by the ticket (flagged here for review before production wiring):

1. **None handling**: ``None`` is treated identically to the empty string
   ``""`` for both Purpose and Payment -- i.e. ``map_purpose_to_account(None)``
   returns the same fallback as ``map_purpose_to_account("")``. This was
   chosen because CSV parsing with the ``csv`` module never actually
   produces ``None`` for a present-but-empty field (it produces ``""``),
   but defensive callers might pass ``None`` directly.
2. **Whitespace normalization algorithm**: normalization is
   ``" ".join(value.strip().split())`` -- i.e. strip leading/trailing
   whitespace AND collapse any run of internal whitespace (including
   double spaces, tabs) down to a single space, before the case-insensitive
   lookup. This specifically handles the real-data value
   ``"Vehicle  maintenance "`` (double internal space + trailing space).
3. **No truncation of long strings**: a very long Purpose string is not
   truncated; it is simply looked up as-is (post-normalization) and, since
   it will not match any key in the table, it resolves to the fallback
   account. No length limit is enforced in this prototype.
4. **Sign convention for ``build_posting_pair``**: ``debit_amount`` is
   recorded as ``+amount`` and ``credit_amount`` as ``-amount``, matching
   standard double-entry bookkeeping (the Expenses account is debited
   positively, the Asset/Liability/source account is credited, i.e. reduced
   or increased in the opposite direction). The two amounts are always
   exact negatives of one another.
5. **Narration fallback**: if no explicit ``narration`` is supplied to
   ``build_posting_pair``, the (raw, non-normalized) ``purpose`` string is
   used as the narration, so the narration always "contains" the Purpose
   text used to build the posting.
6. **"Credit card" lower-case variant -- RESOLVED, no longer ambiguous**:
   under the current, final "Account Mapping Clarification (2026-10-01)"
   mapping, "Company Card", "Personal Card", and "Credit Card" are three
   separate, distinct source accounts (not aliases of one another). The
   real-CSV value "Credit card" (lower-case "c") normalizes
   case-insensitively to the "credit card" key and correctly resolves to
   ``Liabilities:INR:CreditCard`` -- this is a genuine match, not an
   alias question. (An earlier revision of this mapping conflated
   "Personal Card" and "Credit Card" into a single account, which is why
   this used to be flagged as ambiguous; it no longer is.)
7. **"Cash" payment method -- RESOLVED, now mapped**: per the
   "Complete Payment Account Mapping (2026-10-01)" section of TICKET-009,
   "Cash" is mapped to ``Assets:INR:Cash:CashInHand``. All four real-data
   Payment values (Company Card, Personal Card, Credit Card, Cash) now
   have dedicated accounts; no row in the real CSV needs the
   ``Assets:Uncategorized`` fallback for Payment. (An earlier revision of
   this file had Cash unmapped -- this is now corrected.)
"""

import csv
import re
import os

import pytest


# ---------------------------------------------------------------------------
# Reference / prototype implementation
# ---------------------------------------------------------------------------

PAYMENT_ACCOUNT_MAP = {
    "company card": "Assets:INR:Cash:IDFC:Current",
    "personal card": "Liabilities:INR:CEOBank",
    "credit card": "Liabilities:INR:CreditCard",
    "cash": "Assets:INR:Cash:CashInHand",
}
PAYMENT_FALLBACK_ACCOUNT = "Assets:Uncategorized"

PURPOSE_ACCOUNT_MAP = {
    "food": "Expenses:Food",
    "fuel": "Expenses:Fuel",
    "office supplies": "Expenses:Office Supplies",
    "vehicle maintenance": "Expenses:Vehicle Maintenance",
    "travel": "Expenses:Travel",
}
PURPOSE_FALLBACK_ACCOUNT = "Expenses:Uncategorized"


def _normalize(value):
    """Strip outer whitespace, collapse internal whitespace runs, lowercase.

    None is treated like the empty string (design decision #1).
    """
    if value is None:
        value = ""
    # strip + collapse internal whitespace (design decision #2)
    collapsed = " ".join(value.split())
    return collapsed.lower()


def map_payment_to_account(payment):
    """Map a Payment column value to its source/credit account.

    Case-insensitive, whitespace-tolerant lookup. Falls back to
    Assets:Uncategorized for anything unmapped, blank, or None.
    """
    key = _normalize(payment)
    return PAYMENT_ACCOUNT_MAP.get(key, PAYMENT_FALLBACK_ACCOUNT)


def map_purpose_to_account(purpose):
    """Map a Purpose column value to its expense/debit account.

    Case-insensitive, whitespace-tolerant lookup. Falls back to
    Expenses:Uncategorized for anything unmapped, blank, or None.
    """
    key = _normalize(purpose)
    return PURPOSE_ACCOUNT_MAP.get(key, PURPOSE_FALLBACK_ACCOUNT)


def build_posting_pair(purpose, payment, amount, narration=None):
    """Build a simple double-entry posting pair dict.

    debit_account  = Expenses:[Purpose] (via map_purpose_to_account)
    credit_account = mapped Payment source account (via map_payment_to_account)
    debit_amount   = +amount
    credit_amount  = -amount   (equal and opposite -- design decision #4)
    narration      = explicit narration, or else the raw purpose text
                      (design decision #5)
    """
    debit_account = map_purpose_to_account(purpose)
    credit_account = map_payment_to_account(payment)
    return {
        "debit_account": debit_account,
        "credit_account": credit_account,
        "debit_amount": amount,
        "credit_amount": -amount,
        "narration": narration if narration is not None else (purpose or ""),
    }


# ---------------------------------------------------------------------------
# Payment -> Source Account tests
# ---------------------------------------------------------------------------

class TestPaymentToSourceAccount:
    def test_company_card(self):
        assert map_payment_to_account("Company Card") == "Assets:INR:Cash:IDFC:Current"

    def test_personal_card(self):
        assert map_payment_to_account("Personal Card") == "Liabilities:INR:CEOBank"

    def test_credit_card(self):
        assert map_payment_to_account("Credit Card") == "Liabilities:INR:CreditCard"

    def test_cash(self):
        # Per "Complete Payment Account Mapping (2026-10-01)": Cash maps to
        # its own dedicated account (13/71 real rows, ~18% -- see
        # TestRealCsvIntegration).
        assert map_payment_to_account("Cash") == "Assets:INR:Cash:CashInHand"

    def test_unmapped_value_falls_back(self):
        assert map_payment_to_account("Bag") == "Assets:Uncategorized"

    def test_case_insensitive_company_card_upper(self):
        assert map_payment_to_account("COMPANY CARD") == "Assets:INR:Cash:IDFC:Current"

    def test_case_insensitive_cash_with_padding(self):
        assert map_payment_to_account(" cash ") == "Assets:INR:Cash:CashInHand"

    def test_case_insensitive_personal_card_lower(self):
        assert map_payment_to_account("personal card") == "Liabilities:INR:CEOBank"

    def test_mixed_case_company_card(self):
        assert map_payment_to_account("company CARD") == "Assets:INR:Cash:IDFC:Current"

    def test_internal_whitespace_collapse(self):
        assert map_payment_to_account("Company  Card") == "Assets:INR:Cash:IDFC:Current"

    def test_real_data_credit_card_lowercase_c_matches_credit_card_account(self):
        # Real CSV has "Credit card" (lower-case c). Under the current
        # mapping this is a genuine, non-ambiguous match (see module
        # docstring item 6) -- it resolves to the real Credit Card account,
        # it is not treated as an alias of Personal Card.
        assert map_payment_to_account("Credit card") == "Liabilities:INR:CreditCard"


# ---------------------------------------------------------------------------
# Purpose -> Expense Account tests
# ---------------------------------------------------------------------------

class TestPurposeToExpenseAccount:
    def test_food(self):
        assert map_purpose_to_account("Food") == "Expenses:Food"

    def test_fuel(self):
        assert map_purpose_to_account("Fuel") == "Expenses:Fuel"

    def test_office_supplies(self):
        assert map_purpose_to_account("Office Supplies") == "Expenses:Office Supplies"

    def test_vehicle_maintenance(self):
        assert map_purpose_to_account("Vehicle maintenance") == "Expenses:Vehicle Maintenance"

    def test_travel(self):
        assert map_purpose_to_account("Travel") == "Expenses:Travel"

    def test_unmapped_value_falls_back(self):
        assert map_purpose_to_account("Gardening") == "Expenses:Uncategorized"

    def test_case_insensitive_padding_food(self):
        assert map_purpose_to_account(" food ") == "Expenses:Food"

    def test_case_insensitive_fuel_upper(self):
        assert map_purpose_to_account("FUEL") == "Expenses:Fuel"

    def test_real_data_recipt_bagging(self):
        assert map_purpose_to_account("Recipt bagging") == "Expenses:Uncategorized"

    def test_real_data_closing_new_envelop(self):
        assert map_purpose_to_account("Closing new envelop") == "Expenses:Uncategorized"

    def test_real_data_closing_envelop(self):
        assert map_purpose_to_account("Closing envelop") == "Expenses:Uncategorized"

    def test_real_data_whitespace_quirk_vehicle_maintenance(self):
        # Real sample data: double internal space + trailing space.
        assert map_purpose_to_account("Vehicle  maintenance ") == "Expenses:Vehicle Maintenance"

    def test_real_data_test_value_capital(self):
        assert map_purpose_to_account("Test") == "Expenses:Uncategorized"

    def test_real_data_test_value_lower(self):
        assert map_purpose_to_account("test") == "Expenses:Uncategorized"


# ---------------------------------------------------------------------------
# Double-entry posting tests
# ---------------------------------------------------------------------------

class TestDoubleEntryPosting:
    def test_debit_account_is_expense_for_purpose(self):
        posting = build_posting_pair("Food", "Company Card", 500.0)
        assert posting["debit_account"] == "Expenses:Food"

    def test_credit_account_is_mapped_payment_account(self):
        posting = build_posting_pair("Food", "Company Card", 500.0)
        assert posting["credit_account"] == "Assets:INR:Cash:IDFC:Current"

    def test_amounts_are_equal_and_opposite(self):
        posting = build_posting_pair("Fuel", "Cash", 1000.0)
        assert posting["debit_amount"] == 1000.0
        assert posting["credit_amount"] == -1000.0
        assert posting["debit_amount"] == -posting["credit_amount"]

    def test_narration_contains_purpose_text(self):
        posting = build_posting_pair("Travel", "Personal Card", 30.0)
        assert "Travel" in posting["narration"]

    def test_explicit_narration_overrides_default(self):
        posting = build_posting_pair("Travel", "Personal Card", 30.0, narration="Cab to airport")
        assert posting["narration"] == "Cab to airport"

    def test_full_posting_consistency_personal_card(self):
        posting = build_posting_pair("Office Supplies", "Personal Card", 3847.0)
        assert posting["debit_account"] == "Expenses:Office Supplies"
        assert posting["credit_account"] == "Liabilities:INR:CEOBank"
        assert posting["debit_amount"] + posting["credit_amount"] == 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string_purpose(self):
        assert map_purpose_to_account("") == "Expenses:Uncategorized"

    def test_empty_string_payment(self):
        assert map_payment_to_account("") == "Assets:Uncategorized"

    def test_none_purpose_treated_like_empty(self):
        assert map_purpose_to_account(None) == "Expenses:Uncategorized"

    def test_none_payment_treated_like_empty(self):
        assert map_payment_to_account(None) == "Assets:Uncategorized"

    def test_purpose_with_special_characters(self):
        assert map_purpose_to_account("USB cables, boxes, snacks") == "Expenses:Uncategorized"

    def test_very_long_purpose_string_does_not_crash(self):
        long_purpose = "X" * 300
        result = map_purpose_to_account(long_purpose)
        assert result == "Expenses:Uncategorized"

    def test_credit_card_lowercase_c_matches_its_own_account_not_personal_card(self):
        # Real data has "Credit card" (lowercase c). Under the current,
        # final mapping, Credit Card is its own distinct account (not an
        # alias of Personal Card) -- see module docstring item 6.
        assert map_payment_to_account("Credit card") == "Liabilities:INR:CreditCard"
        assert map_payment_to_account("Credit card") != "Liabilities:INR:CEOBank"

    def test_build_posting_pair_with_blank_payment_and_purpose(self):
        posting = build_posting_pair("", "", 0.0)
        assert posting["debit_account"] == "Expenses:Uncategorized"
        assert posting["credit_account"] == "Assets:Uncategorized"


# ---------------------------------------------------------------------------
# Integration test against the real exported CSV
# ---------------------------------------------------------------------------

REAL_CSV_PATH = "/prj/ip/claude/Accounts.csv"


class TestRealCsvIntegration:
    @pytest.mark.skipif(
        not os.path.exists(REAL_CSV_PATH),
        reason=f"real sample CSV not found at {REAL_CSV_PATH}",
    )
    def test_every_row_maps_without_crashing_and_exercises_fallbacks(self):
        resolved_debit_accounts = set()
        resolved_credit_accounts = set()
        row_count = 0

        with open(REAL_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                purpose = row.get("Purpose", "")
                payment = row.get("Payment", "")
                amount_raw = row.get("Amount", "")

                # Amount "O" (letter O, not zero) appears in one real row.
                # Not relevant to mapping logic -- just don't let it crash.
                try:
                    amount = float(amount_raw)
                except (TypeError, ValueError):
                    amount = 0.0

                try:
                    posting = build_posting_pair(purpose, payment, amount)
                except Exception as exc:  # pragma: no cover - should never trigger
                    pytest.fail(
                        f"build_posting_pair raised {exc!r} for row "
                        f"Purpose={purpose!r} Payment={payment!r} Amount={amount_raw!r}"
                    )

                assert isinstance(posting["debit_account"], str) and posting["debit_account"]
                assert isinstance(posting["credit_account"], str) and posting["credit_account"]

                resolved_debit_accounts.add(posting["debit_account"])
                resolved_credit_accounts.add(posting["credit_account"])

        assert row_count > 0, "CSV appears to be empty -- nothing was tested"

        # Fallback paths must actually be exercised by real-world data,
        # not just by synthetic unit tests.
        assert PURPOSE_FALLBACK_ACCOUNT in resolved_debit_accounts, (
            "Expected at least one real CSV row to fall back to "
            f"{PURPOSE_FALLBACK_ACCOUNT}, but it never appeared. "
            f"Resolved debit accounts: {resolved_debit_accounts}"
        )
        assert PAYMENT_FALLBACK_ACCOUNT in resolved_credit_accounts, (
            "Expected at least one real CSV row to fall back to "
            f"{PAYMENT_FALLBACK_ACCOUNT}, but it never appeared. "
            f"Resolved credit accounts: {resolved_credit_accounts}"
        )

        # Sanity: the known mapped accounts should also show up in real data.
        assert "Expenses:Food" in resolved_debit_accounts
        assert "Expenses:Fuel" in resolved_debit_accounts
        assert "Assets:INR:Cash:IDFC:Current" in resolved_credit_accounts  # Company Card
        assert "Liabilities:INR:CEOBank" in resolved_credit_accounts      # Personal Card
        assert "Liabilities:INR:CreditCard" in resolved_credit_accounts  # Credit Card
        assert "Assets:INR:Cash:CashInHand" in resolved_credit_accounts  # Cash
        # Remaining unmapped real Payment values ('', "Bag", "Test", "test")
        # still correctly exercise the Assets:Uncategorized fallback path
        # asserted above -- all four known Payment values now have their
        # own dedicated account per "Complete Payment Account Mapping
        # (2026-10-01)".


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
