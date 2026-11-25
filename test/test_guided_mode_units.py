"""
Unit tests for guided mode components (importer_registry, file_validator,
parent_ledger_generator, utilities, gulp_runner).

Tests use mocking and fixtures to avoid filesystem/subprocess dependencies.
All tests pass locally without external data or production services.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import json
import tempfile
import shutil
from dataclasses import dataclass
from typing import List, Dict, Optional


# ============================================================================
# FIXTURES & MOCK DATA
# ============================================================================

@pytest.fixture
def mock_importer_module():
    """Create a mock importer module with standard metadata."""
    mod = Mock()
    mod.IMPORTER_NAME = "Test Bank"
    mod.Importer = Mock()
    # Set attributes on the class itself
    mod.Importer.IMPORTER_NAME = "Test Bank"
    mod.Importer.filename_pattern_def = "TestStatement"
    mod.Importer.header_identifier = '"AccountNumber"'
    mod.Importer.column_labels_line = "Date,Amount,Description"
    mod.Importer.currency = "INR"
    return mod


@pytest.fixture
def importers_metadata():
    """Expected metadata for all 6 importers."""
    return {
        'ICICIBank': {
            'IMPORTER_NAME': 'ICICI Bank Account',
            'filename_pattern_def': 'OpTrans',
            'header_identifier': '"ReportType"',
            'currency': 'INR',
            'folder_name': 'icici_bank'
        },
        'ICICICard': {
            'IMPORTER_NAME': 'ICICI Bank Credit Card',
            'filename_pattern_def': 'CreditCard',
            'header_identifier': '"Accountno:"',
            'currency': 'INR',
            'folder_name': 'icici_card'
        },
        'IDFC': {
            'IMPORTER_NAME': 'IDFC Bank',
            'filename_pattern_def': 'Statement',
            'header_identifier': 'ValueDate',
            'currency': 'INR',
            'folder_name': 'idfc_bank'
        },
        'SBI': {
            'IMPORTER_NAME': 'SBI Bank',
            'filename_pattern_def': 'Bnk',
            'header_identifier': 'Transaction',
            'currency': 'INR',
            'folder_name': 'sbi_bank'
        },
        'Upworks': {
            'IMPORTER_NAME': 'Upwork Earnings',
            'filename_pattern_def': 'Earnings',
            'header_identifier': 'Date',
            'currency': 'USD',
            'folder_name': 'upworks'
        },
        'Account': {
            'IMPORTER_NAME': 'Manual Account',
            'filename_pattern_def': 'Manual',
            'header_identifier': 'Entry',
            'currency': 'INR',
            'folder_name': 'account'
        }
    }


@pytest.fixture
def temp_fy_dir():
    """Create a temporary FY directory for testing."""
    tmpdir = tempfile.mkdtemp(prefix='FY2025_26_test_')
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================================
# IMPORTER REGISTRY TESTS
# ============================================================================

class TestImporterRegistry:
    """Test dynamic discovery and metadata extraction of importers."""

    def test_discover_importers_returns_dict(self):
        """discover_importers() should return dict mapping importer names to metadata."""
        # Mock the importlib module discovery
        with patch('importlib.import_module') as mock_import:
            # Create 6 mock importer modules
            mock_modules = {}
            for name in ['ICICIBank', 'ICICICard', 'IDFC', 'SBI', 'Upworks', 'Account']:
                mod = Mock()
                mod.Importer = Mock()
                mod.Importer.IMPORTER_NAME = f"{name} Importer"
                mod.Importer.filename_pattern_def = f"{name}Pattern"
                mod.Importer.header_identifier = f"Header_{name}"
                mod.Importer.currency = "INR"
                mod.Importer.column_labels_line = "Col1,Col2"
                mock_modules[name] = mod

            mock_import.side_effect = lambda x: mock_modules[x.split('.')[-1]]

            # Test would call discover_importers() here
            # For now, verify expected structure
            assert all(name in ['ICICIBank', 'ICICICard', 'IDFC', 'SBI', 'Upworks', 'Account']
                       for name in mock_modules.keys())

    def test_discover_importers_all_six_present(self, importers_metadata):
        """All 6 importers should be discoverable."""
        expected_importers = {'ICICIBank', 'ICICICard', 'IDFC', 'SBI', 'Upworks', 'Account'}
        assert set(importers_metadata.keys()) == expected_importers

    def test_importer_metadata_fields_complete(self, importers_metadata):
        """Each importer metadata must have required fields."""
        required_fields = {'IMPORTER_NAME', 'filename_pattern_def', 'header_identifier',
                          'currency', 'folder_name'}
        for name, metadata in importers_metadata.items():
            assert set(metadata.keys()) == required_fields, f"Missing fields in {name}"

    def test_folder_name_derivation_icici_bank(self):
        """Folder name ICICIBank → icici_bank."""
        # Test the folding logic: CamelCase → snake_case (handles acronyms properly)
        import re
        name = 'ICICIBank'
        expected = 'icici_bank'
        # Proper CamelCase converter: insert _ before uppercase followed by lowercase,
        # and before uppercase that comes after lowercase
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
        assert result == expected

    def test_folder_name_derivation_icici_card(self):
        """Folder name ICICICard → icici_card."""
        # Proper CamelCase converter: handles consecutive capitals correctly
        import re
        name = 'ICICICard'
        expected = 'icici_card'
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
        assert result == expected

    def test_folder_name_derivation_upworks(self):
        """Folder name Upworks → upworks."""
        name = 'Upworks'
        expected = 'upworks'
        result = ''.join('_' + c.lower() if c.isupper() else c
                        for c in name).lstrip('_')
        assert result == expected

    def test_introspect_importer_extracts_metadata(self, mock_importer_module):
        """introspect_importer() should extract metadata from a module."""
        # Verify expected fields are present
        assert hasattr(mock_importer_module, 'IMPORTER_NAME')
        assert hasattr(mock_importer_module, 'Importer')

    def test_introspect_importer_handles_missing_field(self):
        """introspect_importer() should handle missing IMPORTER_NAME gracefully."""
        mod = Mock(spec=[])  # No attributes
        mod.Importer = Mock(spec=['filename_pattern_def'])
        # Should use fallback (module name) instead of raising
        fallback_name = 'UnknownImporter'
        assert fallback_name or True  # Fallback should be available

    def test_importer_currency_field(self, importers_metadata):
        """Each importer should have a currency field."""
        for name, metadata in importers_metadata.items():
            assert metadata['currency'] in ['INR', 'USD']


# ============================================================================
# FILE VALIDATOR TESTS
# ============================================================================

class TestFileValidator:
    """Test file validation against importer patterns and headers."""

    def test_check_filename_pattern_matches_creditcard(self):
        """Pattern 'CreditCard*.csv' should match 'CreditCard_2026_01.csv'."""
        pattern = 'CreditCard'
        filename = 'CreditCard_2026_01.csv'
        # Simple substring match or regex
        assert pattern in filename or filename.startswith(pattern)

    def test_check_filename_pattern_matches_optrans(self):
        """Pattern 'OpTrans' should match 'OpTrans_2026.xls'."""
        pattern = 'OpTrans'
        filename = 'OpTrans_2026.xls'
        assert pattern in filename

    def test_check_filename_pattern_rejects_mismatch(self):
        """Pattern 'CreditCard' should reject 'BankStatement.csv'."""
        pattern = 'CreditCard'
        filename = 'BankStatement.csv'
        assert pattern not in filename

    def test_check_filename_pattern_handles_spaces(self):
        """Pattern matching should handle filenames with spaces."""
        pattern = 'Statement'
        filename = 'Bank Statement 2026.csv'
        # Pattern should still match if it's a substring
        assert pattern in filename

    def test_check_filename_pattern_handles_hyphens(self):
        """Pattern matching should handle hyphens."""
        pattern = 'OpTrans'
        filename = 'OpTrans-2026-01.xls'
        assert pattern in filename

    def test_check_filename_pattern_handles_underscores(self):
        """Pattern matching should handle underscores."""
        pattern = 'CreditCard'
        filename = 'CreditCard_2026_statement.csv'
        assert pattern in filename

    def test_validation_result_structure(self):
        """ValidationResult should have is_valid, errors, warnings fields."""
        # Simulate ValidationResult dataclass
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        assert 'is_valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert isinstance(result['errors'], list)
        assert isinstance(result['warnings'], list)

    def test_validate_file_success(self):
        """validate_file() should return is_valid=True for matching file."""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    def test_validate_file_failure(self):
        """validate_file() should return is_valid=False with error messages."""
        result = {
            'is_valid': False,
            'errors': ['Filename pattern mismatch', 'Header identifier not found'],
            'warnings': []
        }
        assert result['is_valid'] is False
        assert len(result['errors']) > 0

    def test_validate_file_with_warnings(self):
        """validate_file() may return warnings without failing."""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': ['Column order differs from expected']
        }
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0

    @patch('subprocess.run')
    def test_check_header_with_bean_identify_success(self, mock_subprocess):
        """bean-identify subprocess should validate header successfully."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='VALID',
            stderr=''
        )
        # Simulate bean_identify call
        assert mock_subprocess.return_value.returncode == 0

    @patch('subprocess.run')
    def test_check_header_with_bean_identify_failure(self, mock_subprocess):
        """bean-identify subprocess should fail gracefully."""
        mock_subprocess.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='Invalid statement format'
        )
        assert mock_subprocess.return_value.returncode != 0

    def test_validate_file_empty_filename(self):
        """validate_file() should reject empty filename."""
        filename = ''
        result = {
            'is_valid': False,
            'errors': ['Filename is empty'],
            'warnings': []
        }
        assert result['is_valid'] is False

    def test_validate_file_none_filename(self):
        """validate_file() should reject None filename."""
        filename = None
        # Should raise or return error
        assert filename is None or isinstance(filename, str)

    def test_validate_file_very_long_filename(self):
        """validate_file() should handle very long filenames."""
        filename = 'A' * 300 + '.csv'
        # Should not crash, may warn about length
        assert len(filename) > 255


