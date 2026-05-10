"""
Unit tests for the bank statement ingesters in dyu_accounting/gulp/.

Test rows are built from the exact column headers and real-world sample
data from each bank's exported file format.
"""
import importlib
import io
from types import SimpleNamespace

import pytest

petl = pytest.importorskip('petl', reason='petl is required by beancount_reds_importers')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_importer(module_name):
    """Instantiate an Importer calling only custom_init (bypasses base-class __init__)."""
    mod = importlib.import_module(f'dyu_accounting.gulp.{module_name}')
    imp = object.__new__(mod.Importer)
    mod.Importer.custom_init(imp)
    return imp


def prepare_rows(imp, rows):
    """Run prepare_table on a list-of-dicts and return results as a list of dicts."""
    tbl = petl.fromdicts(rows)
    result = imp.prepare_table(tbl)
    return list(petl.dicts(result))


def skip_row(**kwargs):
    return SimpleNamespace(**kwargs)


# ---------------------------------------------------------------------------
# ICICICard
# Headers: Date,Sr.No.,Transaction Details,Reward Point Header,
#          Intl.Amount,Amount(in Rs),BillingAmountSign
#
# Real sample (CreditCardStatement_24_25.CSV):
#   "Accountno:","1111111111222223"         <- header_identifier line
#   ...
#   "Date","Sr.No.","Transaction Details","Reward Point Header","Intl.Amount","Amount(in Rs)","BillingAmountSign"
#   "01-APR-24","1","DIGITALOCEAN.COM AMSTERDAM NL*","10","6.00","521.17","521.17"
#   "02-APR-24","2","AVENUE SUPERMARTS LTD- BANGALORE IN","14","0.00","718.61","718.61"
# ---------------------------------------------------------------------------

class TestICICICardParseINR:
    """_parse_inr must handle plain decimals and Indian lakh comma formatting."""

    def test_plain_decimal(self):
        from dyu_accounting.gulp.ICICICard import Importer
        assert Importer._parse_inr('521.17') == pytest.approx(521.17)

    def test_plain_decimal_large(self):
        from dyu_accounting.gulp.ICICICard import Importer
        assert Importer._parse_inr('718.61') == pytest.approx(718.61)

    def test_thousands_comma(self):
        from dyu_accounting.gulp.ICICICard import Importer
        assert Importer._parse_inr('1,000.00') == pytest.approx(1000.0)

    def test_indian_lakh_format(self):
        from dyu_accounting.gulp.ICICICard import Importer
        assert Importer._parse_inr('1,23,456.78') == pytest.approx(123456.78)

    def test_negative(self):
        from dyu_accounting.gulp.ICICICard import Importer
        assert Importer._parse_inr('-500.00') == pytest.approx(-500.0)


