"""
dyu_accounting

A Business accounting package conformant to Indian accounting norms
"""
import jinja2
import json
from os.path import exists
import os
import argparse
import sys
import beancount
from beancount import loader
import dyu_accounting.pnl as pnl
import dyu_accounting.exchange_gain as exchange_gain
import dyu_accounting.balance_sheet as bsheet
from dyu_accounting.gst import GST
import dyu_accounting.depreciation as depr
import dyu_accounting.journal as journal
from dyu_accounting.Utilities import render_template
import logging
logging.basicConfig(filename="dyuAccount.log",
                    filemode='w', level=logging.DEBUG)
logging.debug("Testing")

__version__ = "0.1.0"
__author__ = 'Vijayvithal Jahagirdar'
__credits__ = 'Dyumnin Semiconductors OPC Pvt Ltd'


def accounting():
    logger = logging.getLogger('Accounting: ')
    with open("config.json", "r") as jfile:
        cfg = json.load(jfile)

    parser = argparse.ArgumentParser(
        description='A Python Package for Indian Accounting')
    parser.add_argument('--outdir', default="Output", help="Output Folder")
    parser.add_argument('--infile', required=True, help="Input Ledger File")
    # parser.add_argument('--cname', required=True, help="Company Name")
    # parser.add_argument('--caddr', required=True, help="Company Address")
    parser.add_argument('--fy', required=True, type=int,
                        help="Generate Reports for the financial year(Starts 1st April)")
    opts = parser.parse_args()
    cfg['fy'] = opts.fy
    cfg['outdir'] = opts.outdir
    entries, errors, options = loader.load_file(
        opts.infile, log_errors=sys.stderr)

    os.makedirs(opts.outdir, exist_ok=True)
    if opts.fy:
        reports = {}
        d = depr.Depreciation(entries, options, cfg)
        reports['depreciation'] = d.report_depreciation(opts.outdir)
        exc_gain = exchange_gain.ExchangeGain(cfg)
        entries.extend(exc_gain.calc_gains(entries))
        entries = beancount.core.data.sorted(entries)
        pnl_stmt = pnl.PnL(entries, options, cfg)
        pnl_stmt.set_depreciation(d.depr['total']['mca'][opts.fy])
        reports['pnl'] = pnl_stmt.report_pnl(opts.outdir)
        j = journal.Journal(entries, options, cfg)
        reports['journal'] = j.report_journal(opts.outdir)
        bs = bsheet.BalanceSheet(entries, options, cfg)
        bs.mkBalanceSheet(opts.fy - 1)
        bs.mkBalanceSheet(opts.fy)
        logger.debug(f'Account is {bs.balancesheet}')
        reports['balance_sheet'] = bs.report_balance_sheet()
        gst = GST(entries, options, cfg)
        reports['gst'] = gst.report_gst()

        filename = "index.html"
        render_template(data={
            'template_name': 'index.tpl',
            'cfg': cfg,
            'reports': reports,
            'outfile': filename
        })
