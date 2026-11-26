import pytest
from beancount.loader import load_string
from beancount.core import amount
from beancount.core.position import Position
from decimal import Decimal
import dyu_accounting.balance_sheet as bsheet
import dyu_accounting.depreciation as depr


def test_shareCapital():
    account = '''
2018-07-01 open Equity:INR:ShareCapital              INR
    balance_sheet: "liabilities.share_capital"
2018-07-01 open Liabilities:INR:Surplus              INR
    balance_sheet: "liabilities.surplus"
2018-07-01 open Assets:INR:Bank:Current              INR
    balance_sheet: "assets.cash"
2018-07-01 open Equity:Opening-Balances INR
    balance_sheet: "assets.cash"
2018-07-02 * "Share Transfer" "Opening Company"
    Assets:INR:Bank:Current 100000 INR
    Equity:INR:ShareCapital
;2018-07-02 balance Equity:INR:ShareCapital -100000 INR
    '''
    entries, error, opts = load_string(account)
    print(error)
    depr.Depreciation(entries, opts, cfg={'fy': 2018})
    cfg = {
        'fy': 2019,
        'company': {'name': 'Company Name', 'address': 'Company Address'},
    }
    bals = bsheet.BalanceSheet(entries, opts, cfg)
    bals.mkBalanceSheet(2019)
    # Compare the display-signed totals (liabilities/equity flipped
    # positive, matching how the report itself presents them - see
    # BalanceSheet._display_account), since that's the actual "does the
    # balance sheet balance" invariant; the raw BSTable has liabilities
    # as a negative (credit-normal) figure and assets positive
    # (debit-normal), so they're never literally equal to each other.
    bs = bsheet.BalanceSheet._display_account(bals.balancesheet[2019])
    assert bs['liabilities']['total'] == bs['assets']['total']
