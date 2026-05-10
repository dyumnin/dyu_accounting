import jinja2
from beancount.core import data
import re
import datetime
import os


def get_account_value(entries, account_name, start_date=None, end_date=None):
    """
    Returns:
        float: The sum of value of all postings to an account in a given timeframe.
    Args:
        entries: Beancount list of entries
        account_name (str): A pattern that matches the account name.
            This will select the account and sub accounts.
            If only account is required end pattern with $
        start_date (datetime.date): The date (inclusive) from which to search for entries.
            If None, from start of accounting.
        end_date (datetime.date): The date (inclusive) till which to search for entries.
            If None, till end of accounting.
    """
    e = entries
    if start_date is not None:
        e = [x for x in e if x.date >= start_date]
    if end_date is not None:
        e = [x for x in e if x.date <= end_date]
    transactions = [x for x in e if isinstance(x, data.Transaction)]
    postings = [p for txn in transactions for p in txn.postings]
    values = [p.units.number for p in postings if re.match(account_name, p.account)]
    return sum(values)


def get_fy(date):
    entry_year = date.year
    entry_month = date.month
    fy = entry_year-1 if entry_month < 4 else entry_year
    return fy


def get_year_end(date):
    entry_year = date.year
    entry_month = date.month
    fy = entry_year-1 if entry_month < 4 else entry_year

    return datetime.date(fy+1, 3, 31)


def get_quarter(date):
    m = date.month
    if m < 4:
        return 'q4'
    return 'q' + str((m - 4) // 3 + 1)


def hoh(base, *keys):
    x = base
    for k in keys:
        if k not in x:
            x[k] = {}
        x = x[k]
    return base


def render_template(data):
    templateEnv = jinja2.Environment(
        loader=jinja2.PackageLoader('dyu_accounting', 'templates'),
        trim_blocks=True,
        lstrip_blocks=True)
    fname = data['template_name']
    template = templateEnv.get_template(fname)
    outputText = template.render(data)
    filename = data['outfile']
    with open(os.path.join(data['cfg']['outdir'], filename), "w") as fy_file:
        fy_file.write(outputText)