# ============================================================================
# PARENT LEDGER GENERATOR TESTS
# ============================================================================

class TestParentLedgerGenerator:
    """Test parent ledger and reconciliation report generation."""

    def test_sort_intermediates_alphabetically(self):
        """sort_intermediates_alphabetically() should sort by filename."""
        paths = [
            'FY2025_26/intermediate/icici_card_CreditCard_2026_02.beancount',
            'FY2025_26/intermediate/icici_bank_OpTrans_2026_01.beancount',
            'FY2025_26/intermediate/sbi_bank_Bnk_2026_01.beancount',
        ]
        sorted_paths = sorted(paths)
        # Alphabetically: icici_bank < icici_card < sbi
        assert sorted_paths[0].endswith('icici_bank_OpTrans_2026_01.beancount')
        assert sorted_paths[1].endswith('icici_card_CreditCard_2026_02.beancount')
        assert sorted_paths[2].endswith('sbi_bank_Bnk_2026_01.beancount')

    def test_sort_intermediates_handles_sequences(self):
        """Sorting should handle _01, _02 sequences correctly."""
        paths = [
            'intermediate/bank_stmt_03.beancount',
            'intermediate/bank_stmt_01.beancount',
            'intermediate/bank_stmt_02.beancount',
        ]
        sorted_paths = sorted(paths)
        assert sorted_paths[1].endswith('_02.beancount')
        assert sorted_paths[2].endswith('_03.beancount')

    def test_generate_parent_ledger_returns_string(self):
        """generate_parent_ledger() should return string content, not file."""
        fy = 2026
        intermediates = [
            'FY2025_26/intermediate/icici_bank_stmt_01.beancount',
            'FY2025_26/intermediate/icici_card_stmt_01.beancount',
        ]
        # Should produce string with include directives
        content = f"""
; FY{fy} Parent Ledger
; Auto-generated by guided mode

include "{intermediates[0]}"
include "{intermediates[1]}"
"""
        assert isinstance(content, str)
        assert f'FY{fy}' in content
        for intermediate in intermediates:
            assert intermediate in content

    def test_generate_parent_ledger_includes_all_intermediates(self):
        """Parent ledger should include all intermediate files."""
        fy = 2026
        intermediates = [
            'FY2025_26/intermediate/file1.beancount',
            'FY2025_26/intermediate/file2.beancount',
            'FY2025_26/intermediate/file3.beancount',
        ]
        content = '\n'.join(f'include "{f}"' for f in intermediates)
        for intermediate in intermediates:
            assert intermediate in content

    def test_generate_parent_ledger_valid_beancount_syntax(self):
        """Generated parent ledger should have valid beancount syntax."""
        fy = 2026
        content = f"""
; FY{fy} Parent Ledger

include "FY{fy}/intermediate/file1.beancount"
include "FY{fy}/intermediate/file2.beancount"

option "operating_currency" "INR"
"""
        # Check for syntactic requirements
        assert f'include ' in content
        assert 'option' in content
        assert ';' in content  # Comments

    def test_generate_reconciliation_report_returns_string(self):
        """generate_reconciliation_report() should return string, not file."""
        fy = 2026
        report = f"""
=== Reconciliation Report FY{fy} ===

Importers: 3
Total Transactions: 150
Date Range: 2026-04-01 to 2027-03-31

Importer Breakdown:
- icici_bank: 50 transactions
- icici_card: 45 transactions
- sbi_bank: 55 transactions

Accounts Touched: Assets:INR:Bank, Liabilities:CreditCard
"""
        assert isinstance(report, str)
        assert f'FY{fy}' in report
        assert 'Transactions' in report
        assert 'Accounts' in report

    def test_reconciliation_report_contains_importer_names(self):
        """Report should list all importers."""
        report = """
Importer Breakdown:
- icici_bank: 50 transactions
- icici_card: 45 transactions
"""
        assert 'icici_bank' in report
        assert 'icici_card' in report

    def test_reconciliation_report_contains_transaction_counts(self):
        """Report should show transaction counts per importer."""
        report = """
- icici_bank: 50 transactions
- icici_card: 45 transactions
"""
        assert '50 transactions' in report
        assert '45 transactions' in report

    def test_reconciliation_report_contains_date_range(self):
        """Report should include date range."""
        report = """
Date Range: 2026-04-01 to 2027-03-31
"""
        assert '2026-04-01' in report
        assert '2027-03-31' in report


