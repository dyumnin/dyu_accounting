"""
Tests for dyu_accounting.reconcile_upwork.

Builds small real intermediate .beancount files on disk (mirroring what
Upworks.py's merged-transaction output actually looks like - a withdrawal
is already fully balanced, with a *provisional* receivable value at the
withdrawal date's own rate) and runs the real reconcile_withdrawal()
against them, then re-reads the written output with beancount's own
loader.
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


# Provisional receivable = 5498.19 * 85.802474 = 471772.62... (rounds as below).
WITHDRAWAL = """
2025-06-30 * "Wire Transfer (USD) 9032" "Dyumnin Technologies"
  upwork_withdrawal: TRUE
  Assets:USD:Upwork                          -5498.19 USD @ 85.802474 INR
  Assets:INR:Cash:AccountReceivable:Upwork
  Assets:USD:Upwork                            -50.00 USD
  Expenses:USD:Upwork:WithdrawalFee             50.00 USD
"""

IDFC_UNRELATED = """
2025-08-01 * "POS-VISA/SOMETHING" ""
  Assets:INR:Cash:IDFC:Current  -500.00 INR
"""

IDFC_DEPOSIT = """
2025-07-10 * "IWRM202500096655CRE001" ""
  Assets:INR:Cash:IDFC:Current  466835.53 INR
"""


class TestReconcileWithdrawal:
    def test_true_up_adds_receivable_clear_and_gain_loss(self, tmp_path, monkeypatch):
        intermediate = _setup_fy(
            tmp_path, monkeypatch, WITHDRAWAL, IDFC_UNRELATED + IDFC_DEPOSIT
        )

        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 6, 30), datetime.date(2025, 7, 10)
        )

        idfc_entries = _load(intermediate / "idfc_bank_test.beancount")
        deposit = next(e for e in idfc_entries if e.date == datetime.date(2025, 7, 10))
        assert len(deposit.postings) == 3
        accounts = {p.account: float(p.units.number) for p in deposit.postings}
        assert accounts["Assets:INR:Cash:IDFC:Current"] == pytest.approx(466835.53)
        # Provisional receivable (5498.19 * 85.802474) gets cleared negative.
        expected_inr = float(5498.19) * 85.802474
        assert accounts["Assets:INR:Cash:AccountReceivable:Upwork"] == pytest.approx(-expected_inr, abs=0.01)
        # Auto-balances to whatever the other two postings need to sum to
        # zero: provisional - actual (positive here = a loss, since actual
        # settled for less than the provisional estimate).
        assert accounts["Assets:INR:ExchangeGain"] == pytest.approx(
            expected_inr - 466835.53, abs=0.01
        )

        # Unrelated IDFC entry untouched, and the Upwork-side transaction
        # itself was never modified.
        assert len(idfc_entries) == 2
        upwork_entries = _load(intermediate / "upworks_test.beancount")
        withdrawal = next(e for e in upwork_entries if e.date == datetime.date(2025, 6, 30))
        assert len(withdrawal.postings) == 4

    def test_no_matching_withdrawal_date_reports_and_does_not_crash(self, tmp_path, monkeypatch, capsys):
        _setup_fy(tmp_path, monkeypatch, WITHDRAWAL, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2099, 1, 1), datetime.date(2025, 7, 10)
        )
        assert "No Upwork withdrawal" in capsys.readouterr().out

    def test_no_matching_idfc_date_reports_and_does_not_crash(self, tmp_path, monkeypatch, capsys):
        _setup_fy(tmp_path, monkeypatch, WITHDRAWAL, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 6, 30), datetime.date(2099, 1, 1)
        )
        assert "No unresolved IDFC deposit" in capsys.readouterr().out

    def test_rerun_does_not_double_process(self, tmp_path, monkeypatch, capsys):
        """
        Once the IDFC entry is completed (no longer single-leg), re-running
        with the same dates must not find it again or double-count the gain.
        """
        _setup_fy(tmp_path, monkeypatch, WITHDRAWAL, IDFC_DEPOSIT)
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 6, 30), datetime.date(2025, 7, 10)
        )
        reconcile_withdrawal(
            "2025_26", datetime.date(2025, 6, 30), datetime.date(2025, 7, 10)
        )
        assert "No unresolved IDFC deposit" in capsys.readouterr().out
