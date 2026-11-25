"""
Unit tests for the bank statement ingesters in dyu_accounting/gulp/.

Test rows are built from the exact column headers and real-world sample
data from each bank's exported file format.
"""
import datetime
import importlib
import io
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

petl = pytest.importorskip('petl', reason='petl is required by beancount_reds_importers')
beancount_cache = pytest.importorskip('beancount.ingest.cache', reason='beancount is required')


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


def extract_real_file(module_name, config, filepath):
    """
    Run a real importer end-to-end against a real file on disk, the same way
    bean-extract itself does (identify() then extract()), rather than
    exercising prepare_table()/helper methods in isolation. Several real bugs
    in this package (a duplicate-field 'amount' crashing namedtuple()
    construction, an invalid-identifier column name, a bad date format
    silently producing None dates that then crashed extract()) only surface
    at this full-pipeline level, not in isolated prepare_table() calls.
    """
    mod = importlib.import_module(f'dyu_accounting.gulp.{module_name}')
    imp = mod.Importer(config)
    file = beancount_cache.get_file(str(filepath))
    assert imp.identify(file), f"{module_name} did not identify {filepath}"
    return imp.extract(file, [])


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


class TestICICICardEndToEnd:
    """
    Regression test: header_map previously renamed 'Amount(in Rs)' to
    'amount' while prepare_table() also added its own computed 'amount'
    field, producing two fields both named 'amount' - which doesn't fail in
    prepare_table() alone, only once get_transactions() tries to build a
    namedtuple from the full column set.
    """

    def test_real_fixture_extracts_without_crashing(self):
        fixture = Path(__file__).parent / "fixtures" / "icici_card" / "CreditCard_2026_01.csv"
        entries = extract_real_file(
            'ICICICard', {'main_account': 'Liabilities:INR:CreditCard'}, fixture
        )
        assert len(entries) == 3
        amounts = sorted(float(p.units.number) for e in entries for p in e.postings)
        assert amounts == sorted([-521.17, -1250.0, -5000.0])


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
# Real header: S No.,Value Date,Transaction Date,Cheque Number,Transaction
#          Remarks,Withdrawal Amount(INR),Deposit Amount(INR),Balance(INR)
#          (no spaces around '(INR)', unlike what was originally assumed)
# ---------------------------------------------------------------------------

