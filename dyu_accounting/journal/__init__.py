import datetime
from beancount.core import data
import jinja2
import os


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
                    # print(entry)
                    for posting in entry.postings:
                        if posting.account in self.accounts:
                            pa = posting.account
                            self.accounts[pa].append(
                                {'date': entry.date.strftime("%d %b %Y"),
                                 'payee': entry.payee,
                                 'narration': entry.narration,
                                 'amount': posting.units})

    def report_journal(self, outdir):
        # print(self.accounts)
        templateEnv = jinja2.Environment(
            loader=jinja2.PackageLoader('dyu_accounting', 'templates'),
            trim_blocks=True,
            lstrip_blocks=True)
        fname = "journal.tpl"
        # # print(fname)
        template = templateEnv.get_template(fname)
        os.makedirs(outdir, exist_ok=True)
        reports = []
        for account in self.accounts:
            outputText = template.render(company=self.company,
                                         account=self.accounts[account],
                                         account_name=account,
                                         ay=self.fy+1)
            filename = f"journal_{account}.html"
            reports.append(filename)
            with open(
                    os.path.join(outdir, filename),
                    "w"
            ) as fy_file:
                fy_file.write(outputText)
        return reports
