import logging
import re
import petl
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "SBI YONO TSV File"
    # The YONO app export is plain tab-separated text saved with a '.xls' extension,
    # not an actual binary Excel file, so it has to be accepted alongside '.csv'.
    FILE_EXTS = ["csv", "xls"]

    def custom_init(self):
        # SBI exports come in two flavors in the wild: a comma-delimited CSV from
        # net-banking (e.g. 'SBIBankStatement.csv') and a tab-delimited export from
        # the YONO app named 'Account_Statement_<ref>.xls' (despite the extension,
        # it's plain tab-separated text).
        self.filename_pattern_def = r'(SBI|Account_Statement).*'
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

    def read_raw(self, file):
        # Detect comma vs. tab delimiting rather than assuming one, since both
        # real-world SBI export formats need to be supported.
        with open(file.name, encoding='utf-8', errors='ignore') as f:
            sample = f.read(8192)
        delimiter = '\t' if sample.count('\t') > sample.count(',') else ','
        return petl.fromcsv(file.name, delimiter=delimiter)

    def prepare_raw_file(self, rdr):
        # The YONO TSV export pads cells with fixed-width whitespace (e.g. a
        # header cell of '        Debit'), which breaks the base reader's literal
        # header-row matching. Strip every cell so header/data line up cleanly
        # regardless of which export format produced the file.
        def strip_rows(rows):
            for row in rows:
                yield tuple(v.strip() if isinstance(v, str) else v for v in row)
        return petl.wrap(list(strip_rows(rdr)))

    def prepare_table(self, rdr):
        # SBI exports unquoted comma-formatted amounts (e.g. 1,770.00) in a comma-delimited
        # CSV, causing the CSV parser to split one amount into multiple fields.  petl tables
        # are lazy, so rowmap intercepts each row before materialisation and re-joins the
        # split fragments back into the expected 8-column schema.
        expected = self.column_labels_line.split(',')
        rdr = petl.rowmap(rdr, self._fix_split_amounts, header=expected)
        rdr = rdr.addfield('amount', self._clean_table)
        return rdr

    def _fix_split_amounts(self, row):
        """Re-join amount columns that the CSV parser split on Indian comma formatting."""
        expected = self.column_labels_line.split(',')
        n = len(expected)           # 8
        n_prefix = 5                # non-numeric columns: TxnDate,ValDate,Desc,Ref,Branch
        row = list(row)
        if len(row) <= n:
            return (row + [None] * n)[:n]
        prefix = row[:n_prefix]
        fragments = [str(v) for v in row[n_prefix:]]
        merged = self._merge_amount_fragments(fragments)
        # Guarantee exactly 3 amount fields (Debit, Credit, Balance)
        return prefix + (merged + ['0'] * 3)[:3]

    @staticmethod
    def _merge_amount_fragments(fragments):
        """Group CSV fragments back into comma-formatted amounts.

        The CSV parser splits '1,770.00' into ['1', '770.00'].  A fragment that
        contains a decimal point ends the current number; a whitespace-only
        fragment is a standalone empty-amount marker (SBI uses ' ' for blank).
        """
        amounts = []
        current = []
        for f in fragments:
            if re.match(r'^\s*$', f):
                if current:
                    amounts.append(','.join(current))
                    current = []
                amounts.append(f)
            else:
                current.append(f)
                if '.' in f:
                    amounts.append(','.join(current))
                    current = []
        if current:
            amounts.append(','.join(current))
        return amounts

    def _clean_table(self, x):
        debit = self._parse_amount(x.Debit)
        credit = self._parse_amount(x.Credit)
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
