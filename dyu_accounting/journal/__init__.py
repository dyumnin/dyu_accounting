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
        # Prefer discovering cash accounts straight from each account's own
        # `open` directive metadata (schedule3: "bs.cash", or the legacy
        # balance_sheet: "assets.cash") over a hand-maintained list in
        # config.json's cash_accounts, which silently goes stale (missing
        # new accounts, or renamed ones) whenever the chart of accounts
        # changes without a matching config.json edit.
        self.accounts = {}
        for entry in self.entries:
            if isinstance(entry, data.Open):
                schedule3 = entry.meta.get('schedule3')
                legacy = entry.meta.get('balance_sheet')
                if schedule3 == 'bs.cash' or legacy == 'assets.cash':
                    self.accounts[entry.account] = []
        for x in self.cfg.get('cash_accounts', []):
            self.accounts.setdefault(x, [])

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
            # Account names use ':' as a hierarchy separator (e.g.
            # 'Liabilities:INR:CreditCard'), but a ':' in the first segment
            # of a relative link target is ambiguous with a URI scheme per
            # RFC 3986 - browsers/link resolvers can treat it as an attempt
            # at an absolute URI (scheme 'journal_Liabilities', here) rather
            # than a relative file path, breaking the link. Only the
            # filename needs sanitizing; account_name below (used for
            # display inside the report) keeps the real account name.
            safe_account = account.replace(':', '_')
            filename = f"journal_{safe_account}.html"
            written = render_template(data={
                'template_name': "journal.tpl",
                'cfg': self.cfg,
                'account': self.accounts[account],
                'account_name': account,
                'outfile': filename
            })
            reports.append(written)
        return reports
