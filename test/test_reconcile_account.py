"""
Tests for dyu_accounting.reconcile_account.

Builds small real intermediate .beancount files on disk and runs the actual
reconcile_fy() against them (not mocks), then re-reads the written output
with beancount's own loader - the same class of bug this whole feature
exists to avoid (duplicate-counting a transaction) only shows up end-to-end.
"""
import pytest

beancount_loader = pytest.importorskip('beancount.loader', reason='beancount is required')

from beancount.core import data

from dyu_accounting.reconcile_account import reconcile_fy


def _setup_fy(tmp_path, monkeypatch, account_content, source_files):
    """
    Write FY2025_26/intermediate/account_test.beancount plus whatever other
    intermediate files are given in source_files ({filename: content}), cd
    into tmp_path, and return the intermediate dir Path.
    """
    intermediate = tmp_path / "FY2025_26" / "intermediate"
    intermediate.mkdir(parents=True)
    (intermediate / "account_test.beancount").write_text(account_content)
    for filename, content in source_files.items():
        (intermediate / filename).write_text(content)
    monkeypatch.chdir(tmp_path)
    return intermediate


def _load(path):
    entries, _errors, _options = beancount_loader.load_file(str(path))
    return [e for e in entries if isinstance(e, data.Transaction)]


class TestReconcileMatching:
    def test_matched_entry_gets_second_leg_and_receipt(self, tmp_path, monkeypatch):
        account_content = """
2025-04-14 * "Food" ""
  receipt: "https://example.com/r1"
  Assets:INR:Cash:IDFC:Current  547.21 INR
  Expenses:Food
"""
        source_content = """
2025-04-14 * "POS-VISA/SOME MERCHANT" "1"
  Assets:INR:Cash:IDFC:Current  -547.21 INR
"""
        intermediate = _setup_fy(
            tmp_path, monkeypatch, account_content,
            {"idfc_bank_test.beancount": source_content}
        )

        reconcile_fy("2025_26")

        source_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(source_entries) == 1
        entry = source_entries[0]
        assert len(entry.postings) == 2
        assert entry.meta.get('receipt') == "https://example.com/r1"
        accounts = {p.account for p in entry.postings}
        assert accounts == {"Assets:INR:Cash:IDFC:Current", "Expenses:Food"}
        # Balances: the IDFC posting is -547.21, so Expenses:Food must be +547.21.
        food_posting = next(p for p in entry.postings if p.account == "Expenses:Food")
        assert float(food_posting.units.number) == pytest.approx(547.21)

        # The matched entry must not also remain in the Account file (no double-count).
        leftover = _load(intermediate / "account_test.beancount")
        assert len(leftover) == 0

    def test_outside_date_window_is_not_matched(self, tmp_path, monkeypatch):
        account_content = """
2025-04-01 * "Food" ""
  Assets:INR:Cash:IDFC:Current  547.21 INR
  Expenses:Food
"""
        source_content = """
2025-04-14 * "POS-VISA/SOME MERCHANT" "1"
  Assets:INR:Cash:IDFC:Current  -547.21 INR
"""
        intermediate = _setup_fy(
            tmp_path, monkeypatch, account_content,
            {"idfc_bank_test.beancount": source_content}
        )

        reconcile_fy("2025_26")

        source_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(source_entries) == 1
        assert len(source_entries[0].postings) == 1  # left untouched

        leftover = _load(intermediate / "account_test.beancount")
        assert len(leftover) == 1  # left for manual review, not dropped

    def test_different_amount_is_not_matched(self, tmp_path, monkeypatch):
        account_content = """
2025-04-14 * "Food" ""
  Assets:INR:Cash:IDFC:Current  500.00 INR
  Expenses:Food
"""
        source_content = """
2025-04-14 * "POS-VISA/SOME MERCHANT" "1"
  Assets:INR:Cash:IDFC:Current  -547.21 INR
"""
        intermediate = _setup_fy(
            tmp_path, monkeypatch, account_content,
            {"idfc_bank_test.beancount": source_content}
        )

        reconcile_fy("2025_26")

        source_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(source_entries[0].postings) == 1

        leftover = _load(intermediate / "account_test.beancount")
        assert len(leftover) == 1

    def test_within_tolerance_rounding_is_matched(self, tmp_path, monkeypatch):
        account_content = """
2025-04-14 * "Food" ""
  Assets:INR:Cash:IDFC:Current  547.21 INR
  Expenses:Food
"""
        source_content = """
2025-04-14 * "POS-VISA/SOME MERCHANT" "1"
  Assets:INR:Cash:IDFC:Current  -547.215 INR
"""
        intermediate = _setup_fy(
            tmp_path, monkeypatch, account_content,
            {"idfc_bank_test.beancount": source_content}
        )

        reconcile_fy("2025_26")

        source_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(source_entries[0].postings) == 2


