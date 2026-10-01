import datetime
from beancount.core import data
import jinja2
import os
from dyu_accounting.Utilities import render_template


class Journal:
    def __init__(self, entries, options_map, cfg):
        self.entries = entries
        self.cfg = cfg
        self.fy = cfg['fy']
        self.company = cfg['company']
        self.open_date = datetime.date(self.fy, 4, 1)
        self.close_date = datetime.date(self.fy + 1, 3, 31)
        self.options_map = options_map
        self.find_cash_accounts()
        self.find_cash_transactions()

    def find_cash_accounts(self):
        self.accounts = {}
        for x in self.cfg['cash_accounts']:
            self.accounts[x] = []
        # self.accounts = {}
        # for entry in self.entries:
        #     if isinstance(entry, data.Open):
        #         if(entry.meta.get('balance_sheet')) == "assets.cash":
        #             self.accounts[entry.account] = []

    def find_cash_transactions(self):
        for entry in self.entries:
            if isinstance(entry, data.Transaction):
                if (
                        entry.date >= self.open_date
                        and entry.date <= self.close_date
                ):
                    for posting in entry.postings:
                        if posting.account in self.accounts:
                            pa = posting.account
                            self.accounts[pa].append(
                                {'date': entry.date.strftime("%d %b %Y"),
                                 'payee': entry.payee,
                                 'narration': entry.narration,
                                 'amount': posting.units})

    def report_journal(self, outdir):
        reports = []
        for account in self.accounts:
            filename = f"journal_{account}.html"
            render_template(data={
                'template_name': "journal.tpl",
                'cfg': self.cfg,
                'account': self.accounts[account],
                'account_name': account,
                'outfile': filename
            })
            reports.append(filename)
        return reports
