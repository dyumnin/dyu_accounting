#! env python3
import os
from decimal import Decimal
import logging
import sys
import datetime
import re
from beancount import loader
from beancount.core import amount, convert
from beancount.core.amount import Amount
from beancount.core.position import Position
from beancount.core.inventory import Inventory
from beancount.core.number import D
from beancount.core import flags
from beancount.core import data
from beancount.ops.summarize import balance_by_account, create_entries_from_balances
from dyu_accounting.Utilities import get_fy, get_quarter, get_year_end
from dyu_accounting.Utilities import render_template
#from dyu_accounting import templates
import jinja2
import copy
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources
# __plugins__ = ['report_gst']
# Python Script for GST Reporting. Reports data for GSTR 1 and GSTR 3
# Input GST(GST Paid during a purchase.) is an Asset
# Output GST(GST Collected during a Sale) is an Liability.
# For GST1 Report all GST collected during Sales.
# For GSR3 Report all GST paid during Purchase.

COMPANY_NAME = "Dyumnin Semiconductors OPC Private LTD"
COMPANY_ADDRESS = "#1 Bharathi Ramana, Vidhyaranyapura, 1st Block, Nanjappa Layout, Bangalore 13"
SHARE_CAPITAL = ['Equity:INR:ShareCapital']

# Same account patterns PnL uses to compute a single FY's profit - reused
# here, over all history up to a snapshot date, to derive retained
# earnings (see BalanceSheet._cumulative_profit).
_INCOME_RE = re.compile(r'Income:')
_EXPENSE_RE = re.compile(r'Expenses:INR')

# Newer charts of accounts tag each `open` directive with a Schedule III
# key (e.g. `schedule3: "bs.cash"`) instead of the legacy `balance_sheet:
# "assets.cash"` key this module originally read. Translate the ones that
# belong on the balance sheet (bs.*) into the (head, subkey) pairs BSTable
# already uses; schedule3 values outside this table (e.g. pnl.* ones, used
# to route accounts like Assets:INR:ExchangeGain to the P&L instead) are
# intentionally left out of the balance sheet.
SCHEDULE3_TO_BS = {
    'bs.fixed_assets': ('assets', 'tangible'),
    'bs.investments_nc': ('assets', 'investments_non_current'),
    'bs.gst_itc': ('assets', 'misc_current'),
    'bs.cash': ('assets', 'cash'),
    'bs.trade_receivables': ('assets', 'trade_receivables'),
    'bs.shortterm_loans': ('assets', 'shortterm_loans'),
    'bs.wip_capital': ('assets', 'wip_capital'),
    'bs.provisions': ('liabilities', 'shortterm_provisions'),
    'bs.equity_share_capital': ('liabilities', 'share_capital'),
    'bs.equity_surplus': ('liabilities', 'surplus'),
    'bs.borrowings': ('liabilities', 'shortterm_borrowing'),
    'bs.trade_payables': ('liabilities', 'trade_payable'),
    'bs.gst_payable': ('liabilities', 'other_current_liabilities'),
    'bs.other_current_liabilities': ('liabilities', 'other_current_liabilities'),
    'bs.accrued_liabilities': ('liabilities', 'shortterm_provisions'),
}


