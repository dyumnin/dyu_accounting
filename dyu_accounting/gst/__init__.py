import jinja2
import datetime
from decimal import Decimal
import re
import os
from beancount.core import data, amount
from dyu_accounting.Utilities import render_template
zero_inr = amount.Amount(Decimal(0), 'INR')


class GST:
    def __init__(self, entries, options, cfg):
        self.cfg = cfg
        self.entries = entries
        self.fy = cfg['fy']
        self.company = cfg['company']
        self.open_date = datetime.date(self.fy, 4, 1)
        self.close_date = datetime.date(self.fy + 1, 3, 31)
        self.calc_gst(cfg['gst']['qrmp'])

    def calc_gst(self, qrmp=True):
        self.gst = []
        if qrmp:
            for i in range(4):
                self.gst.append({})
        else:
            for i in range(12):
                self.gst.append({})

        for entry in self.entries:
            if isinstance(entry, data.Transaction):
                if entry.date < self.open_date or entry.date > self.close_date:
                    continue
                if qrmp:
                    entry_idx = (entry.date.month-1)//3
                else:
                    entry_idx = (entry.date.month-1)
                if entry.postings:
                    for posting in entry.postings:
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
        fname = "GST.html"
        render_template(data={
            'template_name': "GST.tpl",
            'cfg': self.cfg,
            'gst': self.gst,
            'outfile': fname
        })
        return [fname]
