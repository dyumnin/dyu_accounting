import datetime
import logging
from decimal import Decimal

import petl
from forex_python.converter import CurrencyRates

from beancount.core import data
from beancount.core.amount import Amount

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    """
    Upwork's export has multiple rows per real-world event, all sharing one
    'Transaction ID': an Hourly/Fixed-price earning alongside its Service Fee
    and WHT rows, or a Withdrawal alongside its Withdrawal Fee row. These are
    merged here into one beancount transaction per Transaction ID (see
    prepare_table/_merge_group), rather than one transaction per CSV row like
    every other importer in this package - the accounting only makes sense
    merged (e.g. the withdrawal's principal amount needs to balance against
    its own fee row, and an earning's gross amount needs to balance against
    its fee rows and net wallet change, all at the same FX rate).

    - Earning (Hourly/Fixed-price) groups: Assets:USD:Upwork gets the net
      (gross minus fees) wallet change; Income:USD:UPWORKS:Client gets the
      gross amount; fee rows (Service Fee/WHT) get their own Expenses
      account. All four legs share the same @ rate price annotation (the
      earning date's USD/INR rate) - necessary so they stay in USD units
      (matching their Expenses:USD:*/Income:USD:* open directives) while
      still balancing by weight in INR; see conversation/commit history for
      why a single price on only one leg doesn't balance.
    - Withdrawal groups: fully balanced immediately, with the fee kept
      separate from the FX conversion since it's a flat USD cost, never
      itself converted:
        * the fee portion is a self-balanced, unpriced pair: Assets:USD:Upwork
          (Dr -fee) / Expenses:USD:Upwork:WithdrawalFee (Cr +fee);
        * the principal is priced at the withdrawal date's own auto-fetched
          rate (same mechanism as earnings) and targets
          Assets:INR:Cash:AccountReceivable:Upwork - a *provisional* INR
          value, since the real rate isn't known until the IDFC bank
          statement settles (10+ day lag is normal). reconcile_upwork.py
          later true's this up to the real amount once that's matched,
          posting the expected-vs-actual difference to
          Assets:INR:ExchangeGain.
    """

    IMPORTER_NAME = "Upworks Transaction Report"

    MAIN_TYPES = {"hourly", "fixed-price", "withdrawal"}
    FEE_TYPE_TO_ACCOUNT = {
        "wht": "Expenses:USD:Upwork:WHT",
        "service fee": "Expenses:USD:Upwork:ServiceFee",
        "withdrawal fee": "Expenses:USD:Upwork:WithdrawalFee",
    }
    INCOME_ACCOUNT = "Income:USD:UPWORKS:Client"
    RECEIVABLE_ACCOUNT = "Assets:INR:Cash:AccountReceivable:Upwork"

    def custom_init(self):
        # Upwork's own export is actually named '<date>_transaction_report.csv',
        # not prefixed with 'Upworks' as originally assumed.
        self.filename_pattern_def = r'(Upworks|.*transaction_report).*'
        # Real header: Date,Transaction ID,Transaction type,Transaction summary,
        # Transaction summary details,Description 1,Description 2,Description 3,
        # Agency team,Freelancer,Client team,Account name,PO,Ref ID,Amount $,
        # Amount in local currency,Currency,Current balance $,Payment method
        # Only a stable subset is listed here (skip_until_main_table only checks
        # that these show up in the header row, not that the row matches exactly),
        # so added/reordered columns don't break matching.
        self.column_labels_line = 'Date,Transaction type,Description 1,Account name,Amount $,Current balance $'
        self.currency = "USD"
        self.header_identifier = 'Date'
        self.date_format = '%b %d, %Y'
        self.header_map = {
            'Date': 'date',
            'Description 1': 'memo',
            'Amount $': 'amount',
            'Current balance $': 'balance',
            'Account name': 'payee',
        }
        self.skip_transaction_types = ['Journal']
        self._rates = CurrencyRates()
        self._rate_cache = {}

    def _get_rate(self, date):
        """Look up the historical USD/INR rate for a date, caching per date."""
        if date not in self._rate_cache:
            try:
                rate = self._rates.get_rate(
                    'USD', 'INR', datetime.datetime(date.year, date.month, date.day)
                )
                # Go through str() so the Decimal doesn't inherit binary-float
                # imprecision (D() does a plain Decimal(float) otherwise).
                self._rate_cache[date] = Decimal(str(round(rate, 6)))
            except Exception as err:
                logging.warning("Could not fetch USD/INR rate for %s: %s", date, err)
                self._rate_cache[date] = None
        return self._rate_cache[date]

    def _merge_group(self, rows):
        """Merge all CSV rows sharing one Transaction ID into a single dict."""
        main_rows = [r for r in rows if (r.get('Transaction type') or '').strip().lower() in self.MAIN_TYPES]
        main = main_rows[0] if main_rows else rows[0]
        fee_rows = [r for r in rows if r is not main]
        is_withdrawal = (main.get('Transaction type') or '').strip().lower() == 'withdrawal'

        extra_postings = []
        for r in fee_rows:
            ftype = (r.get('Transaction type') or '').strip().lower()
            account = self.FEE_TYPE_TO_ACCOUNT.get(ftype)
            amount_str = r.get('Amount $')
            if account and amount_str not in (None, ''):
                # Fee rows are negative (money leaving the wallet); the
                # matching Expenses posting is the positive mirror of that.
                extra_postings.append((account, -Decimal(str(amount_str))))

        main_amount = Decimal(str(main.get('Amount $') or '0'))
        date = datetime.datetime.strptime(main['Date'].strip(), self.date_format).date()
        rate = self._get_rate(date)

        merged = dict(main)
        merged['is_withdrawal'] = is_withdrawal
        merged['extra_postings'] = extra_postings
        merged['gross_amount'] = str(main_amount)
        merged['foreign_amount'] = rate
        merged['foreign_currency'] = 'INR' if rate else None
        if is_withdrawal:
            # Principal only - the fee is handled as its own self-balanced,
            # unpriced pair in add_custom_postings (a flat USD cost, never
            # itself converted), kept separate from this priced leg.
            merged['Amount $'] = str(main_amount)
            merged['fee_total'] = str(sum((amt for _, amt in extra_postings), Decimal(0)))
        else:
            # extra_postings already hold the positive Expense amounts; the
            # wallet's net change subtracts them from the gross earning.
            net_amount = main_amount - sum((amt for _, amt in extra_postings), Decimal(0))
            merged['Amount $'] = str(net_amount)
        return merged

    def prepare_table(self, rdr):
        rows = list(petl.dicts(rdr))
        groups = {}
        order = []
        for row in rows:
            txn_id = row.get('Transaction ID')
            if txn_id not in groups:
                groups[txn_id] = []
                order.append(txn_id)
            groups[txn_id].append(row)

        merged_rows = [self._merge_group(groups[txn_id]) for txn_id in order]
        return petl.fromdicts(merged_rows)

    def get_target_account(self, ot):
        """
        Withdrawal groups target the INR receivable (a provisional value at
        the withdrawal date's own rate - reconcile_upwork.py true's this up
        once the real bank-side amount is known). Earnings target the USD
        income account; add_custom_postings() below fixes it up to be
        explicit and same-priced as the main leg (see class docstring).
        """
        if getattr(ot, "is_withdrawal", False):
            return self.RECEIVABLE_ACCOUNT
        return self.INCOME_ACCOUNT

    def add_custom_postings(self, entry, ot):
        extra_postings = getattr(ot, "extra_postings", None) or []

        if getattr(ot, "is_withdrawal", False):
            fee_total = Decimal(str(getattr(ot, "fee_total", "0") or "0"))
            if fee_total:
                # Self-balanced pair, deliberately unpriced: a flat USD cost
                # already fully known, not part of the FX conversion.
                data.create_simple_posting(entry, self.config["main_account"], -fee_total, "USD")
            for account, amount in extra_postings:
                data.create_simple_posting(entry, account, amount, "USD")
            return

        main = entry.postings[0]
        price = main.price
        gross = Decimal(str(getattr(ot, "gross_amount", "0") or "0"))

        if price is not None and entry.postings and entry.postings[-1].units is None:
            target = entry.postings[-1]
            entry.postings[-1] = data.Posting(
                target.account,
                Amount(-gross, main.units.currency),
                None,
                price,
                target.flag,
                target.meta,
            )

        for account, amount in extra_postings:
            entry.postings.append(
                data.Posting(account, Amount(amount, "USD"), None, price, None, None)
            )

    def build_metadata(self, file, metatype=None, data={}):
        meta = super().build_metadata(file, metatype, data)
        if metatype == "transaction":
            ot = data.get("transaction")
            if getattr(ot, "is_withdrawal", False):
                # Lets reconcile_upwork.py reliably find these rather than
                # guessing from account names/posting count.
                meta["upwork_withdrawal"] = True
        return meta

    def skip_transaction(self, row):
        if row.date is None:
            logging.debug("skipping row with no date: %s", row)
        return row.date is None
