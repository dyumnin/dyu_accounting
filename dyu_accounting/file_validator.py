"""
File validation against importer patterns and headers.
"""

import os
import re
import zipfile
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
    3. Header identifier is present

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

    # Check header identifier
    if metadata.header_identifier:
        if not check_header_identifier(filepath, metadata):
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


def check_header_identifier(filepath: str, metadata: ImporterMetadata) -> bool:
    """
    Check whether the header identifier is present in the file.

    .xlsx files are zip containers with compressed XML, so their text is not
    recoverable by reading the raw bytes as UTF-8 - they're unzipped and the
    worksheet/shared-string XML parts are searched instead. Other formats
    (CSV, etc.) are searched as plain text.

    Args:
        filepath: Path to the file
        metadata: ImporterMetadata with header_identifier

    Returns:
        True if header identifier is found, False otherwise
    """
    if not metadata.header_identifier:
        return True  # No header check needed

    if zipfile.is_zipfile(filepath):
        return _check_header_in_xlsx(filepath, metadata.header_identifier)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return metadata.header_identifier in f.read()
    except Exception:
        return False


def _check_header_in_xlsx(filepath: str, header_identifier: str) -> bool:
    """Search an .xlsx file's worksheet and shared-string XML parts for a string."""
    try:
        with zipfile.ZipFile(filepath) as zf:
            parts = [
                name for name in zf.namelist()
                if name == 'xl/sharedStrings.xml' or name.startswith('xl/worksheets/')
            ]
            for name in parts:
                content = zf.read(name).decode('utf-8', errors='ignore')
                if header_identifier in content:
                    return True
    except (zipfile.BadZipFile, KeyError):
        return False
    return False
