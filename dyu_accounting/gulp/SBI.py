
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
import re


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "SBI YONO TSV File"

    def custom_init(self):
        self.filename_pattern_def = 'SBI'
        self.column_labels_line = 'Txn Date,Value Date,Description,Ref No./Cheque No.,Branch Code,Debit,Credit,Balance'
        self.currency="INR"

        self.header_identifier = 'Account Name'
        self.date_format = '%d %b %Y'
        self.header_map = {
            'Txn Date': 'date',
            'Description': 'memo',
            'Debit': 'withdrawal',
            'Credit': 'deposit',
            'Balance': 'balance',
            'Ref No./Cheque No.':'payee'
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        rdr = rdr.addfield('amount',
                           #lambda x: "-" + str(x['Debit']) if x['Debit'] != None else str(x['Credit']))
                           self._clean_table
                           )
        return rdr
    def _clean_table(self,x):
        debit= 0 if (re.match(r'^\s*$',x['Debit'])) else float(x['Debit'])
        credit= 0 if (re.match(r'^\s*$',x['Credit'])) else float(x['Credit'])
        return credit - debit


    def skip_transaction(self,row):
        if row.date is None:
            print(f"skipping {row}")
        return row.date is None
