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
                if(entry.meta.get('balance_sheet')):
                    self.category[entry.account] = entry.meta.get(
                        'balance_sheet')

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

    def report_balance_sheet(self):
        fname = f"balance_sheet_FY_{self.cfg['fy']}_{self.cfg['fy']+1}.html"
        render_template(data={
            'template_name': 'balancesheet.tpl',
            'cfg': self.cfg,
            'account': self.balancesheet[self.cfg['fy']].account,
            'prev_account': self.balancesheet[self.cfg['fy']-1].account,
            'outfile': fname
        })
        return [fname]

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
