import jinja2
import datetime
from decimal import Decimal
import re
import os
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
        self.pnl_data['profit'] = self.pnl_data['expenses_total'] + \
            self.pnl_data['revenue']
        fname="PnL.html"
        render_template(data={
            'template_name': 'PnL.tpl',
            'cfg': self.cfg,
            'pnl': self.pnl_data,
            'outfile': fname
        })
        return [fname]
