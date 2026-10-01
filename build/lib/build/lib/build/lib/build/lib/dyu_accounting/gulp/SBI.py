# importers/sbi_ca_csv.py
"""bean-gulp importer for SBI current-account CSV (retail internet banking)"""

from __future__ import annotations

import csv
import datetime as dt
import re
from typing import Any, Dict, List, Optional

from beancount.core.amount import Amount
from beancount.core.data import (
    Balance,
    Directive,
    Meta,
    Posting,
    Transaction,
    new_metadata,
)
from beancount.core.number import D
from beangulp import DateUtils, Importer, utils
from beangulp.importers.mixins import (
    IdentifyMixin,
    FilingMixin,
)

META_KEYS = (
    "txn_date",
    "value_date",
    "description",
    "ref_no",
    "branch_code",
    "debit",
    "credit",
    "balance",
)


class SbiCaCsvImporter(IdentifyMixin, FilingMixin, Importer):
    """Importer for SBI current-account CSV files."""

    # --- configuration ------------------------------------------------------
    def __init__(
        self,
        account: str,
        currency: str = "INR",
        account_name_regex: str | None = None,
    ):
        """
        account: Beancount account that holds the money (e.g. Assets:IN:SBI:CA:Surabhi)
        currency: currency of the account
        account_name_regex: optional extra safety – regex that has to match the
                            “Account Name” field in the header
        """
        self.account = account
        self.currency = currency
        self.account_name_regex = re.compile(account_name_regex) if account_name_regex else None

        # --- beangulp mixins -------------------------------------------------
        # Identify by the exact header line that starts the transaction section
        self.matchers = [
            ("content", "Txn Date\tValue Date\tDescription\tRef No./Cheque No.\tBranch Code\tDebit\tCredit\tBalance")
        ]

    # -------------------------------------------------------------------------
    def extract(
        self, filepath: str, existing: Optional[List[Directive]] = None
    ) -> List[Directive]:
        """Parse CSV and yield Beancount directives."""
        entries: List[Directive] = []
        with open(filepath, newline="", encoding="utf-8") as fd:
            # skip everything until the header line
            reader = csv.DictReader(
                utils.dropwhile_reader(
                    fd,
                    lambda row: row[0].strip() != "Txn Date",
                ),
                delimiter="\t",
            )

            for row in reader:
                entries.extend(self._process_row(row, filepath))

        return entries

    # -------------------------------------------------------------------------
    def _process_row(self, row: Dict[str, Any], filepath: str) -> List[Directive]:
        """Convert one CSV row into Transaction (+ optional Balance)."""
        meta = new_metadata(filepath, 0)  # line numbers not useful here
        date = DateUtils.parse_date(row["Txn Date"], fmt="%d %b %Y")
        amt_debit = self._to_decimal(row["Debit"])
        amt_credit = self._to_decimal(row["Credit"])
        balance = self._to_decimal(row["Balance"])

        if amt_debit and amt_credit:
            raise ValueError("Row has both debit and credit – unexpected")
        if not (amt_debit or amt_credit):
            # some banks write 0/0 rows – ignore
            return []

        units = amt_credit if amt_credit else -amt_debit
        units = Amount(units, self.currency)

        # attach original row as metadata
        for k in META_KEYS:
            meta[k] = row.get(k, "")

        txn = Transaction(
            meta=meta,
            date=date,
            flag="*",
            payee="",
            narration=row["Description"].strip(),
            tags=set(),
            links=set(),
            postings=[
                Posting(
                    account=self.account,
                    units=units,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                Posting(
                    account="Expenses:TODO",
                    units=-units,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ],
        )

        # optional: emit a Balance directive on the last row of the file
        # (beangulp will keep only the latest one automatically)
        bal = Balance(
            meta=new_metadata(filepath, 0),
            date=date,
            account=self.account,
            amount=Amount(balance, self.currency),
            tolerance=None,
            diff_amount=None,
        )

        return [txn, bal]

    # -------------------------------------------------------------------------
    @staticmethod
    def _to_decimal(value: str) -> Optional[D]:
        """Convert Indian number format (12,345.67) to Decimal."""
        if not value or value.strip() == "":
            return None
        value = value.replace(",", "")
        return D(value)


# -------------------------------------------------------------------------
# beangulp hook – this is what bean-gulp calls
def get_importer(config_dict: Dict[str, Any]) -> SbiCaCsvImporter:
    """Factory function expected by bean-gulp."""
    return SbiCaCsvImporter(
        account=config_dict["account"],
        currency=config_dict.get("currency", "INR"),
        account_name_regex=config_dict.get("account_name_regex"),
    )