class TestICICIBankPrepareTable:
    COL_WD = 'Withdrawal Amount(INR)'
    COL_DEP = 'Deposit Amount(INR)'

    def _row(self, wd, dep, balance=50000.0):
        return {
            'S No.': 1, 'Value Date': '01/01/2023', 'Transaction Date': '01/01/2023',
            'Cheque Number': '', 'Transaction Remarks': 'Test',
            self.COL_WD: wd, self.COL_DEP: dep, 'Balance(INR)': balance,
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
# Real header (Upwork's own 'transaction_report.csv' export): Date,Transaction ID,
#          Transaction type,Transaction summary,Transaction summary details,
#          Description 1,Description 2,Description 3,Agency team,Freelancer,
#          Client team,Account name,PO,Ref ID,Amount $,Amount in local currency,
#          Currency,Current balance $,Payment method
# prepare_table() also fetches a historical USD/INR rate per transaction date
# (via forex_python) and attaches it as foreign_amount/foreign_currency, which
# banking.Importer.extract() uses to record an '@ rate INR' price annotation.
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


class TestUpworksMergeGroup:
    """
    Upwork's export has multiple rows per real-world event sharing one
    'Transaction ID' (an earning plus its Service Fee/WHT rows, or a
    Withdrawal plus its Withdrawal Fee row) - _merge_group() combines them
    into the single dict prepare_table() turns into one beancount
    transaction. See the Importer class docstring for the full rationale.
    """

    NUAND_GROUP = [
        {'Date': 'Jul 25, 2025', 'Transaction type': 'Service Fee',
         'Description 1': 'Service fee', 'Account name': 'Dyumnin Technologies',
         'Amount $': '-12.00', 'Current balance $': '1020.36'},
        {'Date': 'Jul 25, 2025', 'Transaction type': 'WHT',
         'Description 1': 'Withholding tax', 'Account name': 'Dyumnin Technologies',
         'Amount $': '-0.12', 'Current balance $': '1032.36'},
        {'Date': 'Jul 25, 2025', 'Transaction type': 'Hourly',
         'Description 1': 'Earnings for Jul 14-Jul 20, 2025', 'Account name': 'Dyumnin Technologies',
         'Amount $': '120.00', 'Current balance $': '1032.48'},
    ]

    WITHDRAWAL_GROUP = [
        {'Date': 'Sep 29, 2025', 'Transaction type': 'Withdrawal Fee',
         'Description 1': 'Withdrawal fee', 'Account name': 'Dyumnin Technologies',
         'Amount $': '-50.00', 'Current balance $': '0.00'},
        {'Date': 'Sep 29, 2025', 'Transaction type': 'Withdrawal',
         'Description 1': 'Wire Transfer (USD) 9032', 'Account name': 'Dyumnin Technologies',
         'Amount $': '-970.36', 'Current balance $': '50.00'},
    ]

    def test_earning_group_nets_gross_minus_fees(self):
        """Real sample: 120 (Hourly) - 12.00 (Service Fee) - 0.12 (WHT) = 107.88."""
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.NUAND_GROUP)
        assert merged['Amount $'] == '107.88'
        assert merged['gross_amount'] == '120.00'
        assert merged['is_withdrawal'] is False

    def test_earning_group_fee_postings(self):
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.NUAND_GROUP)
        assert set(merged['extra_postings']) == {
            ('Expenses:USD:Upwork:ServiceFee', Decimal('12.00')),
            ('Expenses:USD:Upwork:WHT', Decimal('0.12')),
        }

    def test_earning_group_attaches_rate_for_earning_date(self):
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.NUAND_GROUP)
        assert merged['foreign_currency'] == 'INR'
        assert merged['foreign_amount'] > 0

    def test_earning_group_memo_comes_from_main_row(self):
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.NUAND_GROUP)
        assert merged['Description 1'] == 'Earnings for Jul 14-Jul 20, 2025'

    def test_withdrawal_group_main_amount_is_principal_only(self):
        """Real sample: -970.36 (Withdrawal), not merged with the -50.00 fee."""
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.WITHDRAWAL_GROUP)
        assert merged['Amount $'] == '-970.36'
        assert merged['is_withdrawal'] is True

    def test_withdrawal_group_fee_is_separate_posting(self):
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.WITHDRAWAL_GROUP)
        assert merged['extra_postings'] == [('Expenses:USD:Upwork:WithdrawalFee', Decimal('50.00'))]

    def test_withdrawal_group_has_no_rate(self):
        """
        Withdrawal rows get no auto-fetched rate - the real USD/INR rate
        isn't known until the IDFC bank statement is matched, which is
        reconcile_upwork.py's job, not this importer's.
        """
        imp = make_importer('Upworks')
        merged = imp._merge_group(self.WITHDRAWAL_GROUP)
        assert merged['foreign_amount'] is None
        assert merged['foreign_currency'] is None


class TestUpworksSkipTransaction:
    def test_valid_date_not_skipped(self):
        assert make_importer('Upworks').skip_transaction(skip_row(date='Jan 01, 2023')) is False

    def test_none_date_skipped(self):
        assert make_importer('Upworks').skip_transaction(skip_row(date=None)) is True


class TestUpworksGetTargetAccount:
    def test_withdrawal_gets_no_target(self):
        """
        Left single-leg (principal + its own fee posting) for
        reconcile_upwork.py to complete once the real bank-side amount is
        known.
        """
        imp = make_importer('Upworks')
        assert imp.get_target_account(skip_row(is_withdrawal=True)) is None

    def test_earning_targets_income_account(self):
        imp = make_importer('Upworks')
        assert imp.get_target_account(skip_row(is_withdrawal=False)) == 'Income:USD:UPWORKS:Client'


