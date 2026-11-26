import jinja2
import datetime
from decimal import Decimal
import re
import os
import sys
from beancount.core import data
from dyu_accounting.Utilities import render_template


class PnL:
    def __init__(self, entries, options, cfg):
        self.cfg = cfg
        self.entries = entries
        self.cfg = cfg
        self.fy = cfg['fy']
        self.company = cfg['company']
        self.open_date = datetime.date(self.fy, 4, 1)
        self.close_date = datetime.date(self.fy + 1, 3, 31)
        self.pnl_data = {
            'revenue': Decimal(),
            'salary': Decimal(),
            'depreciation': Decimal(),
            'misc_expenses': Decimal(),
            'expenses_total': Decimal(),
            'profit': Decimal()}
        self.calc_pnl()

    def calc_pnl(self):
        income_re = re.compile(r'Income:')
        expense_re = re.compile(r'Expenses:INR')
        salary_re = re.compile(r'Expenses:INR:Salary')
        for entry in self.entries:
            if isinstance(entry, data.Transaction):
                if (
                        entry.date >= self.open_date
                        and entry.date <= self.close_date
                ):
                    for posting in entry.postings:
                        if income_re.match(posting.account):
                            # Income accounts are credit-normal: a revenue
                            # posting should be negative. A positive one
                            # (e.g. from a hand-added leg) doesn't just
                            # look odd - it actively cancels out correctly
                            # signed revenue in the same running total
                            # instead of adding to it, silently understating
                            # revenue. Flag it rather than fail quietly.
                            if posting.units.number > 0:
                                print(
                                    f"WARNING: positive amount on income "
                                    f"account {posting.account} in "
                                    f"{entry.date} \"{entry.narration}\" "
                                    f"({posting.units}) - revenue accounts "
                                    f"are normally credited (negative); "
                                    f"this will understate reported revenue "
                                    f"unless it is a deliberate refund/"
                                    f"contra entry.",
                                    file=sys.stderr)
                            self._add('revenue', posting)
                        if salary_re.match(posting.account):
                            self._add('salary', posting)
                        elif expense_re.match(posting.account):
                            self._add('misc_expenses', posting)

    def set_depreciation(self, amount):
        self.pnl_data['depreciation'] = amount

    def _add(self, key, posting):
        if posting.units.currency == "INR":
            sum = posting.units.number
        else:
            sum = posting.units.number * \
                posting.price.number
        self.pnl_data[key] += sum

    def report_pnl(self, outdir):
        self.pnl_data['expenses_total'] = self.pnl_data['depreciation'] + \
            self.pnl_data['misc_expenses'] + self.pnl_data['salary']
        # Income is credit-normal, so pnl_data['revenue'] has been
        # accumulating as a negative raw ledger balance (see calc_pnl/_add)
        # - that's exactly what the positive-posting warning above needs,
        # so it's kept raw until here. Flip it to the conventional positive
        # revenue figure for display and compute profit the normal way
        # (revenue - expenses) now that both sides are display-signed,
        # rather than just summing the raw-signed postings, which silently
        # inverted a real profit into what looked like a loss of the same
        # size.
        self.pnl_data['revenue'] = -self.pnl_data['revenue']
        self.pnl_data['profit'] = self.pnl_data['revenue'] - \
            self.pnl_data['expenses_total']
        fname="PnL.html"
        written = render_template(data={
            'template_name': 'PnL.tpl',
            'cfg': self.cfg,
            'pnl': self.pnl_data,
            'outfile': fname
        })
        return [written]