class TestReconcileCash:
    def test_cash_entries_go_to_cash_beancount_untouched(self, tmp_path, monkeypatch):
        account_content = """
2025-04-14 * "Food" ""
  receipt: "https://example.com/cash1"
  Assets:INR:Cash:CashInHand  200.00 INR
  Expenses:Food
"""
        intermediate = _setup_fy(tmp_path, monkeypatch, account_content, {})

        reconcile_fy("2025_26")

        cash_entries = _load(intermediate / "cash.beancount")
        assert len(cash_entries) == 1
        assert len(cash_entries[0].postings) == 2
        assert cash_entries[0].meta.get('receipt') == "https://example.com/cash1"

        leftover = _load(intermediate / "account_test.beancount")
        assert len(leftover) == 0  # moved to cash.beancount, not duplicated here too

    def test_rerun_does_not_lose_previously_reconciled_cash_entries(self, tmp_path, monkeypatch):
        """
        Regression test: a cash entry only appears in account_*.beancount
        the one run where it gets moved out to cash.beancount. A later
        reconcile_fy() call (e.g. after importing more files) must not
        overwrite cash.beancount with only that run's (possibly empty) cash
        entries and lose what a previous run already wrote there.
        """
        account_content = """
2025-04-14 * "Food" ""
  Assets:INR:Cash:CashInHand  200.00 INR
  Expenses:Food
"""
        intermediate = _setup_fy(tmp_path, monkeypatch, account_content, {})
        reconcile_fy("2025_26")
        assert len(_load(intermediate / "cash.beancount")) == 1

        # Second run: account_test.beancount now has nothing left in it
        # (the cash entry was already moved out), simulating a later re-run.
        (intermediate / "account_test.beancount").write_text(
            ";; Unmatched Account (Google Form) entries - review manually\n"
        )
        reconcile_fy("2025_26")

        assert len(_load(intermediate / "cash.beancount")) == 1

    def test_revives_bean_extract_duplicate_commented_entries(self, tmp_path, monkeypatch):
        """
        Regression test: beancount.ingest.extract.print_extracted_entries
        comments out (prefixes every line with '; ') any entry it believes
        already exists in the target ledger passed via -f/-e. If an
        intermediate file is re-extracted after the parent ledger already
        includes its entries, every one of them comes back like this -
        otherwise invisible to beancount's parser, so a real transaction
        that already exists elsewhere (possibly already reconciled) could
        never be matched again on a later --reconcile-account run.
        """
        account_content = """
2025-04-14 * "Food" ""
  Assets:INR:Cash:IDFC:Current  547.21 INR
  Expenses:INR:Food
"""
        # Exactly bean-extract's own duplicate-comment format.
        source_content = (
            "; 2025-04-14 * \"POS-VISA/SOME MERCHANT\" \"1\"\n"
            ";   Assets:INR:Cash:IDFC:Current  -547.21 INR\n"
        )
        intermediate = _setup_fy(
            tmp_path, monkeypatch, account_content,
            {"idfc_bank_test.beancount": source_content}
        )

        reconcile_fy("2025_26")

        source_entries = _load(intermediate / "idfc_bank_test.beancount")
        assert len(source_entries) == 1
        assert len(source_entries[0].postings) == 2

    def test_parent_ledger_includes_cash_beancount(self, tmp_path, monkeypatch):
        """
        Regression test: cash.beancount didn't exist when --guided last
        generated FY{fy}.beancount's include list, so a cash entry would be
        silently missing from the final ledger unless reconcile_fy()
        regenerates that include list afterwards.
        """
        account_content = """
2025-04-14 * "Food" ""
  Assets:INR:Cash:CashInHand  200.00 INR
  Expenses:INR:Food
"""
        intermediate = _setup_fy(tmp_path, monkeypatch, account_content, {})
        reconcile_fy("2025_26")

        parent = (tmp_path / "FY2025_26" / "FY2025_26.beancount").read_text()
        assert 'include "intermediate/cash.beancount"' in parent
        assert 'include "intermediate/account_test.beancount"' in parent

    def test_no_account_files_is_a_no_op(self, tmp_path, monkeypatch):
        (tmp_path / "FY2025_26" / "intermediate").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        reconcile_fy("2025_26")  # must not raise
        assert not (tmp_path / "FY2025_26" / "intermediate" / "cash.beancount").exists()
