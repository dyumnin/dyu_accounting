import logging
from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = "ICICI Bank Importer"

    def custom_init(self):
        self.filename_pattern_def = 'OpTrans.*'
        self.column_labels_line = 'S No.,Value Date,Transaction Date,Cheque Number,Transaction Remarks,Withdrawal Amount (INR ),Deposit Amount (INR ),Balance (INR )'
        self.currency = "INR"
        self.header_identifier = 'DETAILED STATEMENT'
        self.date_format = '%d/%m/%Y'
        self.header_map = {
            'S No.': 'payee',
            'Value Date': 'date',
            'Transaction Remarks': 'memo',
            'Withdrawal Amount (INR )': 'withdrawal',
            'Deposit Amount (INR )': 'deposit',
            'Balance (INR )': 'balance',
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        wd = 'Withdrawal Amount (INR )'
        dep = 'Deposit Amount (INR )'
        rdr = rdr.addfield('amount',
                           lambda x: str(-x[wd]) if x[wd] not in (None, '', 0) else str(x[dep] or 0))
        return rdr

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
