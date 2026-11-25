"""
Tests for dyu_accounting.reconcile_upwork.

Builds small real intermediate .beancount files on disk (mirroring what
Upworks.py's merged-transaction output actually looks like) and runs the
real reconcile_withdrawal() against them, then re-reads the written output
with beancount's own loader.
"""
import datetime

import pytest

beancount_loader = pytest.importorskip('beancount.loader', reason='beancount is required')

from beancount.core import data

from dyu_accounting.reconcile_upwork import reconcile_withdrawal


def _setup_fy(tmp_path, monkeypatch, upwork_content, idfc_content):
    intermediate = tmp_path / "FY2025_26" / "intermediate"
    intermediate.mkdir(parents=True)
    (intermediate / "upworks_test.beancount").write_text(upwork_content)
    (intermediate / "idfc_bank_test.beancount").write_text(idfc_content)
    monkeypatch.chdir(tmp_path)
    return intermediate


def _load(path):
    entries, _errors, _options = beancount_loader.load_file(str(path))
    return [e for e in entries if isinstance(e, data.Transaction)]


EARNING_1 = """
2025-07-11 * "Earnings for Jun 30-Jul 6, 2025" "Dyumnin Technologies"
  Assets:USD:Upwork              22.47 USD @ 85.822135 INR
  Income:USD:UPWORKS:Client     -25.00 USD @ 85.822135 INR
  Expenses:USD:Upwork:ServiceFee  2.50 USD @ 85.822135 INR
  Expenses:USD:Upwork:WHT         0.03 USD @ 85.822135 INR
"""

EARNING_2 = """
2025-09-04 * "Earnings for Aug 25-Aug 31, 2025" "Dyumnin Technologies"
  Assets:USD:Upwork             997.89 USD @ 85.5 INR
  Income:USD:UPWORKS:Client   -1020.3 USD @ 85.5 INR
  Expenses:USD:Upwork:ServiceFee 22.0 USD @ 85.5 INR
  Expenses:USD:Upwork:WHT        0.41 USD @ 85.5 INR
"""

WITHDRAWAL = """
2025-09-29 * "Wire Transfer (USD) 9032" "Dyumnin Technologies"
  upwork_withdrawal: TRUE
  Assets:USD:Upwork               -970.36 USD
  Expenses:USD:Upwork:WithdrawalFee 50.00 USD
"""

IDFC_UNRELATED = """
2025-08-01 * "POS-VISA/SOMETHING" ""
  Assets:INR:Cash:IDFC:Current  -500.00 INR
"""

IDFC_DEPOSIT = """
2025-10-09 * "IWRM202500149813CRE001" ""
  Assets:INR:Cash:IDFC:Current  84000.00 INR
"""


class TestReconcileWithdrawal:
    def test_completes_withdrawal_and_removes_idfc_duplicate(self, tmp_path, monkeypatch):
        intermediate = _setup_fy(
            tmp_path, monkeypatch,
            EARNING_1 + EARNING_2 + WITHDRAWAL,
            IDFC_UNRELATED + IDFC_DEPOSIT,
        )

        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 9, 29), datetime.date(2025, 10, 9)
        )

        upwork_entries = _load(intermediate / "upworks_test.beancount")
        withdrawal = next(e for e in upwork_entries if e.date == datetime.date(2025, 9, 29))
        assert len(withdrawal.postings) == 4
        accounts = {p.account: p for p in withdrawal.postings}
        assert "Assets:INR:Cash:IDFC:Current" in accounts
        assert float(accounts["Assets:INR:Cash:IDFC:Current"].units.number) == pytest.approx(84000.00)
        assert "Assets:INR:ExchangeGain" in accounts
        # The principal and fee legs both got the blended rate as their price.
        assert accounts["Assets:USD:Upwork"].price is not None
        assert accounts["Expenses:USD:Upwork:WithdrawalFee"].price is not None
        assert (accounts["Assets:USD:Upwork"].price.number
                == accounts["Expenses:USD:Upwork:WithdrawalFee"].price.number)

        idfc_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(idfc_entries) == 1  # the unrelated POS entry only
        assert idfc_entries[0].date == datetime.date(2025, 8, 1)

    def test_blended_rate_excludes_fee_and_earlier_withdrawals(self, tmp_path, monkeypatch):
        """
        Only EARNING_2 (after the implicit "no previous withdrawal" start,
        up to and including the withdrawal date) should feed the blended
        rate here, since there's no earlier withdrawal to bound the window -
        both EARNING_1 and EARNING_2 are in-window. Expected rate should be
        the USD-weighted average of their per-earning rates, not including
        the withdrawal's own fee.
        """
        intermediate = _setup_fy(
            tmp_path, monkeypatch,
            EARNING_1 + EARNING_2 + WITHDRAWAL,
            IDFC_DEPOSIT,
        )
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 9, 29), datetime.date(2025, 10, 9)
        )
        upwork_entries = _load(intermediate / "upworks_test.beancount")
        withdrawal = next(e for e in upwork_entries if e.date == datetime.date(2025, 9, 29))
        principal = next(p for p in withdrawal.postings if p.account == "Assets:USD:Upwork")

        total_usd = float(22.47 + 997.89)
        total_weight = float(22.47) * 85.822135 + float(997.89) * 85.5
        expected_blended = total_weight / total_usd
        assert float(principal.price.number) == pytest.approx(expected_blended, rel=1e-6)

    def test_already_reconciled_withdrawal_is_skipped(self, tmp_path, monkeypatch, capsys):
        already_done = """
2025-09-29 * "Wire Transfer (USD) 9032" "Dyumnin Technologies"
  upwork_withdrawal: TRUE
  Assets:USD:Upwork               -970.36 USD @ 85.5 INR
  Expenses:USD:Upwork:WithdrawalFee 50.00 USD @ 85.5 INR
  Assets:INR:Cash:IDFC:Current    84000.00 INR
  Assets:INR:ExchangeGain
"""
        _setup_fy(tmp_path, monkeypatch, already_done, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 9, 29), datetime.date(2025, 10, 9)
        )
        assert "already" in capsys.readouterr().out.lower()

    def test_no_matching_withdrawal_date_reports_and_does_not_crash(self, tmp_path, monkeypatch, capsys):
        _setup_fy(tmp_path, monkeypatch, WITHDRAWAL, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2099, 1, 1), datetime.date(2025, 10, 9)
        )
        assert "No Upwork withdrawal" in capsys.readouterr().out

    def test_no_matching_idfc_date_reports_and_does_not_crash(self, tmp_path, monkeypatch, capsys):
        _setup_fy(tmp_path, monkeypatch, EARNING_1 + WITHDRAWAL, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 9, 29), datetime.date(2099, 1, 1)
        )
        assert "No unresolved IDFC deposit" in capsys.readouterr().out
