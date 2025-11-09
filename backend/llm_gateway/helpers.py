"""
Helper utility functions for the LLM Gateway module.

This module provides utility functions for file operations, date/time handling,
API key masking, data formatting, and Excel export functionality.
"""

from datetime import timedelta
from io import BytesIO
from pathlib import Path
import re

import pandas as pd
from django.http import HttpResponse
from django.utils import timezone
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE


def read_prompt_template(template_filename):
    """
    Read a prompt template from a file.

    Opens and reads the contents of a prompt template file. Used for loading
    prompt templates that are stored as text files.

    Args:
        template_filename: Path to the template file to read

    Returns:
        str: The contents of the template file

    Raises:
        FileNotFoundError: If the template file does not exist
    """
    file_path = f"{template_filename}"
    try:
        with Path(file_path).open("r") as file_handle:
            return file_handle.read()
    except FileNotFoundError as exc:
        error_msg = f"Prompt template file not found: {file_path}"
        raise FileNotFoundError(error_msg) from exc


def get_today_date_range():
    """
    Calculate the start and end datetime for the current local day.

    Used for filtering records by today's date range, particularly for
    daily usage limit calculations. Returns the start of today (00:00:00)
    and the start of tomorrow (00:00:00) in the local timezone.

    Returns:
        tuple: A tuple containing (day_start, day_end) datetime objects
               in local timezone. day_end is exclusive (start of next day).
    """
    # Get current time in local timezone
    current_time = timezone.localtime(timezone.now())
    # Set to start of day (midnight)
    day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    # Calculate end of day (start of next day, exclusive)
    day_end = day_start + timedelta(days=1)

    return day_start, day_end


def mask_api_key(content: str) -> str:
    """
    Mask API keys in error messages and other content for security.

    Replaces API key patterns (e.g., 'sk-...') with a masked version
    to prevent accidental exposure of sensitive credentials in logs
    or error messages.

    Args:
        content: The string content that may contain API keys

    Returns:
        str: The content with API keys replaced by 'sk-[MASKED]'
    """
    # Pattern to match sk- followed by alphanumeric characters
    # This matches common API key formats like OpenAI keys
    api_key_pattern = r"(sk-[a-zA-Z0-9]+)"
    return re.sub(api_key_pattern, "sk-[MASKED]", str(content))


def format_datetime(datetime_obj: timezone.datetime) -> str:
    """
    Convert a datetime object to a formatted string in local timezone.

    Formats a datetime object for display purposes, converting it to
    the local timezone and formatting as a readable string.

    Args:
        datetime_obj: The datetime object to format (can be timezone-aware
                     or timezone-naive)

    Returns:
        str: Formatted datetime string in format "YYYY-MM-DD HH:MM:SS TZ"
    """
    # Convert to local timezone if timezone-aware
    local_dt = timezone.localtime(datetime_obj)
    # Format as readable string with timezone
    return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def illegal_char_remover(data):
    """
    Remove illegal characters from data that cannot be used in Excel cells.

    Excel has restrictions on certain control characters. This function
    removes characters that would cause issues when exporting to Excel.

    Args:
        data: The data to clean (string or other type)

    Returns:
        str or original type: Cleaned string if input was string,
                             otherwise returns data unchanged
    """
    if isinstance(data, str):
        # Remove characters that Excel cannot handle
        return ILLEGAL_CHARACTERS_RE.sub("", data)
    return data


def generate_excel_response(rows, filename):
    """
    Generate an Excel file response from a list of row dictionaries.

    Creates an Excel file from a list of dictionaries (where each dict
    represents a row with column headers as keys). The file is prepared
    as an HTTP response for download with a timestamped filename.

    Args:
        rows: List of dictionaries, each representing a row of data.
              Dictionary keys become column headers.
        filename: Base filename for the Excel file (without extension)

    Returns:
        HttpResponse: HTTP response containing the Excel file with
                     appropriate headers for file download
    """
    # Convert list of dicts to pandas DataFrame
    data_frame = pd.DataFrame(rows)
    # Remove illegal characters from all cells to prevent Excel errors
    data_frame = data_frame.applymap(illegal_char_remover)

    # Create Excel file in memory
    output_buffer = BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as excel_writer:
        # Write DataFrame to Excel without index column
        data_frame.to_excel(excel_writer, index=False)

    # Generate timestamped filename
    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{filename}_{timestamp}.xlsx"

    # Create HTTP response with Excel file
    http_response = HttpResponse(
        output_buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # Set Content-Disposition header to trigger file download
    http_response["Content-Disposition"] = f'attachment; filename="{output_filename}"'
    return http_response
