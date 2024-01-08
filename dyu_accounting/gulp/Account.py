from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Google Form Data"

    def custom_init(self):
        self.currency = 'INR'
        self.filename_pattern_def = 'Accounts .*'
        self.column_labels_line = 'Timestamp,Date,Transaction Title,Amount,Paid from Account,Credit to Account,Receipt'
        self.header_identifier = 'Timestamp,Date,Transaction Title,Amount,Paid from Account,Credit to Account,Receipt'
        self.date_format = '%d/%m/%Y'
        self.header_map = {
            'Date': 'date',
            'Transaction Title': 'memo',
            'Amount': 'amount'
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        rdr = rdr.addfield('payee', '')
        print(rdr)
        return rdr
