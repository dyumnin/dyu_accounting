"""
Main orchestrator for guided workflow state machine.

Implements the interactive guided mode for annual statement import workflow.
Handles: FY selection, folder creation, importer selection with pre-selection,
file validation with retry loops, bean-extract invocation, parent ledger generation,
and config persistence.
"""

import os
import json
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from dyu_accounting.importer_registry import discover_importers, ImporterMetadata
from dyu_accounting.file_validator import validate_file
from dyu_accounting.gulp_runner import run_bean_extract
from dyu_accounting.parent_ledger_generator import (
    generate_parent_ledger,
    generate_reconciliation_report
)
from dyu_accounting.Utilities import (
    create_fy_folder_structure,
    generate_import_module_code,
    save_guided_config,
    load_guided_config,
    parse_financial_year_input,
    extract_previous_fy
)


def async_guided_workflow(fy: Optional[str] = None, cwd: str = ".") -> None:
    """
    Main entry point for guided workflow.

    Orchestrates the entire workflow: FY selection → folder creation →
    importer selection → file validation → bean-extract → parent ledger generation.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26"), or None to prompt user
        cwd: Current working directory (for testing)
    """
    os.chdir(cwd)

    # Step 1: Ask for financial year
    if fy is None:
        fy = ask_financial_year()
    else:
        print(f"Using financial year: {fy}")

    print(f"\nPreparing guided import for FY {fy}...")

    # Step 2: Create folder structure
    create_folder_structure(fy)

    # Step 3: Discover available importers
    registry = discover_importers()
    if not registry:
        print("Error: No importers found in dyu_accounting.gulp")
        return

    print(f"\nFound {len(registry)} importers available")

    # Step 4: Select importers (with pre-selection from previous year)
    selected_importers = select_importers(fy, registry)
    if not selected_importers:
        print("No importers selected. Exiting.")
        return

    # Step 5: Load or prompt for account configuration
    accounts = load_previous_accounts(fy, registry)

    # Step 6: Validate files per importer (with retry loop)
    print("\nValidating files...")
    validated_files = {}
    for importer_name in selected_importers:
        files = validate_files_for_importer(importer_name, fy, registry)
        if files:
            validated_files[importer_name] = files

    if not validated_files:
        print("No valid files found. Exiting.")
        return

    # Step 7: Generate import module
    import_module_path = generate_import_module(fy, selected_importers, accounts, registry)

    # Step 8: Run extraction pipeline
    all_intermediate_paths = run_extraction_pipeline(
        fy, import_module_path, validated_files, accounts, registry
    )

    # Step 9: Generate parent ledger
    generate_and_save_parent_ledger(fy, all_intermediate_paths)

    # Step 10: Generate reconciliation report
    reconciliation_path = generate_and_save_reconciliation_report(fy, all_intermediate_paths)

    # Step 11: Save configuration for next year
    save_guided_config(fy, {
        importer: accounts.get(importer, '')
        for importer in selected_importers
    })

    print(f"\nGuided import complete!")
    print(f"  Parent ledger: FY{fy}/FY{fy}.beancount")
    print(f"  Reconciliation: {reconciliation_path}")


def ask_financial_year() -> str:
    """
    Prompt user for financial year in Indian FY format.

    Accepts three formats:
    - "2025-26" (hyphen-separated)
    - "2025_26" (underscore-separated)
    - "202526" (6-digit compact, no separator)

    All formats normalize to "YYYY_YY" (e.g., "2025_26").

    Returns:
        Financial year as string in "YYYY_YY" format (e.g., "2025_26")
    """
    while True:
        try:
            fy_input = input("\nEnter financial year (e.g., 2025-26, 2025_26, or 202526): ").strip()
            fy = parse_financial_year_input(fy_input)
            return fy
        except ValueError as e:
            print(f"Invalid input: {e}")


