#!env python3
from decimal import Decimal
import jinja2
import os
# import logging
import sys
import datetime
from beancount import loader
from beancount.core import amount
# from beancount.core.number import D
# import re
from beancount.core import data
from beancount.ops.summarize import balance_by_account, create_entries_from_balances
from dyu_accounting.Utilities import get_account_value, get_fy,  get_year_end, render_template

DEPRECIATION_TABLE = {
    'Furniture': {
        'block': 'furniture',
        'life': 10,
        'wdv': Decimal(25.88),
        'slm': Decimal(9.5),
        'it_wdv': Decimal(10)},

    'OfficeEquipment': {
        'block': 'furniture',
        'life': 5,
        'wdv': Decimal(45.07),
        'slm': Decimal(19.00),
        'it_wdv': Decimal(10)},

    'Phone': {
        'block': 'phone',
        'life': 5,
        'wdv': Decimal(45.07),
        'slm': Decimal(19.00),
        'it_wdv': Decimal(15)},

    'Server': {
        'block': 'laptop',
        'life': 6,
        'wdv': Decimal(39.3),
        'slm': Decimal(15),
        'it_wdv': Decimal(40)},

    'Laptop': {
        'block': 'laptop',
        'life': 3,
        'wdv': Decimal(63.16),
        'slm': Decimal(31.67),
        'it_wdv': Decimal(40)},

    'Electrical': {
        'block': 'furniture',
        'life': 10,
        'wdv': Decimal(25.88),
        'slm': Decimal(9.50),
        'it_wdv': Decimal(10)}
}

DEPRECIATION_ACCOUNT = 'Expenses:INR:Depreciation'
SCRAP_ACCOUNT = 'Expenses:INR:Scrap'