class TestICICICardPrepareTable:
    """
    Real dates use uppercase months (01-APR-24).  Python's %d-%b-%y handles
    this case-insensitively.  Amounts are positive decimals (debits); they
    must be negated to follow beancount's sign convention.
    """
    AMT = 'Amount(in Rs)'

    def _row(self, date, sr, narration, reward, intl, amount, billing_sign):
        return {
            'Date': date, 'Sr.No.': sr, 'Transaction Details': narration,
            'Reward Point Header': reward, 'Intl.Amount': intl,
            self.AMT: amount, 'BillingAmountSign': billing_sign,
        }

    def test_debit_digitalocean(self):
        """01-APR-24, 521.17 → amount = -521.17"""
        imp = make_importer('ICICICard')
        rows = prepare_rows(imp, [self._row('01-APR-24', '1',
                                            'DIGITALOCEAN.COM AMSTERDAM NL*',
                                            '10', '6.00', '521.17', '521.17')])
        assert float(rows[0]['amount']) == pytest.approx(-521.17)

    def test_debit_supermarket(self):
        """02-APR-24, 718.61 → amount = -718.61"""
        imp = make_importer('ICICICard')
        rows = prepare_rows(imp, [self._row('02-APR-24', '2',
                                            'AVENUE SUPERMARTS LTD- BANGALORE IN',
                                            '14', '0.00', '718.61', '718.61')])
        assert float(rows[0]['amount']) == pytest.approx(-718.61)

    def test_credit_refund(self):
        """Negative amount in CSV (credit/refund) → positive in beancount."""
        imp = make_importer('ICICICard')
        rows = prepare_rows(imp, [self._row('15-MAY-24', '3', 'REFUND',
                                            '0', '0.00', '-200.00', '-200.00')])
        assert float(rows[0]['amount']) == pytest.approx(200.0)

    def test_none_amount_returns_zero(self):
        imp = make_importer('ICICICard')
        rows = prepare_rows(imp, [self._row('01-JUN-24', '4', 'X',
                                            '0', '0.00', None, None)])
        assert rows[0]['amount'] == '0'

    def test_large_amount_with_commas(self):
        """Amount like 1,23,456.00 is parsed correctly after comma stripping."""
        imp = make_importer('ICICICard')
        rows = prepare_rows(imp, [self._row('01-JUL-24', '5', 'BIG PURCHASE',
                                            '0', '0.00', '1,23,456.00', '1,23,456.00')])
        assert float(rows[0]['amount']) == pytest.approx(-123456.0)


class TestICICICardSkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('ICICICard').skip_transaction(skip_row(date='01-APR-24')) is False

    def test_none_date_skipped(self):
        assert make_importer('ICICICard').skip_transaction(skip_row(date=None)) is True


# ---------------------------------------------------------------------------
# SBI
# Headers: Txn Date,Value Date,Description,Ref No./Cheque No.,Branch Code,
#          Debit,Credit,Balance
#
# Real sample (SBIBankStatement.csv):
#   Account Name       :  ,Foo Bar OPC PVT LTD   <- header_identifier line
#   ...
#   Txn Date,Value Date,Description,...,Debit,Credit,Balance
#   5 Apr 2024,...,400.00, ,12,857.63             <- balance has Indian commas
#   22 Jul 2024,..., ,4,912.50,17,750.13          <- credit has Indian commas
#   13 Nov 2024,...,1,770.00, ,15,471.13          <- debit has Indian commas
#
# SBI exports unquoted comma-formatted amounts inside a comma-delimited CSV.
# This causes the CSV parser to split e.g. "1,770.00" into two fields.
# _merge_amount_fragments() re-joins them inside prepare_table().
# ---------------------------------------------------------------------------

class TestSBIParseAmount:
    """_parse_amount handles blank, None, plain and Indian comma-formatted values."""

    def test_blank_returns_zero(self):
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('') == 0.0

    def test_space_returns_zero(self):
        """SBI uses ' ' (single space) for an empty debit or credit cell."""
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount(' ') == 0.0

    def test_none_returns_zero(self):
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount(None) == 0.0

    def test_plain_amount(self):
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('400.00') == pytest.approx(400.0)

    def test_indian_lakh_debit(self):
        """Real sample: debit of 1,770.00"""
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('1,770.00') == pytest.approx(1770.0)

    def test_indian_lakh_credit(self):
        """Real sample: credit of 4,912.50"""
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('4,912.50') == pytest.approx(4912.5)

    def test_indian_lakh_balance(self):
        """Real sample: balance of 12,857.63"""
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('12,857.63') == pytest.approx(12857.63)

    def test_large_lakh_balance(self):
        """Real sample: balance of 17,750.13"""
        from dyu_accounting.gulp.SBI import Importer
        assert Importer._parse_amount('17,750.13') == pytest.approx(17750.13)


