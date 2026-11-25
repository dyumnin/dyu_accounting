import datetime
import logging
from decimal import Decimal

from forex_python.converter import CurrencyRates

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Upworks Transaction Report"

    # Transaction type column -> second leg. Matched case-insensitively
    # against the 'Transaction type' column.
    #   - WHT/Service Fee/Withdrawal Fee: the cost of using Upwork.
    #   - Withdrawal (the principal amount - a separate row per withdrawal
    #     from 'Withdrawal Fee', same Transaction ID): money actually leaving
    #     the Upwork USD wallet for the bank, so it's a transfer straight to
    #     IDFC, not income.
    #   - Everything else (Hourly, Fixed-price earnings, ...) falls back to
    #     TARGET_FALLBACK_ACCOUNT - these are income, recognized into the INR
    #     receivable account (money earned but not yet withdrawn), which a
    #     withdrawal then draws down.
    TARGET_ACCOUNT_MAP = {
        "wht": "Expenses:USD:Upwork:WHT",
        "service fee": "Expenses:USD:Upwork:ServiceFee",
        "withdrawal fee": "Expenses:USD:Upwork:WithdrawalFee",
        "withdrawal": "Assets:INR:Cash:IDFC:Current",
    }
    TARGET_FALLBACK_ACCOUNT = "Assets:INR:Cash:AccountReceivable:Upwork"

    def custom_init(self):
        # Upwork's own export is actually named '<date>_transaction_report.csv',
        # not prefixed with 'Upworks' as originally assumed.
        self.filename_pattern_def = r'(Upworks|.*transaction_report).*'
        # Real header: Date,Transaction ID,Transaction type,Transaction summary,
        # Transaction summary details,Description 1,Description 2,Description 3,
        # Agency team,Freelancer,Client team,Account name,PO,Ref ID,Amount $,
        # Amount in local currency,Currency,Current balance $,Payment method
        # Only a stable subset is listed here (skip_until_main_table only checks
        # that these show up in the header row, not that the row matches exactly),
        # so added/reordered columns don't break matching.
        self.column_labels_line = 'Date,Transaction type,Description 1,Account name,Amount $,Current balance $'
        self.currency = "USD"
        self.header_identifier = 'Date'
        self.date_format = '%b %d, %Y'
        self.header_map = {
            'Date': 'date',
            'Transaction type': 'txn_type',
            'Description 1': 'memo',
            'Amount $': 'amount',
            'Current balance $': 'balance',
            'Account name': 'payee',
        }
        self.skip_transaction_types = ['Journal']
        self._rates = CurrencyRates()
        self._rate_cache = {}

    def _get_rate(self, date):
        """Look up the historical USD/INR rate for a date, caching per date.

        Mirrors the manual GoogleFinance lookup previously done in Excel to
        produce 'Exchange Rate'/'Converted Value' columns.
        """
        if date not in self._rate_cache:
            try:
                rate = self._rates.get_rate(
                    'USD', 'INR', datetime.datetime(date.year, date.month, date.day)
                )
                # Go through str() so the Decimal doesn't inherit binary-float
                # imprecision (D() does a plain Decimal(float) otherwise).
                self._rate_cache[date] = Decimal(str(round(rate, 6)))
            except Exception as err:
                logging.warning("Could not fetch USD/INR rate for %s: %s", date, err)
                self._rate_cache[date] = None
        return self._rate_cache[date]

    def prepare_table(self, rdr):
        def rate_for_row(row):
            date = datetime.datetime.strptime(row['Date'].strip(), self.date_format).date()
            return self._get_rate(date)

        rdr = rdr.addfield('foreign_amount', rate_for_row)
        rdr = rdr.addfield('foreign_currency', lambda row: 'INR' if row['foreign_amount'] else None)
        return rdr

    def get_target_account(self, ot):
        """Transaction type column -> expense/receivable account.

        Overrides banking.Importer.get_target_account (normally
        self.config.get("target_account"), a single fixed account) so each
        row gets the right second leg, turning these from single-leg
        unbalanced transactions into complete double-entry ones.
        """
        txn_type = (getattr(ot, "txn_type", None) or "").strip().lower()
        return self.TARGET_ACCOUNT_MAP.get(txn_type, self.TARGET_FALLBACK_ACCOUNT)

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
