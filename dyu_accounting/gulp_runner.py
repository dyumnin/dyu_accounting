"""
Subprocess wrapper for bean-extract CLI.

Handles invocation of bean-extract and writing its output to per-file
intermediate ledgers.
"""

import subprocess
import os
from typing import Dict, List


def run_bean_extract(
    fy: str,
    import_module_path: str,
    target_ledger_path: str,
    file_paths: List[str]
) -> Dict[str, str]:
    """
    Run bean-extract on each file and save its output to an intermediate ledger.

    bean-extract writes extracted entries to stdout only - it has no concept
    of writing per-file output itself, and -f/-e only points it at an
    existing ledger for de-duplication, not an output path. So this runs
    bean-extract once per file and captures+writes each file's stdout to its
    own FY{fy}/intermediate/{importer_folder}_{filename}.beancount, which is
    what generate_parent_ledger()/generate_reconciliation_report() expect to
    be able to `include` and load.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        import_module_path: Path to the .import module (e.g., FY2025_26.import)
        target_ledger_path: Existing ledger to pass to bean-extract for
            de-duplication (e.g., FY2025_26/FY2025_26.beancount); may not
            exist yet, which is fine - bean-extract just skips de-dup then.
        file_paths: List of input files to extract, each expected to live
            under FY{fy}/imports/{importer_folder}/...

    Returns:
        Dictionary mapping input file path to generated intermediate ledger path
        Example: {
            'FY2025_26/imports/icici_bank/OpTrans_2025_26_01.xls':
                'FY2025_26/intermediate/icici_bank_OpTrans_2025_26_01.beancount',
            ...
        }

    Raises:
        RuntimeError: If bean-extract command fails for every file, or isn't installed
    """
    if not file_paths:
        return {}

    intermediate_dir = f"FY{fy}/intermediate"
    os.makedirs(intermediate_dir, exist_ok=True)

    intermediate_map = {}
    errors = []

    for file_path in file_paths:
        cmd = ['bean-extract', import_module_path, '-f', target_ledger_path, file_path]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{file_path}: bean-extract timed out after 60 seconds")
            continue
        except FileNotFoundError:
            raise RuntimeError("bean-extract command not found. Install beancount package.")

        if result.returncode != 0:
            errors.append(f"{file_path}: {result.stderr or result.stdout or 'Unknown error'}")
            continue

        # bean-extract exits 0 and prints only its ";; -*- mode: beancount -*-"
        # banner (no "**** <file>" marker, no entries) when NO importer in the
        # config recognized the file at all - this is silent otherwise, so
        # flag it rather than writing a near-empty intermediate file unremarked.
        if '****' not in result.stdout:
            print(f"Warning: {file_path}: no importer recognized this file (empty extraction)")
        elif not _has_entries_after_marker(result.stdout):
            print(f"Warning: {file_path}: recognized but produced 0 transactions "
                  f"(possibly already in {target_ledger_path} from an earlier run)")

        intermediate_path = intermediate_path_for(fy, file_path)
        with open(intermediate_path, 'w') as f:
            f.write(result.stdout)
        intermediate_map[file_path] = intermediate_path

    if errors and not intermediate_map:
        raise RuntimeError("bean-extract failed for all files:\n" + "\n".join(errors))
    for err in errors:
        print(f"Warning: {err}")

    return intermediate_map


def _has_entries_after_marker(stdout: str) -> bool:
    """Whether any non-blank, non-comment content follows the '****' file marker."""
    after_marker = stdout.split('****', 1)[1] if '****' in stdout else stdout
    return any(
        line.strip() and not line.strip().startswith(';;')
        for line in after_marker.splitlines()[1:]  # skip the marker's own line (the filename)
    )


def intermediate_path_for(fy: str, file_path: str) -> str:
    """
    Derive the intermediate ledger path for one input file.

    Expects file_path to live under FY{fy}/imports/{importer_folder}/... and
    derives FY{fy}/intermediate/{importer_folder}_{filename_without_ext}.beancount.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        file_path: Path to the input file being extracted

    Returns:
        Path to the intermediate ledger this file's extraction should be
        written to
    """
    filename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(filename)[0]
    folder_name = os.path.basename(os.path.dirname(file_path))
    return f"FY{fy}/intermediate/{folder_name}_{filename_without_ext}.beancount"
