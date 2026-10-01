from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
from pudb import set_trace


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Upworks Transaction Report"

    def custom_init(self):
        self.filename_pattern_def = 'Upworks.*'
        self.column_labels_line = 'Date,Ref ID,Type,Description,Agency,Freelancer,Team,Account Name,PO,Amount,ExchangeRate,Currency,Balance'
        self.currency="USD"
        #set_trace()

        self.header_identifier = ''
        self.date_format = '%b %d, %Y'
        self.header_map = {
            'Date': 'date',
            'Description': 'memo',
            'Amount': 'amount',
            'Balance': 'balance',
            'Account Name':'payee',
            'ExchangeRate': 'rate'

        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        return rdr
    def skip_transaction(self,row):
        if row.date is None:
            print(f"skipping {row}")
        return row.date is None
