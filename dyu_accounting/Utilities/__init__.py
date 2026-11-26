import jinja2
from beancount.core import data
import re
import datetime
import os
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional


def format_money(value, places=2):
    """Jinja filter: render a beancount Amount (or anything with .number/
    .currency, e.g. an Inventory's get_currency_units() result) as "N.NN
    CUR", rounded to `places` decimals. Anything else (a blank string from
    a ternary with no match, a plain Decimal/number) passes through
    unchanged, since .number/.currency doesn't apply to it.
    """
    try:
        number = value.number
        currency = value.currency
    except AttributeError:
        return value
    quant = Decimal(1).scaleb(-places)
    return f"{number.quantize(quant, rounding=ROUND_HALF_UP)} {currency}"


def get_account_value(entries, account_name, start_date=None, end_date=None):
    """
    Returns:
        float: The sum of value of all postings to an account in a given timeframe.
    Args:
        entries: Beancount list of entries
        account_name (str): A pattern that matches the account name.
            This will select the account and sub accounts.
            If only account is required end pattern with $
        start_date (datetime.date): The date (inclusive) from which to search for entries.
            If None, from start of accounting.
        end_date (datetime.date): The date (inclusive) till which to search for entries.
            If None, till end of accounting.
    """
    e = entries
    if start_date is not None:
        e = [x for x in e if x.date >= start_date]
    if end_date is not None:
        e = [x for x in e if x.date <= start_date]
    transactions = [x for x in e if isinstance(x, data.Transaction)]
    postings = [x for x in transactions if x.postings]
    values = [
        x.units.number for x in postings if re.match(account_name, x.account)]
    return sum(values)


def get_fy(date):
    entry_year = date.year
    entry_month = date.month
    fy = entry_year-1 if entry_month < 4 else entry_year
    return fy


def get_year_end(date):
    entry_year = date.year
    entry_month = date.month
    fy = entry_year-1 if entry_month < 4 else entry_year

    return datetime.date(fy+1, 3, 31)


def get_quarter(date):
    entry_quarter = date.month//3
    entry_quarter = 'q4' if entry_quarter == 0 else 'q' + str(entry_quarter)
    return entry_quarter


def hoh(base, *keys):
    x = base
    for k in keys:
        if k not in x:
            x[k] = {}
        x = x[k]
    return base


def render_template(data):
    """
    Returns:
        str: The filename actually written under data['cfg']['outdir'] (its
            extension may differ from data['outfile'] - e.g. 'adoc' format
            swaps a '.html' outfile to '.adoc'). Callers that build an index/
            navigation page linking to this report must use this return
            value, not data['outfile'], or the link target won't match what
            was actually written to disk.
    """
    fmt = data['cfg'].get('format', 'html')
    if fmt == 'tex':
        tpl_path = os.path.join('templates', 'tex')
    elif fmt == 'md':
        tpl_path = os.path.join('templates', 'md')
    elif fmt == 'adoc':
        tpl_path = os.path.join('templates', 'adoc')
    elif fmt == 'html':
        tpl_path = os.path.join('templates', 'html')
    else:
        tpl_path = 'templates'
    templateEnv = jinja2.Environment(
        loader=jinja2.PackageLoader('dyu_accounting', tpl_path),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True)
    templateEnv.filters['money'] = format_money
    fname = data['template_name']
    template = templateEnv.get_template(fname)
    outputText = template.render(data)
    if fmt == 'tex':
        data['cfg']['texwriter'].write(outputText)
    filename = data['outfile']
    if fmt == 'adoc':
        filename = os.path.splitext(filename)[0] + '.adoc'
    with open(os.path.join(data['cfg']['outdir'], filename), "w") as fy_file:
        fy_file.write(outputText)
    return filename


# ============================================================================
# Guided Mode Helper Functions
# ============================================================================

