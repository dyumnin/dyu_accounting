#! env python3
import sys
import datetime
import re
from beancount import loader
from beancount.core import amount
from beancount.core.number import D
from beancount.core import data
from beancount.parser import printer
#__plugins__ = ['report_gst']
# Python Script for GST Reporting. Reports data for GSTR 1 and GSTR 3
# Input GST(GST Paid during a purchase.) is an Asset
# Output GST(GST Collected during a Sale) is an Liability.
# For GST1 Report all GST collected during Sales.
# For GSR3 Report all GST paid during Purchase.


def report_gst(entries, options_map):
    errors = []
    # print("entries=%s\n Options=%s\n \n" % (repr(entries), repr(options_map)))
    # print("GST Plugin Invoked")
    # asset_re = re.compile(r'Assets.*GST')
    # liability_re = re.compile(r'Liabilities.*GST')
    gst = {}
    today = datetime.date.today()
    # cur_quarter = today.month//3
    # print(cur_quarter)
    for entry in entries:
        if isinstance(entry, data.Transaction):
            entry_year = entry.date.year
            entry_quarter = entry.date.month//3
            fy = str(entry_year-1) if entry_quarter == 0 else str(entry_year)
            gst[fy] = gst.get(fy, {})
            # print(repr(gst))
            entry_quarter = 'q4' if entry_quarter == 0 else 'q' + \
                str(entry_quarter)
            gst[fy][entry_quarter] = gst[fy].get(entry_quarter, {
                'asset': {}, 'liability': {}})
            if entry.postings:
                for posting in entry.postings:
                    # print(f" {entry_year} {entry_quarter} posting account = {repr(posting.account)}")
                    if re.search("Assets.*GST", posting.account):
                        gst[fy][entry_quarter]['asset'][posting.account] = amount.add(
                            gst[fy][entry_quarter]['asset'].get(
                                posting.account, amount.Amount(D(0), 'INR')),
                            posting.units)
                    if re.search("Liabilities.*GST", posting.account):
                        gst[fy][entry_quarter]['liability'][posting.account] = amount.add(
                            gst[fy][entry_quarter]['liability'].get(
                                posting.account, amount.Amount(D(0), 'INR')),
                            posting.units)

    print(" FY  Quarter Account                      GST3        GST1")
    blank=' '
    for fy in gst:
        for q in gst[fy]:
            for account in gst[fy][q]['asset']:
                print(f" {fy:5} {q:3} {account:14} {gst[fy][q]['asset'][account]} {blank:10}")
            for account in gst[fy][q]['liability']:
                print(f" {fy:5} {q:3} {account:14} {blank:10} {gst[fy][q]['liability'][account]} ")
#    print(f'GSTR3: {repr(asset)}')

    return entries, errors


if __name__ == "__main__":

    entries, errors, options = loader.load_file(
        sys.argv[1], log_errors=sys.stderr)
    # print(repr(errors))
    report_gst(entries, options)
    # depreciation(entries, options)
