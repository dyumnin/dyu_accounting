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
    """
    Main entry point for accounting CLI.

    Supports:
    1. Legacy mode: account --in ledger.beancount --fy 2026 --out reports/
    2. Guided mode: account --guided
    3. Account reconciliation: account --reconcile-account --fy 2025_26

    This maintains backward compatibility while adding the new guided workflow.
    """
    # Import guided_mode here to avoid circular imports
    try:
        from dyu_accounting.guided_mode import async_guided_workflow
        guided_available = True
    except ImportError:
        guided_available = False

    # Check if --guided flag is present
    if '--guided' in sys.argv:
        if not guided_available:
            print("Error: guided mode modules not available")
            sys.exit(1)
        # Remove --guided from argv so argparse doesn't see it
        sys.argv.remove('--guided')
        async_guided_workflow()
        return

    # Check if --reconcile-account flag is present
    if '--reconcile-account' in sys.argv:
        sys.argv.remove('--reconcile-account')
        fy_arg = None
        if '--fy' in sys.argv:
            fy_idx = sys.argv.index('--fy')
            if fy_idx + 1 < len(sys.argv):
                fy_arg = sys.argv[fy_idx + 1]
                del sys.argv[fy_idx:fy_idx + 2]
        if not fy_arg:
            print("Error: --reconcile-account requires --fy <year> (e.g. --fy 2025_26)")
            sys.exit(1)
        from dyu_accounting.Utilities import parse_financial_year_input
        from dyu_accounting.reconcile_account import reconcile_fy
        reconcile_fy(parse_financial_year_input(fy_arg))
        return

    # Legacy mode (backward compatible)
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
        mkWriter(cfg)
        d = depr.Depreciation(entries, options, cfg)
        reports['depreciation'] = d.report_depreciation(opts.outdir)
        try:
            exc_gain = exchange_gain.ExchangeGain(cfg)
            entries.extend(exc_gain.calc_gains(entries))
            entries = beancount.core.data.sorted(entries)
        except Exception as e:
            logger.info(e)
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


def mkWriter(cfg):
    writer = open(os.path.join(cfg['outdir'], "report.tex"), "w")
    cfg['texwriter'] = writer
    templateEnv = jinja2.Environment(
        loader=jinja2.PackageLoader(
            'dyu_accounting', os.path.join('templates', 'tex')),
        trim_blocks=True,
        lstrip_blocks=True)
    template = templateEnv.get_template("latex_header.tpl")
    outputText = template.render({
        'cfg': cfg
    })
    writer.write(outputText)
    return writer
