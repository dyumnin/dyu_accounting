import logging
import re
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "SBI YONO TSV File"

    def custom_init(self):
        self.filename_pattern_def = 'SBI'
        self.column_labels_line = 'Txn Date,Value Date,Description,Ref No./Cheque No.,Branch Code,Debit,Credit,Balance'
        self.currency = "INR"
        self.header_identifier = 'Account Name'
        self.date_format = '%d %b %Y'
        self.header_map = {
            'Txn Date': 'date',
            'Description': 'memo',
            'Debit': 'withdrawal',
            'Credit': 'deposit',
            'Balance': 'balance',
            'Ref No./Cheque No.': 'payee',
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        rdr = rdr.addfield('amount', self._clean_table)
        return rdr

    def _clean_table(self, x):
        debit = self._parse_amount(x['Debit'])
        credit = self._parse_amount(x['Credit'])
        return str(credit - debit)

    @staticmethod
    def _parse_amount(v):
        """Parse an amount that may be blank, None, or use Indian lakh comma formatting."""
        if v is None or re.match(r'^\s*$', str(v)):
            return 0.0
        return float(str(v).replace(',', ''))

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
