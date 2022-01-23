import jinja2
import datetime
from decimal import Decimal
import re
import os
from beancount.core import data, amount

zero_inr = amount.Amount(Decimal(0), 'INR')


class GST:
    def __init__(self, entries, options, cfg):
        self.cfg = cfg
        self.entries = entries
        self.fy = cfg['fy']
        self.company = cfg['company']
        self.open_date = datetime.date(self.fy, 4, 1)
        self.close_date = datetime.date(self.fy + 1, 3, 31)
        self.calc_gst()

    def calc_gst(self, scheme="quarterly"):
        self.gst = []
        if scheme == "quarterly":
            for i in range(4):
                self.gst.append({})
        else:
            for i in range(12):
                self.gst.append({})

        for entry in self.entries:
            if isinstance(entry, data.Transaction):
                if entry.date < self.open_date or entry.date > self.close_date:
                    continue
                if scheme == 'quarterly':
                    entry_idx = (entry.date.month-1)//3
                else:
                    entry_idx = (entry.date.month-1)
                if entry.postings:
                    for posting in entry.postings:
                        # print(f" {entry_year} {entry_quarter} posting account = {repr(posting.account)}")
                        if re.search("Assets.*GST", posting.account):
                            self.gst[
                                    entry_idx][posting.account] =\
                                amount.add(
                                self.gst[entry_idx].get(
                                    posting.account, zero_inr),
                                posting.units)
                        if re.search("Liabilities.*GST", posting.account):
                            self.gst[
                                    entry_idx][posting.account] = \
                                amount.add(
                                self.gst[entry_idx].get(
                                    posting.account, zero_inr),
                                posting.units)

    def report_gst(self):
        templateEnv = jinja2.Environment(
            loader=jinja2.PackageLoader('dyu_accounting', 'templates'),
            trim_blocks=True,
            lstrip_blocks=True)
        fname = "GST.tpl"
        template = templateEnv.get_template(fname)
        outputText = template.render(company=self.company,
                                     data=self.gst,
                                     fy=self.fy)
        with open(
                os.path.join(self.cfg['outdir'], "GST.html"),
                "w"
        ) as fy_file:
            fy_file.write(outputText)
        return ["GST.html"]