def parse_financial_year_input(user_input: str) -> str:
    """
    Parse and normalize financial year input to "YYYY_YY" format.

    Accepts three input formats:
    - "2025-26" (hyphen-separated)
    - "2025_26" (underscore-separated, already normalized)
    - "202526" (6-digit compact, no separator)

    Validates:
    - Rejects single-year format ("2025")
    - Rejects non-consecutive years ("2025-27")
    - Rejects 2-digit years ("25-26")

    Args:
        user_input: User's financial year input string

    Returns:
        Normalized FY string in "YYYY_YY" format (e.g., "2025_26")

    Raises:
        ValueError: If input format is invalid
    """
    user_input = user_input.strip()

    # Handle hyphen format: "2025-26"
    if '-' in user_input:
        parts = user_input.split('-')
        if len(parts) != 2:
            raise ValueError("Invalid format. Use 'YYYY-YY' (e.g., 2025-26)")
        start, end = parts
        if len(start) != 4:
            raise ValueError("Use 4-digit years (e.g., 2025-26, not 25-26)")
        if len(end) != 2:
            raise ValueError("Invalid format. Use 'YYYY-YY' (e.g., 2025-26)")
        try:
            start_year = int(start)
            end_year = int(end)
            expected_end = (start_year + 1) % 100
            if end_year != expected_end:
                raise ValueError("Years must be consecutive (e.g., 2025-26)")
            return f"{start_year}_{end_year:02d}"
        except ValueError as e:
            if "consecutive" in str(e):
                raise
            raise ValueError("Invalid year values")

    # Handle underscore format: "2025_26" (already normalized)
    if '_' in user_input:
        parts = user_input.split('_')
        if len(parts) != 2:
            raise ValueError("Invalid format. Use 'YYYY_YY' (e.g., 2025_26)")
        start, end = parts
        if len(start) != 4:
            raise ValueError("Use 4-digit years (e.g., 2025_26)")
        if len(end) != 2:
            raise ValueError("Invalid format. Use 'YYYY_YY' (e.g., 2025_26)")
        try:
            start_year = int(start)
            end_year = int(end)
            expected_end = (start_year + 1) % 100
            if end_year != expected_end:
                raise ValueError("Years must be consecutive (e.g., 2025_26)")
            return f"{start_year}_{end_year:02d}"
        except ValueError as e:
            if "consecutive" in str(e):
                raise
            raise ValueError("Invalid year values")

    # Handle compact format: "202526" (6-digit, no separator)
    if len(user_input) == 6 and user_input.isdigit():
        try:
            start = user_input[:4]
            end = user_input[4:6]
            start_year = int(start)
            end_year = int(end)
            expected_end = (start_year + 1) % 100
            if end_year != expected_end:
                raise ValueError("Years must be consecutive (e.g., 202526)")
            return f"{start_year}_{end_year:02d}"
        except ValueError as e:
            if "consecutive" in str(e):
                raise
            raise ValueError("Invalid year values in compact format")

    # Reject single-year format
    if len(user_input) == 4 and user_input.isdigit():
        raise ValueError("Please provide full financial year range (e.g., 2025-26)")

    raise ValueError("Invalid format. Use one of: '2025-26', '2025_26', or '202526'")


def extract_previous_fy(fy_str: str) -> Optional[str]:
    """
    Extract previous financial year from current FY string.

    Calculates the previous FY by decrementing the start year.
    Example: "2025_26" → "2024_25"
    Edge cases handled: "2000_01" → "1999_00", "1901_02" → "1900_01"

    Args:
        fy_str: Current FY string in "YYYY_YY" format (e.g., "2025_26")

    Returns:
        Previous FY string in same format, or None if parsing fails
    """
    try:
        parts = fy_str.split('_')
        if len(parts) != 2:
            return None
        start_year = int(parts[0])
        prev_start = start_year - 1
        prev_end = start_year  # Previous FY ends when current FY starts
        return f"{prev_start}_{prev_end % 100:02d}"
    except (ValueError, AttributeError):
        return None