class TestUpworksEndToEnd:
    """
    Regression test: runs the real importer end-to-end (identify() +
    extract()) against a real fixture file, the same way bean-extract
    itself does, to catch issues that only surface in the full pipeline
    (e.g. a posting ending up in the wrong currency, which only bean-extract
    in isolation wouldn't catch without real `open` directives loaded).
    """

    def test_real_fixture_produces_balanced_merged_transactions(self):
        fixture = Path(__file__).parent / "fixtures" / "upworks" / "Upworks_2026_01.csv"
        entries = extract_real_file(
            'Upworks', {'main_account': 'Assets:USD:Upwork'}, fixture
        )
        assert len(entries) == 2  # one merged entry per Transaction ID

        earning = next(e for e in entries if e.date == datetime.date(2025, 7, 25))
        accounts = {p.account: p for p in earning.postings}
        assert float(accounts['Assets:USD:Upwork'].units.number) == pytest.approx(107.88)
        assert float(accounts['Income:USD:UPWORKS:Client'].units.number) == pytest.approx(-120.0)
        assert float(accounts['Expenses:USD:Upwork:ServiceFee'].units.number) == pytest.approx(12.0)
        assert float(accounts['Expenses:USD:Upwork:WHT'].units.number) == pytest.approx(0.12)
        # All four legs share the same price (same earning-date rate).
        prices = {p.price.number for p in earning.postings}
        assert len(prices) == 1

        withdrawal = next(e for e in entries if e.date == datetime.date(2025, 9, 29))
        accounts = {p.account: p for p in withdrawal.postings}
        assert float(accounts['Assets:USD:Upwork'].units.number) == pytest.approx(-970.36)
        assert float(accounts['Expenses:USD:Upwork:WithdrawalFee'].units.number) == pytest.approx(50.0)
        assert all(p.price is None for p in withdrawal.postings)


# ---------------------------------------------------------------------------
# Account (Google Forms)
# Headers: Timestamp,Date,Amount,Purpose,Payment,Receipt
#
# Payment -> source/credit account (get_main_account), Purpose -> expense/
# debit account (get_target_account). See TICKET-009 for the locked design.
# ---------------------------------------------------------------------------

class TestAccountConfig:
    def test_header_identifier_is_six_column_format(self):
        imp = make_importer('Account')
        assert imp.header_identifier == 'Timestamp,Date,Amount,Purpose,Payment,Receipt'

    def test_column_labels_line_is_six_column_format(self):
        imp = make_importer('Account')
        assert imp.column_labels_line == 'Timestamp,Date,Amount,Purpose,Payment,Receipt'

    def test_old_seven_column_header_no_longer_recognized(self):
        """Clean cutover: the old header string must not match the new one."""
        imp = make_importer('Account')
        old_header = ('Timestamp,Date,Transaction Title,Amount,'
                       'Paid from Account,Credit to Account,Receipt')
        assert imp.header_identifier != old_header


class TestAccountGetMainAccount:
    """Payment column -> source/credit account, case-insensitively."""

    def test_company_card(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='Company Card')) == 'Assets:INR:Cash:IDFC:Current'

    def test_personal_card(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='Personal Card')) == 'Liabilities:INR:CEOBank'

    def test_credit_card(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='Credit Card')) == 'Liabilities:INR:CreditCard'

    def test_cash(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='Cash')) == 'Assets:INR:Cash:CashInHand'

    def test_case_insensitive_upper(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='CASH')) == 'Assets:INR:Cash:CashInHand'

    def test_case_insensitive_with_padding(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment=' cash ')) == 'Assets:INR:Cash:CashInHand'

    def test_unmapped_value_falls_back(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='Bag')) == 'Assets:INR:Uncategorized'

    def test_blank_falls_back(self):
        imp = make_importer('Account')
        assert imp.get_main_account(skip_row(Payment='')) == 'Assets:INR:Uncategorized'


class TestAccountGetTargetAccount:
    """
    Purpose column (ot.memo) -> expense/debit account, case-insensitively.

    Values must follow this project's real chart-of-accounts convention
    (Expenses:INR:<Category>, no spaces - see example/accounts.beancount);
    the originally-locked TICKET-009 spec values ('Expenses:Food', and
    'Expenses:Office Supplies'/'Expenses:Vehicle Maintenance' with spaces)
    didn't match it, and the latter two aren't even valid beancount account
    names (account name components can't contain spaces).
    """

    def test_food(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='Food')) == 'Expenses:INR:Food'

    def test_fuel(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='Fuel')) == 'Expenses:INR:Fuel'

    def test_office_supplies(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='Office Supplies')) == 'Expenses:INR:OfficeSupplies'

    def test_vehicle_maintenance_whitespace_quirk(self):
        """Real data: 'Vehicle  maintenance ' (double internal space, trailing space)."""
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='Vehicle  maintenance ')) == 'Expenses:INR:VehicleMaintenance'

    def test_travel(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='Travel')) == 'Expenses:INR:Travel'

    def test_case_insensitive_upper(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='FOOD')) == 'Expenses:INR:Food'

    def test_unmapped_purpose_falls_back(self):
        """Real sample value from researcher's findings."""
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='1947 food')) == 'Expenses:INR:Uncategorized'

    def test_unmapped_purpose_with_special_characters_falls_back(self):
        imp = make_importer('Account')
        assert imp.get_target_account(skip_row(memo='USB cables, boxes, snacks')) == 'Expenses:INR:Uncategorized'

    def test_account_names_are_valid_beancount_identifiers(self):
        """
        Regression test: account name components can't contain spaces (or
        any character outside [A-Za-z0-9\\-]); 'Expenses:Office Supplies'
        and 'Expenses:Vehicle Maintenance' (the original TICKET-009 spec
        values) would fail to parse the first time a real row hit them.
        """
        import re
        imp = make_importer('Account')
        valid_component = re.compile(r'^[A-Z][A-Za-z0-9\-]*$')
        for account in list(imp.PURPOSE_ACCOUNT_MAP.values()) + [imp.PURPOSE_FALLBACK_ACCOUNT]:
            for component in account.split(':'):
                assert valid_component.match(component), (
                    f"{component!r} in {account!r} is not a valid beancount "
                    "account name component"
                )


