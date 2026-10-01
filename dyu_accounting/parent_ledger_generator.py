"""
Parent ledger and reconciliation report generation.

Generates the parent FY{year}.beancount that includes all intermediate ledgers,
and creates a reconciliation report summarizing the import.
"""

import os
import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from beancount import loader
from beancount.core import data


def generate_parent_ledger(fy: str, intermediate_paths: List[str]) -> str:
    """
    Generate content for parent FY{year}.beancount file.

    Creates a ledger that includes all intermediate ledgers in chronological order.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        intermediate_paths: List of paths to intermediate ledgers

    Returns:
        String containing beancount ledger content (not written to file)
        Example:
            ;; FY 2025_26 Parent Ledger
            ;; Automatically generated - do not edit
            include "intermediate/icici_bank_OpTrans_2025_26_01.beancount"
            include "intermediate/icici_bank_OpTrans_2025_26_02.beancount"
            ...
    """
    # Sort intermediate paths alphabetically
    sorted_paths = sort_intermediates_alphabetically(intermediate_paths)

    # Build ledger content
    lines = [
        f";; FY {fy} Parent Ledger",
        ";; Automatically generated - do not edit",
        "",
    ]

    for path in sorted_paths:
        # Normalize path to use forward slashes
        normalized_path = path.replace('\\', '/')
        lines.append(f'include "{normalized_path}"')

    return '\n'.join(lines)


def sort_intermediates_alphabetically(paths: List[str]) -> List[str]:
    """
    Sort intermediate ledger paths alphabetically by filename.

    This ensures deterministic ordering regardless of import order.

    Args:
        paths: List of intermediate ledger paths

    Returns:
        Sorted list of paths
    """
    # Extract just the filename for sorting, but return full paths
    def get_filename(path: str) -> str:
        return os.path.basename(path)

    return sorted(paths, key=get_filename)


def generate_reconciliation_report(
    fy: str,
    intermediate_paths: List[str]
) -> str:
    """
    Generate a reconciliation report summarizing the import.

    Parses all intermediate ledgers to compute:
    - Total transactions per importer
    - Date range (earliest to latest transaction)
    - Accounts touched
    - Summary statistics

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        intermediate_paths: List of paths to intermediate ledgers

    Returns:
        String containing the reconciliation report
    """
    lines = [
        f"Reconciliation Report for FY {fy}",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Aggregate stats
    total_transactions = 0
    all_accounts = set()
    importer_stats = {}  # {importer: {tx_count, date_min, date_max, accounts}}

    # Parse each intermediate ledger
    for path in intermediate_paths:
        if not os.path.exists(path):
            continue

        try:
            entries, errors, options = loader.load_file(path)

            # Extract importer name from filename
            filename = os.path.basename(path)
            importer_match = re.match(r'([^_]+)_', filename)
            importer = importer_match.group(1) if importer_match else 'unknown'

            # Count transactions and collect metadata
            transactions = [e for e in entries if isinstance(e, data.Transaction)]
            tx_count = len(transactions)
            total_transactions += tx_count

            # Extract date range
            dates = [t.date for t in transactions if t.date]
            date_min = min(dates) if dates else None
            date_max = max(dates) if dates else None

            # Extract accounts
            accounts = set()
            for tx in transactions:
                for posting in tx.postings:
                    accounts.add(posting.account)
            all_accounts.update(accounts)

            # Store stats
            if importer not in importer_stats:
                importer_stats[importer] = {
                    'tx_count': 0,
                    'date_min': date_min,
                    'date_max': date_max,
                    'accounts': set()
                }

            importer_stats[importer]['tx_count'] += tx_count
            if date_min and (importer_stats[importer]['date_min'] is None or
                           date_min < importer_stats[importer]['date_min']):
                importer_stats[importer]['date_min'] = date_min
            if date_max and (importer_stats[importer]['date_max'] is None or
                           date_max > importer_stats[importer]['date_max']):
                importer_stats[importer]['date_max'] = date_max
            importer_stats[importer]['accounts'].update(accounts)

        except Exception as e:
            lines.append(f"Error reading {path}: {e}")

    # Format report
    lines.append(f"Total Transactions: {total_transactions}")
    lines.append(f"Total Accounts Touched: {len(all_accounts)}")
    lines.append("")

    lines.append("By Importer:")
    lines.append("-" * 50)
    for importer, stats in sorted(importer_stats.items()):
        lines.append(f"\n{importer}:")
        lines.append(f"  Transactions: {stats['tx_count']}")
        if stats['date_min']:
            lines.append(f"  Date Range: {stats['date_min']} to {stats['date_max']}")
        lines.append(f"  Accounts: {len(stats['accounts'])}")

    lines.append("")
    lines.append("All Accounts Touched:")
    lines.append("-" * 50)
    for account in sorted(all_accounts):
        lines.append(f"  {account}")

    return '\n'.join(lines)
