"""
Dynamic discovery and metadata extraction of importers from dyu_accounting.gulp.

Provides functions to discover all available importers and extract their metadata.
"""

import importlib
import pkgutil
import re
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ImporterMetadata:
    """Metadata extracted from an importer module."""
    name: str  # e.g., 'ICICIBank'
    importer_class: type  # The Importer class
    friendly_name: str  # e.g., 'ICICI Bank Account'
    filename_pattern: str  # e.g., 'OpTrans'
    header_identifier: str  # e.g., 'DETAILED STATEMENT'
    column_labels: str  # e.g., 'S No.,Value Date,...'
    currency: str  # e.g., 'INR'
    folder_name: str  # e.g., 'icici_bank'


# camel_to_snake() can't split all-caps module names (e.g. 'IDFC', 'SBI') into
# multiple words, so it produces folder names that don't match the fixed bank
# folders create_fy_folder_structure() actually creates. Override those here.
FOLDER_NAME_OVERRIDES = {
    'IDFC': 'idfc_bank',
    'SBI': 'sbi_bank',
}


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    # Insert underscore before uppercase letters preceded by lowercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before uppercase letters preceded by lowercase or digit
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def discover_importers() -> Dict[str, ImporterMetadata]:
    """
    Dynamically discover all importers in dyu_accounting.gulp.

    Returns:
        Dictionary mapping importer name to ImporterMetadata
        Example: {'ICICIBank': ImporterMetadata(...), 'SBI': ImporterMetadata(...)}
    """
    importers = {}

    # Iterate through all modules in dyu_accounting.gulp
    gulp_package = importlib.import_module('dyu_accounting.gulp')

    for importer, module_name, is_pkg in pkgutil.iter_modules(gulp_package.__path__):
        if is_pkg or module_name.startswith('_'):
            continue

        try:
            # Import the module
            module = importlib.import_module(f'dyu_accounting.gulp.{module_name}')

            # Extract metadata
            if hasattr(module, 'Importer'):
                metadata = introspect_importer(module_name, module)
                if metadata:
                    importers[module_name] = metadata
        except Exception:
            # Skip modules that fail to import or lack required attributes
            pass

    return importers


def introspect_importer(module_name: str, module) -> Optional[ImporterMetadata]:
    """
    Extract metadata from a single importer module.

    Args:
        module_name: Name of the module (e.g., 'ICICIBank')
        module: The imported module object

    Returns:
        ImporterMetadata or None if required attributes are missing
    """
    importer_class = getattr(module, 'Importer', None)
    if not importer_class:
        return None

    # Create a dummy instance to extract custom_init() attributes
    try:
        # Create instance without calling __init__
        instance = object.__new__(importer_class)
        # Call custom_init to populate attributes
        if hasattr(instance, 'custom_init'):
            instance.custom_init()
    except Exception:
        instance = importer_class()

    # Extract metadata with fallbacks
    friendly_name = getattr(importer_class, 'IMPORTER_NAME', module_name)
    filename_pattern = getattr(instance, 'filename_pattern_def', module_name)
    header_identifier = getattr(instance, 'header_identifier', '')
    column_labels = getattr(instance, 'column_labels_line', '')
    currency = getattr(instance, 'currency', 'INR')
    folder_name = FOLDER_NAME_OVERRIDES.get(module_name, camel_to_snake(module_name))

    return ImporterMetadata(
        name=module_name,
        importer_class=importer_class,
        friendly_name=friendly_name,
        filename_pattern=filename_pattern,
        header_identifier=header_identifier,
        column_labels=column_labels,
        currency=currency,
        folder_name=folder_name
    )