class TestAccountBuildMetadata:
    def _imp(self):
        imp = make_importer('Account')
        imp.config = {}  # build_metadata's base class reads self.config
        return imp

    def test_receipt_included_when_present(self):
        imp = self._imp()
        ot = skip_row(Receipt='https://drive.google.com/open?id=abc')
        meta = imp.build_metadata(None, metatype='transaction', data={'transaction': ot})
        assert meta['receipt'] == 'https://drive.google.com/open?id=abc'

    def test_receipt_omitted_when_blank(self):
        imp = self._imp()
        ot = skip_row(Receipt='')
        meta = imp.build_metadata(None, metatype='transaction', data={'transaction': ot})
        assert 'receipt' not in meta

    def test_receipt_omitted_when_missing(self):
        imp = self._imp()
        ot = skip_row()
        meta = imp.build_metadata(None, metatype='transaction', data={'transaction': ot})
        assert 'receipt' not in meta


class TestAccountDateFormat:
    """
    Real sample: the Google Form export's 'Date' column uses US-style
    M/D/YYYY (e.g. '5/25/2024' for May 25), not D/M/YYYY. The old D/M/YYYY
    assumption made datetime.strptime raise for any day > 12 (the day value
    landing in the month position is invalid); petl.convert() silently
    swallows that into date=None, which then crashed extract() downstream
    with AttributeError on ot.date.date() - a crash only visible when running
    the full pipeline, not from isolated date-format assertions.
    """

    def test_date_format_is_month_day_year(self):
        imp = make_importer('Account')
        assert imp.date_format == '%m/%d/%Y'
        parsed = datetime.datetime.strptime('5/25/2024', imp.date_format)
        assert parsed == datetime.datetime(2024, 5, 25)

    def test_old_day_month_format_would_have_failed(self):
        """Documents why the old '%d/%m/%Y' assumption was wrong."""
        with pytest.raises(ValueError):
            datetime.datetime.strptime('5/25/2024', '%d/%m/%Y')


class TestAccountSkipTransaction:
    """Account.py was missing this guard entirely (every other importer in
    this package has it), which is why a bad date crashed extract() instead
    of being skipped."""

    def test_valid_date_not_skipped(self):
        assert make_importer('Account').skip_transaction(skip_row(date='01/01/2026')) is False

    def test_none_date_skipped(self):
        assert make_importer('Account').skip_transaction(skip_row(date=None)) is True


class TestAccountEndToEnd:
    def test_real_world_date_with_day_over_12_extracts_without_crashing(self, tmp_path):
        """
        Regression test built from a real Google Form export row
        ('5/25/2024 23:33:30,5/25/2024,6743,Food,Company Card,<url>,') that
        previously produced date=None and crashed extraction with
        AttributeError: 'NoneType' object has no attribute 'date'.
        """
        csv_content = (
            "Timestamp,Date,Amount,Purpose,Payment,Receipt,Column 7\n"
            "5/25/2024 23:33:30,5/25/2024,6743,Food,Company Card,"
            "https://example.com/r,\n"
        )
        fixture = tmp_path / "Accounts_test.csv"
        fixture.write_text(csv_content)

        entries = extract_real_file(
            'Account', {'main_account': 'Liabilities:INR:Misc'}, fixture
        )
        assert len(entries) == 1
        assert entries[0].date == datetime.date(2024, 5, 25)