class BSTable:

    def __init__(self):
        zero_inr = Amount(Decimal(), 'INR')
        self.zero_inr = zero_inr
        self.account = {
            'liabilities': {
                'share_capital': zero_inr,
                'surplus': zero_inr,
                'longterm_borrowing': zero_inr,
                'deferred_tax': zero_inr,
                'longterm_liability': zero_inr,
                'longterm_provisions': zero_inr,
                'shortterm_borrowing': zero_inr,
                'trade_payable': zero_inr,
                'other_current_liabilities': zero_inr,
                'shortterm_provisions': zero_inr,
                'total': zero_inr,
            },
            'assets': {
                'non_current': zero_inr,
                'fixed': zero_inr,
                'tangible': zero_inr,
                'intangible': zero_inr,
                'wip_capital': zero_inr,
                'intangile_wip': zero_inr,
                'investments_non_current': zero_inr,
                'deferred_tax': zero_inr,
                'longterm_loan': zero_inr,
                'other_non_current': zero_inr,
                'investments': zero_inr,
                'inventory': zero_inr,
                'trade_receivables': zero_inr,
                'cash': zero_inr,
                'shortterm_loans': zero_inr,
                'misc_current': zero_inr,
                'total': zero_inr,
            }
        }

    def __repr__(self):
        return f'{self.account}'

    def update_total(self):
        for head in ['liabilities', 'assets']:

            self.account[head]['total'] = self.zero_inr
            for k in self.account[head]:
                if k != 'total':
                    self.add(
                        head, 'total',
                        self.account[head][k]
                    )

    def add(self, head, result_account, v):
        self.account[head][result_account] = amount.add(
            self.account[head][result_account], v)


