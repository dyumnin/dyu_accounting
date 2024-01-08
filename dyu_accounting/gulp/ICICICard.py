import locale
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "ICICI Bank Credit Card"
    print(IMPORTER_NAME)

    def custom_init(self):
        self.currency = "INR"
        # self.filename_pattern_def = '.*43755.*'
        self.filename_pattern_def = '.*'
        self.column_labels_line = 'Date,Sr.No.,Transaction Details,Reward Point Header,Intl.Amount,Amount(in Rs),BillingAmountSign'
        self.header_identifier = '"Accountno:"'
        self.date_format = '%d-%b-%y'
        self.header_map = {
            'Sr.No.': 'payee',
            'Intl.Amount': 'Intl Amount',
            'Reward Point Header': 'Reward Point',
            'Date': 'date',
            'Transaction Details': 'memo',
            'Amount(in Rs)': 'AIR',
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
        amt = 'Amount(in Rs)'
        for i,r in rdr.enumerate():
            print(r[i])
        if rdr["Date"] is not None:
            rdr = rdr.addfield('amount',
                               #lambda x:print(x))
                               lambda x:"-" + str(x[amt]) if locale.atof(x[amt]) > 0 else str(0-locale.atof(x[amt])))
        return rdr

    def skip_transaction(self, row):
        if row.date is None:
            print(f"skipping {row}")
        return row.date is None
