from beancount.loader import load_string
from beancount.core import amount
from beancount.core.position import Position
from beancount.core.amount import Amount
from decimal import Decimal
import dyu_accounting.balance_sheet as bsheet
import dyu_accounting.depreciation as depr
from beancount.ops.summarize import balance_by_account
import datetime


def calc_bs(entries, opt):
    depr.Depreciation(entries, opt)
    bs = bsheet.BalanceSheet(entries, opt, company={
        'name': 'Company Name', 'address': 'Company Address'}, fy=2019)
    return bs


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
entities, error, opts = load_string(account)
print(error)
max_fy = 2019
prev_year = balance_by_account(
    entities, date=datetime.date(max_fy, 4, 1))[0]
cur_year = balance_by_account(
    entities, date=datetime.date(max_fy+1, 4, 1))[0]


def aadd(self, amountx):
    '''
    Overload add function to Amount Type.
    '''
    if amountx.currency != self.currency:
        raise ValueError(
            "Unmatching currencies for operation on {} and {}".format(
                self, amountx))
    self.number += amountx.number


setattr(Amount, 'addx', aadd)
