from datetime import timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
from django.http import HttpResponse
from django.utils import timezone
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE


def read_prompt_template(template_filename):
    template_path = f"{template_filename}"
    try:
        with Path(template_path).open("r") as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f"Prompt template file not found: {template_path}"
        raise FileNotFoundError(msg) from e


def get_today_date_range():
    """
    Returns the start and end datetime for the current local day.

    Returns:
        tuple: (today_start, today_end) datetime objects in local timezone
    """
    now = timezone.localtime(timezone.now())
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    return today_start, today_end


def mask_api_key(content: str) -> str:
    """
    Masks API keys in error messages etc.
    Looks for patterns like 'sk-*' and replaces the it with 'sk-[MASKED]'
    """
    import re

    # Match sk- followed by any characters until a space, quote, or end of string
    pattern = r"(sk-[a-zA-Z0-9]+)"
    return re.sub(pattern, "sk-[MASKED]", str(content))


def format_datetime(datetime_obj: timezone.datetime) -> str:
    """
    Formats a datetime object to a string in the local timezone.
    """
    return timezone.localtime(datetime_obj).strftime("%Y-%m-%d %H:%M:%S %Z")


def illegal_char_remover(data):
    """Remove ILLEGAL CHARACTER."""
    if isinstance(data, str):
        return ILLEGAL_CHARACTERS_RE.sub("", data)
    return data


def generate_excel_response(rows, filename):
    """
    Generate an Excel response from a list of rows.
    """
    df_data = pd.DataFrame(rows)
    df_data = df_data.applymap(illegal_char_remover)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_data.to_excel(writer, index=False)

    now = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{now}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