def create_fy_folder_structure(fy: str) -> None:
    """
    Create FY{year}/ folder structure with subdirectories.

    Creates:
        FY{year}/
        FY{year}/imports/
        FY{year}/imports/{bank}/  (for each of 6 importers)
        FY{year}/intermediate/

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
    """
    fy_dir = f"FY{fy}"
    os.makedirs(fy_dir, exist_ok=True)

    # Create imports folder
    imports_dir = os.path.join(fy_dir, "imports")
    os.makedirs(imports_dir, exist_ok=True)

    # Create bank-specific folders (for all 6 importers)
    banks = [
        'icici_bank',
        'icici_card',
        'idfc_bank',
        'sbi_bank',
        'upworks',
        'account'
    ]
    for bank in banks:
        bank_dir = os.path.join(imports_dir, bank)
        os.makedirs(bank_dir, exist_ok=True)

    # Create intermediate folder
    intermediate_dir = os.path.join(fy_dir, "intermediate")
    os.makedirs(intermediate_dir, exist_ok=True)


def generate_import_module_code(
    selected_importers: List[str],
    accounts: Dict[str, str],
    registry: Optional[Dict] = None
) -> str:
    """
    Generate Python code for FY{year}.import module.

    The module contains:
        from dyu_accounting.gulp.{Importer} import Importer as {Importer}Import
        CONFIG = [
            {Importer}Import({{"main_account": "{account}"}}),
            ...
        ]

    Args:
        selected_importers: List of selected importer names (e.g., ['ICICIBank', 'ICICICard'])
        accounts: Dictionary mapping importer name to account string
        registry: Optional ImporterMetadata registry (for validation)

    Returns:
        String containing the .import module code
    """
    lines = [
        "# Auto-generated import module for bean-extract",
        "# Do not edit manually",
        ""
    ]

    # Import statements
    for importer_name in selected_importers:
        lines.append(f"from dyu_accounting.gulp.{importer_name} import Importer as {importer_name}Import")

    lines.append("")
    lines.append("# CONFIG list for bean-extract")
    lines.append("CONFIG = [")

    for importer_name in selected_importers:
        account = accounts.get(importer_name, 'Assets:Bank')
        # beancount_reds_importers' banking.Importer.__init__(self, config) takes a
        # single positional config dict, not keyword arguments.
        lines.append(f'    {importer_name}Import({{"main_account": "{account}"}}),')

    lines.append("]")

    return '\n'.join(lines)


def save_guided_config(fy: str, config: Dict[str, str]) -> None:
    """
    Save importer configuration to FY{year}/.guided-config.json.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        config: Dictionary mapping importer name to account
                Example: {'ICICIBank': 'Assets:Bank:INR', 'SBI': 'Assets:Bank:SBI'}
    """
    fy_dir = f"FY{fy}"
    config_path = os.path.join(fy_dir, ".guided-config.json")

    os.makedirs(fy_dir, exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def load_guided_config(fy: str) -> Dict[str, str]:
    """
    Load importer configuration from FY{year}/.guided-config.json.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")

    Returns:
        Dictionary mapping importer name to account, or empty dict if file doesn't exist
    """
    fy_dir = f"FY{fy}"
    config_path = os.path.join(fy_dir, ".guided-config.json")

    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_selected_importers(fy: str, selected_importers: List[str]) -> None:
    """
    Save the chosen importer list to FY{year}/.guided-selection.json.

    Kept separate from .guided-config.json (which only gets a key per
    importer once its account has actually been answered) so that resuming
    a run interrupted mid-account-collection still knows the full original
    selection, not just whichever importers already got an answer.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")
        selected_importers: List of importer names selected for this FY
    """
    fy_dir = f"FY{fy}"
    selection_path = os.path.join(fy_dir, ".guided-selection.json")

    os.makedirs(fy_dir, exist_ok=True)

    with open(selection_path, 'w') as f:
        json.dump(selected_importers, f, indent=2)


def load_selected_importers(fy: str) -> List[str]:
    """
    Load the chosen importer list from FY{year}/.guided-selection.json.

    Args:
        fy: Financial year string in "YYYY_YY" format (e.g., "2025_26")

    Returns:
        List of importer names, or empty list if file doesn't exist
    """
    fy_dir = f"FY{fy}"
    selection_path = os.path.join(fy_dir, ".guided-selection.json")

    if not os.path.exists(selection_path):
        return []

    try:
        with open(selection_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