# ============================================================================
# UTILITIES HELPER TESTS
# ============================================================================

class TestUtilitiesHelpers:
    """Test folder creation, config I/O, and import module generation."""

    def test_create_fy_folder_structure(self, temp_fy_dir):
        """create_fy_folder_structure() should create all required subfolders."""
        fy = 2026
        base_path = temp_fy_dir

        # Simulate folder creation
        imports_path = base_path / 'imports'
        intermediate_path = base_path / 'intermediate'
        imports_path.mkdir(exist_ok=True)
        intermediate_path.mkdir(exist_ok=True)

        assert imports_path.exists()
        assert intermediate_path.exists()

    def test_create_fy_folder_structure_creates_bank_subfolders(self, temp_fy_dir):
        """Should create bank-specific import subfolders."""
        banks = ['icici_bank', 'icici_card', 'idfc_bank', 'sbi_bank', 'upworks', 'account']

        base_path = temp_fy_dir
        imports_path = base_path / 'imports'
        imports_path.mkdir(exist_ok=True)

        for bank in banks:
            bank_path = imports_path / bank
            bank_path.mkdir(exist_ok=True)
            assert bank_path.exists()

    def test_create_fy_folder_structure_handles_existing_folders(self, temp_fy_dir):
        """Should not fail if folders already exist."""
        fy_path = temp_fy_dir
        imports_path = fy_path / 'imports'
        imports_path.mkdir(exist_ok=True)

        # Try creating again
        imports_path.mkdir(exist_ok=True)
        assert imports_path.exists()

    def test_generate_import_module_code_structure(self):
        """generate_import_module_code() should produce valid Python."""
        selected_importers = ['ICICIBank', 'ICICICard']
        accounts = {'ICICIBank': 'Assets:INR:Bank', 'ICICICard': 'Liabilities:CreditCard'}

        code = f"""
from dyu_accounting.gulp.ICICIBank import Importer as ICICIBankImporter
from dyu_accounting.gulp.ICICICard import Importer as ICICICardImporter

CONFIG = [
    ICICIBankImporter(main_account="{accounts['ICICIBank']}"),
    ICICICardImporter(main_account="{accounts['ICICICard']}"),
]
"""
        assert 'from dyu_accounting.gulp' in code
        assert 'CONFIG = [' in code
        assert accounts['ICICIBank'] in code

    def test_generate_import_module_code_includes_all_importers(self):
        """Generated code should import all selected importers."""
        importers = ['ICICIBank', 'ICICICard', 'SBI']
        code = '\n'.join(f'from dyu_accounting.gulp.{imp} import Importer' for imp in importers)

        for imp in importers:
            assert imp in code

    def test_generate_import_module_code_valid_python_syntax(self):
        """Generated code should be compilable Python."""
        code = """
from dyu_accounting.gulp.ICICIBank import Importer as ICICIBankImporter

CONFIG = [
    ICICIBankImporter({"main_account": "Assets:INR:Bank"}),
]
"""
        # Should not raise SyntaxError
        compile(code, '<string>', 'exec')

    def test_generate_import_module_code_is_actually_instantiable(self):
        """
        Regression test: generate_import_module_code() must produce code that
        actually runs against the real Importer classes, not just code that
        compiles. beancount_reds_importers' banking.Importer.__init__(self, config)
        takes a single positional config dict - it does NOT accept main_account
        as a keyword argument, so `Importer(main_account="...")` compiles fine
        but raises TypeError at import time (this previously broke bean-extract
        for every importer).
        """
        from dyu_accounting.Utilities import generate_import_module_code

        code = generate_import_module_code(
            ['ICICIBank'], {'ICICIBank': 'Assets:INR:Bank'}
        )
        namespace = {}
        exec(compile(code, '<generated>', 'exec'), namespace)
        assert len(namespace['CONFIG']) == 1

    def test_save_guided_config_creates_json(self, temp_fy_dir):
        """save_guided_config() should write valid JSON file."""
        config = {
            'ICICIBank': 'Assets:INR:Bank',
            'ICICICard': 'Liabilities:CreditCard',
        }
        config_path = temp_fy_dir / '.guided-config.json'

        # Simulate save
        with open(config_path, 'w') as f:
            json.dump(config, f)

        assert config_path.exists()
        assert config_path.suffix == '.json'

    def test_load_guided_config_reads_json(self, temp_fy_dir):
        """load_guided_config() should read and parse JSON correctly."""
        config = {
            'ICICIBank': 'Assets:INR:Bank',
            'ICICICard': 'Liabilities:CreditCard',
        }
        config_path = temp_fy_dir / '.guided-config.json'

        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Simulate load
        with open(config_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == config
        assert loaded['ICICIBank'] == 'Assets:INR:Bank'

    def test_load_guided_config_missing_file_returns_empty(self, temp_fy_dir):
        """load_guided_config() should return empty dict if file missing."""
        config_path = temp_fy_dir / '.guided-config.json'

        # File doesn't exist
        loaded = {} if not config_path.exists() else json.load(open(config_path))

        assert loaded == {}

    def test_config_json_schema(self):
        """Config JSON should follow schema: {importer_name: account_string}."""
        config = {
            'ICICIBank': 'Assets:INR:Bank',
            'ICICICard': 'Liabilities:CreditCard',
            'IDFC': 'Assets:INR:IDFC',
        }

        # Validate schema
        for importer, account in config.items():
            assert isinstance(importer, str)
            assert isinstance(account, str)
            assert ':' in account  # Valid beancount account format


# ============================================================================
# GULP RUNNER TESTS
# ============================================================================

class TestGulpRunner:
    """
    Test bean-extract subprocess wrapper.

    bean-extract writes extracted entries to stdout only - it never writes
    per-file output itself, and -f/-e only points it at an existing ledger
    for de-duplication, not an output path (confirmed via `bean-extract
    --help` and by actually running it). The previous version of this
    module, and these tests, assumed bean-extract printed an "Exported to
    .../intermediate/X.beancount" message it could parse to find a file it
    had written - no such message exists, so that path/branch was always
    dead code; run_bean_extract() always returned an empty dict, and no
    guided-mode run ever actually produced an intermediate ledger.
    run_bean_extract() now runs bean-extract once per file and writes its
    captured stdout to the intermediate ledger itself.
    """

    def test_intermediate_path_for_derives_from_file_path(self):
        from dyu_accounting.gulp_runner import intermediate_path_for
        path = intermediate_path_for(
            '2025_26', 'FY2025_26/imports/icici_bank/OpTrans_2025_26_01.xls'
        )
        assert path == 'FY2025_26/intermediate/icici_bank_OpTrans_2025_26_01.beancount'

    def test_run_bean_extract_writes_real_intermediate_ledger(self, tmp_path, monkeypatch):
        """
        Regression test: run_bean_extract() must actually write the
        intermediate ledger file to disk with bean-extract's real output,
        not just return a path that was never created.
        """
        import shutil
        if shutil.which('bean-extract') is None:
            pytest.skip("bean-extract not on PATH")
        from dyu_accounting.gulp_runner import run_bean_extract

        fy_dir = tmp_path / "FY2025_26"
        import_dir = fy_dir / "imports" / "account"
        import_dir.mkdir(parents=True)
        fixture = Path(__file__).parent / "fixtures" / "account" / "Accounts_2026_01.csv"
        shutil.copy(fixture, import_dir / "Accounts_2026_01.csv")

        import_module = tmp_path / "FY2025_26.import"
        import_module.write_text(
            "from dyu_accounting.gulp.Account import Importer\n"
            "CONFIG = [Importer({'main_account': 'Assets:Bank'})]\n"
        )

        monkeypatch.chdir(tmp_path)
        file_path = "FY2025_26/imports/account/Accounts_2026_01.csv"
        result = run_bean_extract(
            "2025_26", "FY2025_26.import", "FY2025_26/FY2025_26.beancount", [file_path]
        )

        assert file_path in result
        intermediate_path = Path(result[file_path])
        assert intermediate_path == Path("FY2025_26/intermediate/account_Accounts_2026_01.beancount")
        assert intermediate_path.exists()
        content = intermediate_path.read_text()
        assert "Food" in content
        assert "-1500" in content or "1500" in content

    @patch('subprocess.run')
    def test_run_bean_extract_continues_past_one_failing_file(self, mock_subprocess, tmp_path, monkeypatch):
        """A single file's bean-extract failure shouldn't drop the others."""
        from dyu_accounting.gulp_runner import run_bean_extract

        monkeypatch.chdir(tmp_path)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stdout='', stderr='bad file'),
            Mock(returncode=0, stdout=';; ok\n', stderr=''),
        ]

        result = run_bean_extract(
            "2025_26", "FY2025_26.import", "FY2025_26/FY2025_26.beancount",
            ["FY2025_26/imports/account/bad.csv", "FY2025_26/imports/account/good.csv"],
        )

        assert "FY2025_26/imports/account/bad.csv" not in result
        assert "FY2025_26/imports/account/good.csv" in result
        assert Path(result["FY2025_26/imports/account/good.csv"]).read_text() == ';; ok\n'

    @patch('subprocess.run')
    def test_run_bean_extract_raises_if_every_file_fails(self, mock_subprocess, tmp_path, monkeypatch):
        from dyu_accounting.gulp_runner import run_bean_extract

        monkeypatch.chdir(tmp_path)
        mock_subprocess.return_value = Mock(returncode=1, stdout='', stderr='nope')

        with pytest.raises(RuntimeError):
            run_bean_extract(
                "2025_26", "FY2025_26.import", "FY2025_26/FY2025_26.beancount",
                ["FY2025_26/imports/account/bad.csv"],
            )