class TestSBIMergeAmountFragments:
    """
    _merge_amount_fragments re-joins CSV fragments caused by unquoted
    comma-formatted amounts.  Each case mirrors a real row from the sample.
    """

    def _merge(self, *fragments):
        from dyu_accounting.gulp.SBI import Importer
        return Importer._merge_amount_fragments(list(fragments))

    def test_plain_debit_no_commas(self):
        """400.00, ' ', 12,857.63 → ['400.00', ' ', '12,857.63']"""
        assert self._merge('400.00', ' ', '12', '857.63') == ['400.00', ' ', '12,857.63']

    def test_plain_credit_no_commas(self):
        """' ', 4,912.50, 17,750.13 → [' ', '4,912.50', '17,750.13']"""
        assert self._merge(' ', '4', '912.50', '17', '750.13') == [' ', '4,912.50', '17,750.13']

    def test_debit_with_comma(self):
        """1,770.00, ' ', 15,471.13 → ['1,770.00', ' ', '15,471.13']"""
        assert self._merge('1', '770.00', ' ', '15', '471.13') == ['1,770.00', ' ', '15,471.13']

    def test_no_commas_at_all(self):
        """No comma-formatted amounts; row passes through unchanged."""
        assert self._merge('20.00', ' ', '9500.00') == ['20.00', ' ', '9500.00']

    def test_both_debit_and_balance_have_commas(self):
        assert self._merge('1', '000.00', ' ', '99', '000.00') == ['1,000.00', ' ', '99,000.00']


class TestSBICleanTable:
    """_clean_table computes (credit - debit) and returns a string."""

    def _row(self, debit, credit):
        return SimpleNamespace(**{'Debit': debit, 'Credit': credit})

    def test_debit_only(self):
        """Real sample: debit 400.00, credit ' '"""
        assert make_importer('SBI')._clean_table(self._row('400.00', ' ')) == '-400.0'

    def test_credit_only(self):
        """Real sample: debit ' ', credit 4,912.50"""
        assert make_importer('SBI')._clean_table(self._row(' ', '4,912.50')) == '4912.5'

    def test_debit_with_indian_comma(self):
        """Real sample: debit 1,770.00 (already merged by prepare_table)"""
        assert make_importer('SBI')._clean_table(self._row('1,770.00', ' ')) == '-1770.0'

    def test_both_blank_returns_zero(self):
        assert make_importer('SBI')._clean_table(self._row(' ', ' ')) == '0.0'

    def test_returns_string(self):
        result = make_importer('SBI')._clean_table(self._row('100.00', ' '))
        assert isinstance(result, str)


class TestSBIPrepareTable:
    """
    End-to-end prepare_table tests using petl tables.
    Rows are constructed to mimic the post-CSV-parse state (i.e. with
    comma-formatted amounts already split into separate columns).
    """

    def _row(self, txn_date, debit, credit, balance, ref='REF', branch='99922'):
        return {
            'Txn Date': txn_date, 'Value Date': txn_date,
            'Description': 'TEST TXN', 'Ref No./Cheque No.': ref,
            'Branch Code': branch, 'Debit': debit, 'Credit': credit,
            'Balance': balance,
        }

    def test_simple_debit(self):
        """No comma in amounts → prepare_table passes through unchanged."""
        imp = make_importer('SBI')
        rows = prepare_rows(imp, [self._row('5 Apr 2024', '400.00', ' ', '12857.63')])
        assert rows[0]['amount'] == '-400.0'

    def test_simple_credit(self):
        imp = make_importer('SBI')
        rows = prepare_rows(imp, [self._row('22 Jul 2024', ' ', '4912.50', '17750.13')])
        assert rows[0]['amount'] == '4912.5'


