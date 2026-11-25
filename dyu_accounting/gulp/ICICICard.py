import logging
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "ICICI Bank Credit Card"

    def custom_init(self):
        self.currency = "INR"
        self.filename_pattern_def = 'CreditCard'
        self.column_labels_line = 'Date,Sr.No.,Transaction Details,Reward Point Header,Intl.Amount,Amount(in Rs),BillingAmountSign'
        self.header_identifier = '"Accountno:"'
        self.date_format = '%d-%b-%y'
        self.header_map = {
            'Sr.No.': 'payee',
            'Intl.Amount': 'Intl Amount',
            'Reward Point Header': 'Reward Point',
            'Date': 'date',
            'Transaction Details': 'memo',
            # Renamed (not to 'amount' - prepare_table() below already adds a
            # computed 'amount' field from this same raw column, and mapping
            # this one to 'amount' too would produce two fields both named
            # 'amount', crashing namedtuple() construction downstream).
            # Also can't be left unmapped: fix_column_names()'s regex only
            # replaces '-', '/' and ' ', not parentheses, so the raw name
            # 'Amount(in Rs)' would become the invalid identifier
            # 'Amount(in_Rs)' and crash namedtuple() the same way.
            'Amount(in Rs)': 'amount_raw',
        }
        self.skip_transaction_types = ['Journal']

    @staticmethod
    def _parse_inr(s):
        """Parse an INR amount string that may contain commas (e.g. '1,23,456.78')."""
        return float(str(s).replace(',', ''))

    def prepare_table(self, rdr):
        amt = 'Amount(in Rs)'
        # CSV debits are positive, credits are negative; negate to match beancount sign convention.
        rdr = rdr.addfield('amount',
                           lambda x: str(-self._parse_inr(x[amt])) if x[amt] not in (None, '') else '0')
        return rdr

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
