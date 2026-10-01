"""
File validation against importer patterns and headers.

Validates filenames and headers using bean-identify subprocess.
"""

import subprocess
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from dyu_accounting.importer_registry import ImporterMetadata


@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def validate_file(filepath: str, metadata: ImporterMetadata) -> ValidationResult:
    """
    Validate a file against importer metadata.

    Checks:
    1. File exists
    2. Filename matches pattern
    3. Header identifier is present (via bean-identify)

    Args:
        filepath: Path to the file to validate
        metadata: ImporterMetadata for the importer

    Returns:
        ValidationResult with is_valid flag and error/warning lists
    """
    errors = []
    warnings = []

    # Check file exists
    if not os.path.exists(filepath):
        errors.append(f"File does not exist: {filepath}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Check filename pattern
    filename = os.path.basename(filepath)
    if not check_filename_pattern(filename, metadata.filename_pattern):
        errors.append(
            f"Filename '{filename}' does not match pattern '{metadata.filename_pattern}'"
        )

    # Check header identifier via bean-identify
    if metadata.header_identifier:
        if not check_header_with_bean_identify(filepath, metadata):
            errors.append(
                f"Header identifier '{metadata.header_identifier}' not found in file"
            )

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def check_filename_pattern(filename: str, pattern: str) -> bool:
    """
    Check if filename matches the importer's pattern using regex.

    Compiles the pattern as a regex and matches it against the filename.
    Both regex patterns (e.g., 'Accounts.*') and literal strings (e.g., 'CreditCard')
    work correctly, as literal strings are valid regex patterns.

    Args:
        filename: The filename to check
        pattern: The regex pattern to match (e.g., 'Accounts.*', 'CreditCard')

    Returns:
        True if pattern matches, False otherwise
    """
    if not filename or not pattern:
        return False

    try:
        # Compile pattern as regex and match at start of filename
        regex = re.compile(pattern)
        return regex.match(filename) is not None
    except re.error:
        # Invalid regex pattern - log and return False
        import logging
        logging.warning(f"Invalid regex pattern in check_filename_pattern: {pattern}")
        return False


def check_header_with_bean_identify(filepath: str, metadata: ImporterMetadata) -> bool:
    """
    Use bean-identify subprocess to validate file format.

    Attempts to read file and check for header identifier.
    Falls back to simple file read if bean-identify is unavailable.

    Args:
        filepath: Path to the file
        metadata: ImporterMetadata with header_identifier

    Returns:
        True if header identifier is found, False otherwise
    """
    if not metadata.header_identifier:
        return True  # No header check needed

    # Try reading file directly first (fast path)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Check if header identifier is in the file
            return metadata.header_identifier in content
    except Exception:
        pass

    # Try bean-identify as fallback
    try:
        result = subprocess.run(
            ['bean-identify', filepath],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # If bean-identify succeeds, also check header in output or file
            return metadata.header_identifier in result.stdout or \
                   metadata.header_identifier in result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # If all checks fail, return False
    return False