def create_folder_structure(fy: str) -> None:
    """
    Create FY folder structure if it doesn't exist.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
    """
    fy_dir = f"FY{fy}"
    if not os.path.exists(fy_dir):
        create_fy_folder_structure(fy)
        print(f"Created folder structure: {fy_dir}/")
    else:
        print(f"Using existing folder: {fy_dir}/")


def select_importers(fy: str, registry: Dict[str, ImporterMetadata]) -> List[str]:
    """
    Interactive importer selection with pre-selection from previous year.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        registry: Dictionary of ImporterMetadata

    Returns:
        List of selected importer names
    """
    # Try to load previous year's config
    previous_fy = extract_previous_fy(fy)
    previous_accounts = {}
    if previous_fy:
        previous_accounts = load_guided_config(previous_fy)

    selected = []

    if previous_accounts:
        print(f"\nImporters used in {previous_fy}:")
        for importer in previous_accounts.keys():
            if importer in registry:
                print(f"  - {registry[importer].friendly_name}")

        use_previous = input(f"\nUse same importers as {previous_fy}? (Y/n): ").strip().lower()
        if use_previous != 'n':
            return list(previous_accounts.keys())

    # Manual selection
    print("\nAvailable importers:")
    importer_list = sorted(registry.keys())
    for i, name in enumerate(importer_list, 1):
        print(f"  {i}. {registry[name].friendly_name}")

    while True:
        selection = input("\nEnter importer numbers to select (comma-separated, e.g., 1,3,5): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [importer_list[i] for i in indices if 0 <= i < len(importer_list)]
            if selected:
                break
            else:
                print("Invalid selection. Please try again.")
        except (ValueError, IndexError):
            print("Invalid input. Please enter comma-separated numbers.")

    print(f"\nSelected {len(selected)} importers")
    return selected


def load_previous_accounts(fy: str, registry: Dict[str, ImporterMetadata]) -> Dict[str, str]:
    """
    Load account configuration from previous year or prompt user.

    Args:
        fy: Current financial year string in "YYYY_YY" format (e.g., "2025_26")
        registry: Dictionary of ImporterMetadata

    Returns:
        Dictionary mapping importer name to account (e.g., {'ICICIBank': 'Assets:Bank'})
    """
    # Try loading from previous year
    previous_fy = extract_previous_fy(fy)
    previous_accounts = {}
    if previous_fy:
        previous_accounts = load_guided_config(previous_fy)
    if previous_accounts:
        return previous_accounts

    # Prompt for each importer
    accounts = {}
    # This will be filled in during validate_files_for_importer if needed
    return accounts


def validate_files_for_importer(
    importer_name: str,
    fy: str,
    registry: Dict[str, ImporterMetadata]
) -> List[str]:
    """
    Validate files for a specific importer with retry loop.

    Args:
        importer_name: Name of the importer
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        registry: Dictionary of ImporterMetadata

    Returns:
        List of validated file paths
    """
    metadata = registry[importer_name]
    import_dir = f"FY{fy}/imports/{metadata.folder_name}"

    print(f"\n{metadata.friendly_name}:")
    print(f"  Filename pattern: {metadata.filename_pattern}")
    print(f"  Format: CSV/XLS")
    print(f"  Place files in: {import_dir}/")
    print(f"  Sample header: {metadata.header_identifier}")

    validated = []

    while True:
        # List files in the directory
        files = []
        if os.path.exists(import_dir):
            files = [
                os.path.join(import_dir, f)
                for f in os.listdir(import_dir)
                if os.path.isfile(os.path.join(import_dir, f))
                and not f.startswith('.')
            ]

        if not files:
            ready = input(f"  Ready? Place files in {import_dir}/ then press Enter (or 's' to skip): ").strip().lower()
            if ready == 's':
                return validated
            continue

        # Validate files
        all_valid = True
        for filepath in files:
            result = validate_file(filepath, metadata)
            if result.is_valid:
                validated.append(filepath)
            else:
                all_valid = False
                print(f"\n  Validation failed for {os.path.basename(filepath)}:")
                for error in result.errors:
                    print(f"    - {error}")
                for warning in result.warnings:
                    print(f"    ⚠ {warning}")

        if all_valid:
            print(f"  ✓ All {len(validated)} files validated successfully")
            break
        else:
            retry = input(f"  Fix files and press Enter to retry (or 's' to skip): ").strip().lower()
            if retry == 's':
                return validated
            validated = []  # Clear and re-validate

    return validated


def generate_import_module(
    fy: str,
    selected_importers: List[str],
    accounts: Dict[str, str],
    registry: Dict[str, ImporterMetadata]
) -> str:
    """
    Generate .import module with CONFIG list.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        selected_importers: List of selected importer names
        accounts: Dictionary mapping importer to account
        registry: Dictionary of ImporterMetadata

    Returns:
        Path to generated .import module
    """
    import_module_code = generate_import_module_code(selected_importers, accounts, registry)

    import_path = f"FY{fy}.import"
    with open(import_path, 'w') as f:
        f.write(import_module_code)

    print(f"\nGenerated import module: {import_path}")
    return import_path


def run_extraction_pipeline(
    fy: str,
    import_module_path: str,
    validated_files: Dict[str, List[str]],
    accounts: Dict[str, str],
    registry: Dict[str, ImporterMetadata]
) -> List[str]:
    """
    Run bean-extract for all validated files.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        import_module_path: Path to .import module
        validated_files: Dictionary mapping importer name to file list
        accounts: Dictionary mapping importer to account
        registry: Dictionary of ImporterMetadata

    Returns:
        List of paths to generated intermediate ledgers
    """
    all_files = []
    importer_to_account = {}

    for importer_name, files in validated_files.items():
        all_files.extend(files)
        account = accounts.get(importer_name, '')
        if not account:
            # Prompt for account if not provided
            print(f"\nEnter account for {registry[importer_name].friendly_name}:")
            print(f"  Example: Assets:Bank:INR")
            account = input("  Account: ").strip()
        importer_to_account[importer_name] = account

    if not all_files:
        return []

    print(f"\nRunning bean-extract for {len(all_files)} files...")

    target_ledger = f"FY{fy}/FY{fy}.beancount"
    try:
        intermediate_map = run_bean_extract(
            fy,
            import_module_path,
            target_ledger,
            all_files
        )

        intermediate_paths = list(intermediate_map.values())
        print(f"✓ Generated {len(intermediate_paths)} intermediate ledgers")
        return intermediate_paths

    except RuntimeError as e:
        print(f"Error during extraction: {e}")
        return []


def generate_and_save_parent_ledger(fy: str, intermediate_paths: List[str]) -> None:
    """
    Generate and save parent ledger.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        intermediate_paths: List of intermediate ledger paths
    """
    if not intermediate_paths:
        return

    parent_content = generate_parent_ledger(fy, intermediate_paths)
    parent_path = f"FY{fy}/FY{fy}.beancount"

    # If target ledger already exists from bean-extract, append includes
    if os.path.exists(parent_path):
        with open(parent_path, 'a') as f:
            f.write('\n\n' + parent_content)
    else:
        with open(parent_path, 'w') as f:
            f.write(parent_content)

    print(f"Generated parent ledger: {parent_path}")


def generate_and_save_reconciliation_report(
    fy: str,
    intermediate_paths: List[str]
) -> str:
    """
    Generate and save reconciliation report.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        intermediate_paths: List of intermediate ledger paths

    Returns:
        Path to generated reconciliation report
    """
    if not intermediate_paths:
        return f"FY{fy}/reconciliation_FY{fy}.txt"

    report_content = generate_reconciliation_report(fy, intermediate_paths)
    report_path = f"FY{fy}/reconciliation_FY{fy}.txt"

    with open(report_path, 'w') as f:
        f.write(report_content)

    return report_path
