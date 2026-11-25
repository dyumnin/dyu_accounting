import datetime
import logging
from decimal import Decimal

from forex_python.converter import CurrencyRates

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Upworks Transaction Report"

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

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
