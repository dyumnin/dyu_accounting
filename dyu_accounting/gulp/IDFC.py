from beancount_reds_importers.libreader import xlsxreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(xlsxreader.Importer, banking.Importer):
    IMPORTER_NAME = "Google Form Data"

    def custom_init(self):
        self.filename_pattern_def = 'IDFC.*'
        self.column_labels_line = 'Transaction Date,Value Date,Particulars,Cheque No.,Debit,Credit,Balance'
        self.currency="INR"

        self.header_identifier = 'STATEMENT OF ACCOUNT'
        self.date_format = '%d-%b-%Y'
        self.header_map = {
            'Value Date': 'date',
            'Particulars': 'memo',
            'Debit': 'withdrawal',
            'Credit': 'deposit',
            'Balance': 'balance',
            'Cheque No.':'payee'
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        rdr = rdr.addfield('amount',
                           lambda x: "-" + str(x['Debit']) if x['Debit'] != None else str(x['Credit']))
        return rdr
    def skip_transaction(self,row):
        if row.date is None:
            print(f"skipping {row}")
        return row.date is None
