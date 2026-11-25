import logging

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Google Form Data"

    # Payment column -> source/credit account (where the money came from).
    # Matched case-insensitively (strip + collapse internal whitespace, then
    # lowercase) against the Payment column. Covers all four real-data
    # Payment values (see TICKET-009); PAYMENT_FALLBACK_ACCOUNT below handles
    # anything else (blank, typos, placeholder test rows, etc).
    PAYMENT_ACCOUNT_MAP = {
        "company card": "Assets:INR:Cash:IDFC:Current",
        "personal card": "Liabilities:INR:CEOBank",
        "credit card": "Liabilities:INR:CreditCard",
        "cash": "Assets:INR:Cash:CashInHand",
    }
    PAYMENT_FALLBACK_ACCOUNT = "Assets:Uncategorized"

    # Purpose column -> expense/debit account (where the money went).
    # Matched the same way as Payment above.
    PURPOSE_ACCOUNT_MAP = {
        "food": "Expenses:Food",
        "fuel": "Expenses:Fuel",
        "office supplies": "Expenses:Office Supplies",
        "vehicle maintenance": "Expenses:Vehicle Maintenance",
        "travel": "Expenses:Travel",
    }
    PURPOSE_FALLBACK_ACCOUNT = "Expenses:Uncategorized"

    def custom_init(self):
        self.currency = 'INR'
        self.filename_pattern_def = 'Accounts.*'
        self.column_labels_line = 'Timestamp,Date,Amount,Purpose,Payment,Receipt'
        self.header_identifier = 'Timestamp,Date,Amount,Purpose,Payment,Receipt'
        # The real Google Form export's Date column is US-style M/D/YYYY
        # (e.g. '5/25/2024'), not D/M/YYYY - confirmed by day values (16, 17,
        # 21, 25, 28...) landing in the month position, which silently
        # produced date=None for every such row (petl.convert() swallows the
        # strptime ValueError rather than raising), and those None dates then
        # crashed extraction downstream with AttributeError on ot.date.date().
        self.date_format = '%m/%d/%Y'
        self.header_map = {
            'Date': 'date',
            'Purpose': 'memo',
            'Amount': 'amount',
        }
        self.skip_transaction_types = ['Journal']
        # Payment and Receipt are intentionally left out of header_map so
        # they pass through unrenamed (accessible as ot.Payment/ot.Receipt);
        # Payment drives get_main_account() below, Receipt drives
        # build_metadata() below.

    def prepare_table(self, rdr):
        rdr = rdr.addfield('payee', '')
        return rdr

    @staticmethod
    def _normalize(value):
        """Strip outer whitespace, collapse internal whitespace runs, lowercase.

        None is treated the same as the empty string.
        """
        if value is None:
            value = ""
        return " ".join(value.split()).lower()

    def get_main_account(self, ot):
        """Payment column -> source/credit account.

        Overrides banking.Importer.get_main_account (normally a static
        self.config["main_account"]) because the source account varies
        per-row here, driven by the Payment column, rather than being fixed
        per imported file.
        """
        payment = self._normalize(getattr(ot, "Payment", ""))
        return self.PAYMENT_ACCOUNT_MAP.get(payment, self.PAYMENT_FALLBACK_ACCOUNT)

    def get_target_account(self, ot):
        """Purpose column (ot.memo) -> expense/debit account."""
        purpose = self._normalize(getattr(ot, "memo", ""))
        return self.PURPOSE_ACCOUNT_MAP.get(purpose, self.PURPOSE_FALLBACK_ACCOUNT)

    def skip_transaction(self, row):
        # Guards against a bad/unparseable date silently reaching
        # banking.Importer.extract(), which otherwise crashes with
        # AttributeError on ot.date.date() - every other importer in this
        # package has this same guard; this one was missing it, which is why
        # that crash went unnoticed (it's swallowed by find_imports()'s
        # logging.exception() rather than being visible).
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None

    def build_metadata(self, file, metatype=None, data={}):
        meta = super().build_metadata(file, metatype, data)
        if metatype == "transaction":
            ot = data.get("transaction")
            receipt = getattr(ot, "Receipt", None)
            if receipt:
                meta["receipt"] = receipt
        return meta
