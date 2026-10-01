"""
Subprocess wrapper for bean-extract CLI.

Handles invocation of bean-extract and parsing of intermediate ledger paths.
"""

import subprocess
import os
import re
from typing import Dict, List, Optional, Tuple


def run_bean_extract(
    fy: str,
    import_module_path: str,
    target_ledger_path: str,
    file_paths: List[str]
) -> Dict[str, str]:
    """
    Run bean-extract on a list of files.

    Invokes: bean-extract {import_module} -f {target_ledger} {files...}
    Captures stdout to map input files to generated intermediate ledger paths.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        import_module_path: Path to the .import module (e.g., FY2025_26.import)
        target_ledger_path: Path to output ledger (e.g., FY2025_26/FY2025_26.beancount)
        file_paths: List of input files to extract

    Returns:
        Dictionary mapping input file path to generated intermediate ledger path
        Example: {
            'FY2025_26/imports/icici_bank/OpTrans_2025_26_01.xls':
                'FY2025_26/intermediate/icici_bank_OpTrans_2025_26_01.beancount',
            ...
        }

    Raises:
        RuntimeError: If bean-extract command fails
    """
    if not file_paths:
        return {}

    # Build command: bean-extract FY2026.import -f FY2026/FY2026.beancount file1 file2 ...
    cmd = [
        'bean-extract',
        import_module_path,
        '-f', target_ledger_path
    ] + file_paths

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            raise RuntimeError(f"bean-extract failed: {error_msg}")

        # Parse output to extract intermediate ledger mappings
        intermediate_map = {}
        for file_path in file_paths:
            intermediate_path = extract_intermediate_path(result.stdout, file_path)
            if intermediate_path:
                intermediate_map[file_path] = intermediate_path

        return intermediate_map

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"bean-extract timed out after 60 seconds")
    except FileNotFoundError:
        raise RuntimeError("bean-extract command not found. Install beancount package.")


def extract_intermediate_path(
    bean_extract_stdout: str,
    file_path: str
) -> Optional[str]:
    """
    Parse bean-extract output to find the intermediate ledger path.

    bean-extract creates intermediate ledgers with predictable naming.
    Example output contains paths like:
        "Exported to FY2026/intermediate/icici_bank_OpTrans_2026_01.beancount"

    Args:
        bean_extract_stdout: stdout from bean-extract command
        file_path: Original input file path

    Returns:
        Path to generated intermediate ledger, or None if not found
    """
    if not bean_extract_stdout:
        return None

    filename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(filename)[0]

    # Look for patterns in stdout that indicate intermediate ledger path
    # Pattern: "intermediate/{importer}_{filename}_{seq}.beancount"
    patterns = [
        # Standard pattern: "Exported to FY2026/intermediate/..."
        rf'Exported to .*intermediate[/\\].*\.beancount',
        # Alternative: just the filename
        rf'{re.escape(filename_without_ext)}[^"]*\.beancount',
    ]

    for pattern in patterns:
        match = re.search(pattern, bean_extract_stdout, re.IGNORECASE)
        if match:
            path = match.group(0)
            # Clean up "Exported to " prefix if present
            if path.startswith('Exported to '):
                path = path[len('Exported to '):]
            return path.strip()

    # If no pattern matches, try to infer from standard naming convention
    # intermediate/{importer}_{original_filename}.beancount
    if 'intermediate/' in file_path or 'intermediate\\' in file_path:
        # Extract directory from file_path (match new format: FY2025_26)
        fy_match = re.search(r'(FY\d+_\d+)', file_path)
        if fy_match:
            fy_dir = fy_match.group(1)
            # Derive importer from folder name
            importer_match = re.search(rf'{fy_dir}/imports/([^/\\]+)/', file_path)
            if importer_match:
                importer = importer_match.group(1)
                return f"{fy_dir}/intermediate/{importer}_{filename_without_ext}.beancount"

    return None
