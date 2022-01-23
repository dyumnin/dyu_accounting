import jinja2
import datetime
from decimal import Decimal
import re
import os
from beancount.core import data


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
                    print(entry.date)
                    for posting in entry.postings:
                        if income_re.match(posting.account):
                            self._add('revenue', posting)
                        if salary_re.match(posting.account):
                            print(f"salary={posting}")
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
        print(f"adding {sum} to {key} result{self.pnl_data[key]}")

    def report_pnl(self, outdir):
        self.pnl_data['expenses_total'] = self.pnl_data['depreciation'] + \
            self.pnl_data['misc_expenses'] + self.pnl_data['salary']
        self.pnl_data['profit'] = self.pnl_data['expenses_total'] + \
            self.pnl_data['revenue']
        # print(self.pnl_data)
        templateEnv = jinja2.Environment(
            loader=jinja2.PackageLoader('dyu_accounting', 'templates'),
            trim_blocks=True,
            lstrip_blocks=True)
        fname = "PnL.tpl"
        # # print(fname)
        template = templateEnv.get_template(fname)
        # os.makedirs(outdir, exist_ok=True)
        outputText = template.render(company=self.company,
                                     data=self.pnl_data,
                                     ay=self.fy+1)
        with open(
                os.path.join(outdir, "PnL.html"),
                "w"
        ) as fy_file:
            fy_file.write(outputText)
        return ["PnL.html"]