class Depreciation:
    def __init__(self, entries, options_map, cfg,
                 dept='MCA', method='wdv',
                 depreciation_csv=None,
                 depreciation_account=DEPRECIATION_ACCOUNT,
                 scrap_account_name=SCRAP_ACCOUNT):
        self.cfg = cfg
        self.close_date = datetime.date(cfg['fy'] + 1, 3, 31)
        self.entries = entries
        self.it_entries = []
        self.options_map = options_map
        self.dept = dept
        self.method = method
        self.depr = {'mca': [], 'it': {}, 'total': {'mca': {}, 'it': {}}}
        if depreciation_csv:
            self.mca = self.read_depreciation_from_csv(depreciation_csv)
        else:
            self.mca = DEPRECIATION_TABLE
        self.depr_account_name = depreciation_account
        self.scrap_account_name = scrap_account_name
        # self.it_blocks = {}
        if dept == 'IT':
            self._open_accounts()
        self.calc_depreciation()

        pass

    def _open_accounts(self):
        blocks = list(set([x['block'] for x in self.mca]))
        for b in blocks:
            for period in ['Full', 'Half']:
                # TODO add the balance sheet metadate to these accounts.
                data.Open(
                    meta={'balance_sheet': "assets.tangible"},
                    date=datetime.date(2000, 1, 1),
                    account=f"Assets:INR:Block:{b}:{period}",
                    currencies=['INR'])

    def read_depreciation_from_csv(self, file):
        mca = {}
        with open(file, newline='') as csvfile:
            mca_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            mca_reader.__next__()
            for row in mca_reader:
                mca[row[0]] = {
                    'block': row[1],
                    'life': int(row[2]),
                    'wdv': float(row[3]),
                    'slm': float(row[4]),
                    'it_wdv': Decimal(row[5])}
        return mca

    # Category,block,Life,mca_WDV,mca_SLM,it_wdv

    def mkCategories(self):
        categories = {}
        for entry in self.entries:
            if isinstance(entry, data.Open):
                if(entry.meta.get('depreciation_category')):
                    categories[entry.account] = entry.meta.get(
                        'depreciation_category')
        return categories

    def calc_depreciation(self):
        '''
        Read depreciation rate from file.
        create a table as follows
        tbl1[account]=category
        e.g.
        categories['x:y:x']='electrical'
        tbl2[category]={life:xx, mca_wdv_rate, it_rate}
        e.g.
          mca['electrical']=...
        for each posting:
           does the account match Equipment?
           Does it have a category?
           Calculate depreciation for life of asset.
           Write depreciation to depreciation.beancount
           write depreciation report to file
        '''
        entries = self.entries
        self.categories = self.mkCategories()
        errors = []
        fy_list = []
        self.dpr_entries = []
        for entry in entries:
            ''' Is asset depreciable?
            calculate half and full depriciation rate for
            the lifetime of the asset. as per mca or it.
            create a list of depreciation entries for the asset.
            return the list
            '''
            fy_list.append(get_fy(entry.date))
            self.dpr_entries.extend(self._update_depr_txn(entry))
        self.min_fy = min(fy_list)
        self.max_fy = get_fy(datetime.date.today())

        if self.dept != 'IT':
            pass
            # self.entries.extend(self.dpr_entries)
        else:
            '''
            We have only created the blocks for IT,
            now we need to calculate wdv block wise each year and
            transfer the amount.
            '''
            pass
        self._calc_it_depr(self.it_entries)
        self._calc_total_annual_depr()
        # 3
        #     depr_assets = get_depreciable_assets(entry, categories, mca)
        # calc_depreciation(depr_assets)
        # write_depreciation(entries_mca)
        # entries.extend(entries_mca)
        return self.dpr_entries, errors

    def _calc_total_annual_depr(self):
        for fy in range(self.min_fy, self.max_fy):
            self.depr['total']['mca'][fy] = Decimal()
            self.depr['total']['it'][fy] = Decimal()
            for account in self.depr['it']:
                self.depr['total']['it'][fy] = self.depr['total']['it'][fy] + \
                    self.depr['it'][account]['table'][fy]['depr']
            for asset in self.depr['mca']:
                if fy in asset['table']:
                    self.depr['total']['mca'][fy] =\
                        self.depr['total']['mca'][fy] + \
                        asset['table'][fy]

    def _calc_it_depr(self, entries):
        accounts = {}
        self.depr['it'] = {}
        x = [(self.mca[x]['block'], self.mca[x]['it_wdv'])
             for x in self.mca]
        dict_blocks = dict(list(set(x)))
        blocks = dict_blocks.keys()
        for b in blocks:
            for period in ['Full', 'Half']:
                account = f"Assets:INR:Block:{b}:{period}"
                full_account = f"Assets:INR:Block:{b}:Full"
                self.depr['it'][account] = {
                    'block': b, 'rate': dict_blocks[b], 'table': {}}
                accounts[account] = {'block': b,
                                     'period': period, 'full': full_account}
        for fy in range(self.min_fy, self.max_fy):
            """ For each year.
            1. Find balance by accounts at EOY.
            2. Calculate depreciation.
            3. Transfer depreciation
            4. Find balance by accounts
            5. Transfer half to full on 1st of next FY
            """
            entries = data.sorted(entries)
            bba = balance_by_account(
                entries, date=datetime.date(fy+1, 4, 1))[0]
            for account, hsh in accounts.items():
                value = bba[account]
                depr = value.get_currency_units(
                    'INR').number * dict_blocks[hsh['block']]/Decimal(100)
                if hsh['period'] == 'Half':
                    depr = depr/2

                self.depr['it'][account]['table'][fy] = {
                    'amount': value, 'depr': depr}
                fy_end = datetime.date(fy+1, 3, 31)
                entries.append(
                    transfer(
                        "Transfer Depreciation", account,
                        self.depr_account_name,
                        fy_end,
                        amount.Amount(depr, 'INR'), ""
                    ))
            entries = data.sorted(entries)
            bba = balance_by_account(
                entries, date=datetime.date(fy+1, 4, 1))[0]
            for account, hsh in accounts.items():
                if hsh['period'] == 'Half':
                    value = bba[account].get_currency_units('INR')
                    entries.append(
                        transfer(
                            "Transfer Half to Full", account,
                            hsh['full'],
                            datetime.date(fy+1, 4, 1),
                            value, ""
                        ))
            entries = data.sorted(entries)

            ############################


    def _update_depr_txn(self, entry):
        depr_posting = []
        depr_entries = []
        if isinstance(entry, data.Transaction):
            if entry.postings:
                for posting in entry.postings:
                    if posting.account in self.categories:
                        depr_posting.append(posting)
        for posting in depr_posting:
            if self.dept == 'MCA':
                depr_entries.extend(self.calc_mca(entry, posting, self.method))
            # else:  # IT Dept and wdv
            self.update_it_blocks(entry, posting)
        return depr_entries

    def update_it_blocks(self, entry, posting):
        fy = get_fy(entry.date)
        fy_end = datetime.date(fy+1, 3, 31)
        next_fy = datetime.date(fy+1, 4, 1)
        category = self.categories[posting.account]
        rate_table = self.mca[category]
        block = rate_table['block']
        if entry.date < fy_end - datetime.timedelta(days=180):
            period = 'Full'
        else:
            period = 'Half'
        t = transfer(entry.narration, posting.account,
                     f"Assets:INR:Block:{block}:{period}",
                     entry.date, posting.units, "Moving to IT Block")
        self.it_entries.append(t)

    def calc_mca(self, entry, posting, method='wdv'):
        fy = get_fy(entry.date)
        yearly_depr = {}
        txn = []
        category = self.categories[posting.account]
        rate_table = self.mca[category]
        rate = rate_table[method]
        opening = posting.units.number
        if method == 'slm':
            depr = opening * rate/100
        for i in range(rate_table['life']):
            if method == 'wdv':
                depr = opening * rate/100
            opening = opening - depr
            depr_amount = amount.Amount(depr, posting.units.currency)
            date = datetime.date(fy+1+i, 3, 31)
            yearly_depr[fy+i] = depr
            t = transfer(entry.narration, posting.account,
                         self.depr_account_name, date, depr_amount)
            txn.append(t)
        date = datetime.date(fy+1+rate_table['life'], 4, 1)
        t = transfer(entry.narration, posting.account,
                     self.scrap_account_name, date,
                     amount.Amount(opening, posting.units.currency))
        self.depr['mca'].append({
            'narration': entry.narration, 'category': category, 'rate': rate,
            'cost': posting.units, 'purchased_on': entry.date,
            'method': method, 'table': yearly_depr, 'scrap': opening})

        txn.append(t)
        # self.entries.extend(txn)
        return txn

    def report_depreciation(self, outdir):
        data = []
        for entry in self.dpr_entries:
            if entry.date == self.close_date:
                data.append({
                    'date': entry.date,
                    'narration': entry.narration,
                    'amount': entry.postings[0].units.number
                })

        filename = "depreciation.html"
        render_template(data={
            'template_name': "depreciation.tpl",
            'cfg': self.cfg,
            'depr': self.depr,
            'min_fy': self.min_fy,
            'max_fy': self.max_fy,
            'outfile': filename
        })
        return [filename]



def transfer(
        narration, fromAccount, toAccount,
        date, price,
        reason="Depreciation"):
    META = data.new_metadata(
        'foo', 12)
    FLAG = '*'
    txn = data.Transaction(
        META, date, FLAG, None,
        f"{reason} {date} for {narration}",
        data.EMPTY_SET, data.EMPTY_SET, [])
    data.create_simple_posting(
        txn, fromAccount, -1 * price.number, price.currency)
    data.create_simple_posting(
        txn, toAccount,  price.number, price.currency)
    return txn


if __name__ == "__main__":
    '''
    Steps
        - Find asset block.
        - assign to half or full year.
        - on  31st compute WDV and depreciation on
        half and full for each asset block.
        - Transfer half to full for next year.
    '''

    import csv
    entries, errors, options = loader.load_file(
        sys.argv[1], log_errors=sys.stderr)
    d = Depreciation(entries, options)
    d.report_depreciation(entries, options)
    d = Depreciation(entries, options, dept='IT')
    d.report_depreciation(entries, options)
    d = Depreciation(entries, options, dept='IT', method='wdv')
    d.report_depreciation(entries, options)
