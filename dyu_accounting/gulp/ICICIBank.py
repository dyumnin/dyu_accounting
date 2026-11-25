import logging
from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = "ICICI Bank Importer"

    def custom_init(self):
        self.filename_pattern_def = 'OpTrans.*'
        # Real header has no spaces around the '(INR)' suffix (e.g.
        # 'Withdrawal Amount(INR)'), unlike what was originally assumed here.
        self.column_labels_line = 'S No.,Value Date,Transaction Date,Cheque Number,Transaction Remarks,Withdrawal Amount(INR),Deposit Amount(INR),Balance(INR)'
        self.currency = "INR"
        self.header_identifier = 'DETAILED STATEMENT'
        self.date_format = '%d/%m/%Y'
        self.header_map = {
            'S No.': 'payee',
            'Value Date': 'date',
            'Transaction Remarks': 'memo',
            'Withdrawal Amount(INR)': 'withdrawal',
            'Deposit Amount(INR)': 'deposit',
            'Balance(INR)': 'balance',
        }
        self.skip_transaction_types = ['Journal']

    def prepare_raw_file(self, rdr):
        # The real export has a stray blank leading column (before 'S No.') on
        # every row, including the real header row. Left in place, that column's
        # empty '' field name survives renaming and breaks namedtuple conversion
        # later (namedtuple field names must be valid identifiers).
        return rdr.cutout(0)

    def prepare_table(self, rdr):
        wd = 'Withdrawal Amount(INR)'
        dep = 'Deposit Amount(INR)'

        def to_amount(x):
            # Real export's amount cells are text (e.g. '0.00' for "no
            # withdrawal"), not numeric, so they can't be negated directly, and
            # a blank-check against '' or 0 misses the text '0.00' case.
            withdrawal = self._to_float(x[wd])
            if withdrawal:
                return str(-withdrawal)
            deposit = self._to_float(x[dep])
            return str(deposit) if deposit else '0'

        rdr = rdr.addfield('amount', to_amount)
        return rdr

    @staticmethod
    def _to_float(v):
        if v in (None, ''):
            return 0.0
        return float(v)

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