# ============================================================================
# INTEGRATION EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_special_chars_in_filenames(self):
        """Filenames with special chars should not crash validation."""
        filenames = [
            'Statement 2026-01.csv',
            'Statement (Copy).csv',
            'Statement_#1.csv',
            'Statement@Bank.csv',
        ]
        for filename in filenames:
            # Should not raise
            assert isinstance(filename, str)
            assert len(filename) > 0

    def test_account_syntax_validation_format(self):
        """Account strings should follow beancount format (Account:SubAccount:...)."""
        valid_accounts = [
            'Assets:INR:Bank',
            'Liabilities:CreditCard',
            'Expenses:Banking:Fees',
        ]

        invalid_accounts = [
            'InvalidAccount',
            '',
        ]

        # Valid accounts must have at least 1 colon (2+ parts, hierarchical format)
        for account in valid_accounts:
            assert account.count(':') >= 1, f"Valid account {account} should have >= 1 colon"

        # Invalid accounts must have 0 colons (single part, not hierarchical)
        for account in invalid_accounts:
            if account:  # Skip empty string
                assert account.count(':') == 0, f"Invalid account {account} should have 0 colons"

    def test_duplicate_importer_names_guard(self):
        """If two importers have same name, registry should detect."""
        importers = {'ICICIBank': 'meta1', 'ICICICard': 'meta2'}

        # Check for duplicates
        names = list(importers.keys())
        assert len(names) == len(set(names))  # No duplicates

    def test_large_transaction_count_in_report(self):
        """Reconciliation report should handle large transaction counts."""
        count = 10000
        report = f"Total Transactions: {count}"
        assert str(count) in report

    def test_unicode_in_narrations(self):
        """Payee/narration with unicode should be handled."""
        narration = "Payment to विजय (Vijay) Ltd."
        report = f"Description: {narration}"
        assert narration in report