class TestSBIMergeFragmentsViaPrepareTable:
    """
    Verify that prepare_table correctly re-merges rows where the CSV parser
    split comma-formatted amounts into extra columns.  These rows are built
    with the split columns exactly as the CSV parser would produce them.
    """

    HEADER = ['Txn Date', 'Value Date', 'Description', 'Ref No./Cheque No.',
              'Branch Code', 'Debit', 'Credit', 'Balance']

    def _split_row(self, *values):
        """Build a petl table from a raw tuple (may have more than 8 columns)."""
        return petl.wrap([self.HEADER, list(values)])

    def test_balance_split(self):
        """
        '12,857.63' in CSV → ['12', '857.63'] after parsing.
        Row: (5 Apr 2024, 5 Apr 2024, DESC, REF, 99922, 400.00, ' ', 12, 857.63)
        """
        imp = make_importer('SBI')
        tbl = self._split_row('5 Apr 2024', '5 Apr 2024', 'TO TRANSFER',
                               'REF001', '99922', '400.00', ' ', '12', '857.63')
        result = list(petl.dicts(imp.prepare_table(tbl)))
        assert result[0]['Debit'] == '400.00'
        assert result[0]['Credit'] == ' '
        assert result[0]['Balance'] == '12,857.63'
        assert result[0]['amount'] == '-400.0'

    def test_debit_and_balance_both_split(self):
        """
        '1,770.00' debit + '15,471.13' balance.
        Row: (..., 1, 770.00, ' ', 15, 471.13)
        """
        imp = make_importer('SBI')
        tbl = self._split_row('13 Nov 2024', '13 Nov 2024', 'TO TRANSFER',
                               'REF003', '99922', '1', '770.00', ' ', '15', '471.13')
        result = list(petl.dicts(imp.prepare_table(tbl)))
        assert result[0]['Debit'] == '1,770.00'
        assert result[0]['Balance'] == '15,471.13'
        assert result[0]['amount'] == '-1770.0'

    def test_credit_and_balance_both_split(self):
        """
        ' ' debit (empty) + '4,912.50' credit + '17,750.13' balance.
        Row: (..., ' ', 4, 912.50, 17, 750.13)
        """
        imp = make_importer('SBI')
        tbl = self._split_row('22 Jul 2024', '22 Jul 2024', 'BY TRANSFER',
                               'REF002', '99922', ' ', '4', '912.50', '17', '750.13')
        result = list(petl.dicts(imp.prepare_table(tbl)))
        assert result[0]['Debit'] == ' '
        assert result[0]['Credit'] == '4,912.50'
        assert result[0]['Balance'] == '17,750.13'
        assert result[0]['amount'] == '4912.5'


class TestSBISkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('SBI').skip_transaction(skip_row(date='5 Apr 2024')) is False

    def test_none_date_skipped(self):
        assert make_importer('SBI').skip_transaction(skip_row(date=None)) is True


# ---------------------------------------------------------------------------
# ICICIBank
# Headers: S No.,Value Date,Transaction Date,Cheque Number,Transaction Remarks,
#          Withdrawal Amount (INR ),Deposit Amount (INR ),Balance (INR )
# ---------------------------------------------------------------------------

class TestICICIBankPrepareTable:
    COL_WD = 'Withdrawal Amount (INR )'
    COL_DEP = 'Deposit Amount (INR )'

    def _row(self, wd, dep, balance=50000.0):
        return {
            'S No.': 1, 'Value Date': '01/01/2023', 'Transaction Date': '01/01/2023',
            'Cheque Number': '', 'Transaction Remarks': 'Test',
            self.COL_WD: wd, self.COL_DEP: dep, 'Balance (INR )': balance,
        }

    def test_withdrawal_becomes_negative(self):
        imp = make_importer('ICICIBank')
        rows = prepare_rows(imp, [self._row(wd=1000.0, dep=0)])
        assert rows[0]['amount'] == '-1000.0'

    def test_deposit_becomes_positive(self):
        imp = make_importer('ICICIBank')
        rows = prepare_rows(imp, [self._row(wd=0, dep=5000.0)])
        assert rows[0]['amount'] == '5000.0'

    def test_withdrawal_none_uses_deposit(self):
        imp = make_importer('ICICIBank')
        rows = prepare_rows(imp, [self._row(wd=None, dep=200.0)])
        assert rows[0]['amount'] == '200.0'

    def test_both_zero_returns_zero(self):
        imp = make_importer('ICICIBank')
        rows = prepare_rows(imp, [self._row(wd=0, dep=0)])
        assert rows[0]['amount'] == '0'

    def test_withdrawal_empty_string_uses_deposit(self):
        imp = make_importer('ICICIBank')
        rows = prepare_rows(imp, [self._row(wd='', dep=300.0)])
        assert rows[0]['amount'] == '300.0'


class TestICICIBankSkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('ICICIBank').skip_transaction(skip_row(date='01/01/2023')) is False

    def test_none_date_skipped(self):
        assert make_importer('ICICIBank').skip_transaction(skip_row(date=None)) is True


# ---------------------------------------------------------------------------
# IDFC
# Headers: Transaction Date,Value Date,Particulars,Cheque No.,Debit,Credit,Balance
# ---------------------------------------------------------------------------

class TestIDFCPrepareTable:
    def _row(self, debit, credit, balance=10000.0):
        return {
            'Transaction Date': '01-Jan-2023', 'Value Date': '01-Jan-2023',
            'Particulars': 'Test txn', 'Cheque No.': '',
            'Debit': debit, 'Credit': credit, 'Balance': balance,
        }

    def test_debit_becomes_negative(self):
        rows = prepare_rows(make_importer('IDFC'), [self._row(2000.0, None)])
        assert rows[0]['amount'] == '-2000.0'

    def test_credit_becomes_positive(self):
        rows = prepare_rows(make_importer('IDFC'), [self._row(None, 3000.0)])
        assert rows[0]['amount'] == '3000.0'

    def test_zero_debit_uses_credit(self):
        rows = prepare_rows(make_importer('IDFC'), [self._row(0, 1500.0)])
        assert rows[0]['amount'] == '1500.0'

    def test_both_absent_returns_zero(self):
        rows = prepare_rows(make_importer('IDFC'), [self._row(None, None)])
        assert rows[0]['amount'] == '0'


class TestIDFCSkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('IDFC').skip_transaction(skip_row(date='01-Jan-2023')) is False

    def test_none_date_skipped(self):
        assert make_importer('IDFC').skip_transaction(skip_row(date=None)) is True


# ---------------------------------------------------------------------------
# Upworks
# Headers: Date,Ref ID,Type,Description,Agency,Freelancer,Team,Account Name,
#          PO,Amount,ExchangeRate,Currency,Balance
# ---------------------------------------------------------------------------

class TestUpworksConfig:
    def test_header_identifier_not_empty(self):
        assert make_importer('Upworks').header_identifier != ''

    def test_header_identifier_matches_first_column(self):
        """header_identifier must match something in the CSV header row."""
        imp = make_importer('Upworks')
        first_col = imp.column_labels_line.split(',')[0]
        assert imp.header_identifier == first_col

    def test_currency_is_usd(self):
        assert make_importer('Upworks').currency == 'USD'


class TestUpworksPrepareTable:
    def _row(self, amount, balance='100.00'):
        return {
            'Date': 'Jan 01, 2023', 'Ref ID': 'REF001', 'Type': 'Credit',
            'Description': 'Payment received', 'Agency': '', 'Freelancer': 'Test User',
            'Team': '', 'Account Name': 'Freelancer', 'PO': '',
            'Amount': amount, 'ExchangeRate': '82.5',
            'Currency': 'USD', 'Balance': balance,
        }

    def test_positive_amount_passes_through(self):
        rows = prepare_rows(make_importer('Upworks'), [self._row('50.00')])
        assert rows[0]['Amount'] == '50.00'

    def test_negative_amount_passes_through(self):
        """Upworks already uses signed amounts; no negation applied."""
        rows = prepare_rows(make_importer('Upworks'), [self._row('-25.00')])
        assert rows[0]['Amount'] == '-25.00'


class TestUpworksSkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('Upworks').skip_transaction(skip_row(date='Jan 01, 2023')) is False

    def test_none_date_skipped(self):
        assert make_importer('Upworks').skip_transaction(skip_row(date=None)) is True
