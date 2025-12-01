from beancount.loader import load_string
from beancount.core import amount, convert
from beancount.core.position import Position
from beancount.core.amount import Amount
from decimal import Decimal
import dyu_accounting.balance_sheet as bsheet
import dyu_accounting.depreciation as depr
from beancount.ops.summarize import balance_by_account
import datetime
from beancount import loader
import sys

entries, errors, options = loader.load_file(
    'ledger.beancount', log_errors=sys.stderr)
bba = balance_by_account(entries)[0]
nuts = bba['Assets:NUTS:Equipment:Consumable']
bolts = bba['Assets:BOLTS:Equipment:Consumable']
nb = bba['Assets:NUTBOLT:Equipment:Consumable']
