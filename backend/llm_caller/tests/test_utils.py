# ruff: noqa: PLR2004

from io import BytesIO

import pandas as pd
import pytest

from backend.llm_caller.utils import generate_excel_response

NUM_OF_ROWS = 2


@pytest.fixture
def sample_data():
    return [
        {"name": "John", "age": 30, "city": "New York"},
        {"name": "Alice", "age": 25, "city": "London"},
    ]


@pytest.fixture
def sample_data_with_special_characters():
    return [
        {"name": "John", "age": 30, "city": "Special: [\x08]"},
        {"name": "Alice", "age": 25, "city": "London"},
    ]


def test_generate_excel_response_content_type(sample_data):
    """Test if the response has correct content type"""
    response = generate_excel_response(sample_data, "test_file")
    expected_content_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response["Content-Type"] == expected_content_type


def test_generate_excel_response_filename(sample_data):
    """Test if the filename is correctly formatted"""
    response = generate_excel_response(sample_data, "test_file")
    content_disposition = response["Content-Disposition"]

    # Check if filename starts with test_file and ends with .xlsx
    assert 'filename="test_file_' in content_disposition
    assert content_disposition.endswith('.xlsx"')


def test_generate_excel_response_content(sample_data):
    """Test if the Excel file content is correct"""
    response = generate_excel_response(sample_data, "test_file")

    # Read the Excel content from response
    content = BytesIO(response.content)
    df_data = pd.read_excel(content)

    # Check if the DataFrame has correct data
    assert len(df_data) == NUM_OF_ROWS
    assert list(df_data.columns) == ["name", "age", "city"]
    assert df_data.iloc[0]["name"] == "John"
    assert df_data.iloc[1]["name"] == "Alice"
    assert df_data.iloc[0]["age"] == 30
    assert df_data.iloc[1]["age"] == 25


def test_special_characters_in_data(sample_data_with_special_characters):
    """Test if method can handle special characters in data"""

    response = generate_excel_response(sample_data_with_special_characters, "test_file")

    # Read the Excel content from response
    content = BytesIO(response.content)
    df_data = pd.read_excel(content)

    # Check if the DataFrame has correct data
    assert len(df_data) == NUM_OF_ROWS
    assert list(df_data.columns) == ["name", "age", "city"]
    assert df_data.iloc[0]["name"] == "John"
    assert df_data.iloc[0]["age"] == 30
    assert df_data.iloc[0]["city"] == "Special: []"
