"""
Helper utility functions for the LLM Gateway module.

This module provides utility functions for file operations, date/time handling,
API key masking, data formatting, and Excel export functionality.
"""

from datetime import timedelta
from pathlib import Path
import re

from django.utils import timezone


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


def today_bounds_local():
    """
    Determine the datetime boundaries for the current local day.

    This helper computes the inclusive start (00:00:00) and exclusive end
    (00:00:00 of the next day) timestamps for the current date, adjusted
    to the active timezone. Useful for restricting queries to "today only"
    such as daily quota checks or usage statistics.

    Returns:
        tuple[datetime, datetime]: (start_of_day, next_day_start)
    """
    # Get current time in local timezone
    now_local = timezone.localtime(timezone.now())
    # Set to start of day (midnight)
    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    # Calculate end of day (start of next day, exclusive)
    next_day_start = start_of_day + timedelta(days=1)

    return start_of_day, next_day_start


def mask_api_key(content: str) -> str:
    """
    Mask API keys (e.g., OpenAI or Groq) in text for security.

    Detects and replaces API key patterns (like 'sk-...' or 'gsk_...')
    with masked placeholders to prevent accidental credential exposure
    in logs, console output, or error messages.

    Supported formats:
        - OpenAI: sk-xxxxxxxxxxxxxxxxxxxxxxxx
        - Groq:   gsk_xxxxxxxxxxxxxxxxxxxxxxxx

    Args:
        content (str): Text content that may contain API keys.

    Returns:
        str: Sanitized content with sensitive keys masked.
    """
    text = str(content)

    # Common API key patterns (OpenAI, Groq, etc.)
    key_patterns = [
        r"\bsk-[A-Za-z0-9]{10,}\b",   # OpenAI style
        r"\bgsk_[A-Za-z0-9]{10,}\b",  # Groq style
    ]

    for pattern in key_patterns:
        text = re.sub(pattern, lambda m: m.group(0)[:4] + "[MASKED]", text)

    return text