class BalanceSheet:
    def __init__(self, entries, options_map, cfg):
        self.entries = entries
        self.cfg = cfg
        self.company = cfg['company']
        self.fy = cfg['fy']
        self.open_date = datetime.date(self.fy, 4, 1)
        self.prev_open_date = datetime.date(self.fy - 1, 4, 1)
        self.options_map = options_map
        self.map_accounts_to_categories()
        self.balancesheet = {}

    def map_accounts_to_categories(self):
        self.category = {}
        for entry in self.entries:
            if isinstance(entry, data.Open):
                legacy = entry.meta.get('balance_sheet')
                if legacy:
                    self.category[entry.account] = legacy
                    continue
                schedule3 = entry.meta.get('schedule3')
                if schedule3 in SCHEDULE3_TO_BS:
                    head, subkey = SCHEDULE3_TO_BS[schedule3]
                    self.category[entry.account] = f'{head}.{subkey}'

    def mkBalanceSheet(self, year):
        '''
        Read depreciation rate from file.
        create a table as follows
        tbl1[account]=category
        tbl2[category]={life:xx, mca_wdv_rate, it_rate}
        for each posting:
           does the account match Equipment?
           Does it have a category?
           Calculate depreciation for life of asset.
           Write depreciation to depreciation.beancount
           write depreciation report to file
        '''
        # Move all asset cash on open date to Surplus.
        logger = logging.getLogger("BalanceSheet")
        logger.info("Hello")
        # self.transfer_opening_balance(year)
        self._calc_balancesheet(year)

    def _cumulative_profit(self, cutoff_date):
        """Net profit (revenue - expenses), display-signed, from inception
        through (not including) cutoff_date - the same calculation PnL
        does for one FY's window, but over all history.

        This system never posts a period-end closing entry zeroing
        Income/Expense into equity each year, so without this, retained
        profit shows up in Assets (via the cash it generated) but never
        on the liabilities/equity side, and the balance sheet can't
        balance. Injecting it here as a derived Equity:Surplus figure -
        purely for this report - doesn't touch self.entries or any
        ledger file, so it can't affect anything else that reads them
        (journal, GST, bank reconciliation, ...).
        """
        revenue = Decimal()
        expenses = Decimal()
        for entry in self.entries:
            if not isinstance(entry, data.Transaction) or entry.date >= cutoff_date:
                continue
            for posting in entry.postings:
                if posting.units is None:
                    continue
                value = (posting.units.number if posting.units.currency == 'INR'
                          else posting.units.number * posting.price.number)
                if _INCOME_RE.match(posting.account):
                    revenue -= value
                elif _EXPENSE_RE.match(posting.account):
                    expenses += value
        return revenue - expenses

    def _calc_balancesheet(self, yrs):
        logger = logging.getLogger("BalanceSheet:calc_bs")
        logger.info("Calculating Balance Sheet")
        date = datetime.date(yrs+1, 4, 1)
        logger.debug(f'on {date} : entries pre bba={self.entries}')
        bba = balance_by_account(
            self.entries, date=date)[0]
        logger.debug(f'on {date} bba={bba}')
        self.balancesheet[yrs] = BSTable()
        logger.debug(
            f'blank balancesheet on {date} BSTable={self.balancesheet}')
        for e in self.category:
            # self.category[e] {self.category[e]}')
            logging.debug(f'account_name {e},')
            k1, k2 = self.category[e].split('.')
            logging.debug(
                f'e {e} only {bba[e].reduce(convert.get_cost)} bba_e {bba[e]}')
            self.balancesheet[yrs].add(
                k1, k2, bba[e].reduce(convert.get_cost).get_currency_units('INR'))
        # Retained earnings plug - see _cumulative_profit. Raw-signed
        # (negative = a credit, since Equity is credit-normal) so it comes
        # out positive through _display_account()'s flip like every other
        # liabilities/equity line, on top of whatever (normally zero) raw
        # balance the chart's own Equity:Surplus account already has.
        self.balancesheet[yrs].add(
            'liabilities', 'surplus',
            Amount(-self._cumulative_profit(date), 'INR'))
        self.balancesheet[yrs].update_total()
        logger.debug(
            f'balancesheet {date} after update total BSTable={self.balancesheet}')

    def transfer_opening_balance(self, fy):
        logger = logging.getLogger("BalanceSheet:Transfer Opening Balance:")
        open_date = datetime.date(fy, 4, 1)
        open_bba = balance_by_account(
            self.entries, date=open_date)[0]
        logger.debug(f'on {open_date} open_bba={open_bba}')
        balances = {}
        for e in self.category:
            if self.category[e] == 'liabilities.surplus':
                surplus = e
            if self.category[e] == 'assets.cash':
                balances[e] = open_bba[e]
        transfer_entries = create_entries_from_balances(
            balances, open_date,
            surplus, False,
            data.new_metadata(
                '<transfer_balances>', 0),
            flags.FLAG_TRANSFER,
            "Transfer balance for '{account}' (Transfer balance)"
        )
        self.entries.extend(transfer_entries)
        logger.debug(f'transfer Entries {transfer_entries}')
        logger.debug(f'Entries after transfer {self.entries}')

    @staticmethod
    def _display_account(bs_table):
        """BSTable.account, with the 'liabilities' head (which also holds
        the equity lines - share_capital, surplus - per this chart's own
        balance_sheet/schedule3 convention) sign-flipped for display.

        Liabilities and equity are credit-normal, so their raw ledger
        balance is negative (e.g. Share Capital sits at -100000 for a
        credited 100000); Assets are debit-normal, so its raw balance
        already matches the positive figure a balance sheet conventionally
        shows. Flipping only 'liabilities' here, at render time, keeps the
        raw signed values available to anything else (e.g. update_total())
        that works directly with BSTable.
        """
        return {
            'liabilities': {
                k: Amount(-v.number, v.currency)
                for k, v in bs_table.account['liabilities'].items()},
            'assets': bs_table.account['assets'],
        }

    def report_balance_sheet(self):
        fname = f"balance_sheet_FY_{self.cfg['fy']}_{self.cfg['fy']+1}.html"
        written = render_template(data={
            'template_name': 'balancesheet.tpl',
            'cfg': self.cfg,
            'account': self._display_account(self.balancesheet[self.cfg['fy']]),
            'prev_account': self._display_account(self.balancesheet[self.cfg['fy']-1]),
            'outfile': fname
        })
        return [written]

    '''
    Steps
        - Find asset block.
        - assign to half or full year.
        - on  31st compute WDV and depreciation on half and full for each asset block.
        - Transfer half to full for next year.
    '''


if __name__ == "__main__":

    import csv
    entries, errors, options = loader.load_file(
        sys.argv[1], log_errors=sys.stderr)
    bs = BalanceSheet(entries, options, {
        'name': COMPANY_NAME,
        'address': COMPANY_ADDRESS}
    )
    bs.report_balance_sheet()
