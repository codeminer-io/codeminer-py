"""Shared test fixtures for mocking API responses."""

import json
from unittest.mock import MagicMock

import pytest


def make_mock_response(data, status_code=200):
    """Create a mock requests.Response with the given JSON data."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


@pytest.fixture
def success_response():
    """Standard successful API response with result, warnings, messages."""
    return {
        "result": [
            {"code": "J45", "description": "Asthma", "code_type": "icd10"},
            {"code": "J45.0", "description": "Predominantly allergic asthma", "code_type": "icd10"},
        ],
        "warnings": [["Warnings: 0"]],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture
def empty_response():
    """API response with empty result."""
    return {
        "result": [],
        "warnings": [["Warnings: 0"]],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture
def warning_response():
    """API response with warnings."""
    return {
        "result": [
            {"code": "E10", "description": "Type 1 diabetes mellitus", "code_type": "icd10"},
        ],
        "warnings": [
            ["Warnings: 1"],
            {
                "!": "The following codes were not found in the lookup table:",
                "*": "'ZZZZ'",
            },
        ],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture
def error_response():
    """API error response (422)."""
    return {
        "error": {
            "error_type": "codeminer_arg_validation_error",
            "error_message": {
                "x": "Code type 'foo' not found.",
                "i": "Available code types: 'icd10', 'sct'",
            },
        },
        "warnings": [["Warnings: 0"]],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture
def metadata_response():
    """Metadata response for a single type."""
    return {
        "result": [
            {"table_name": "icd10_lookup", "code_type": "icd10", "version": "2024"},
            {"table_name": "sct_lookup", "code_type": "sct", "version": "2024"},
        ],
        "warnings": [["Warnings: 0"]],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture
def health_response():
    """Health endpoint response."""
    return {
        "status": "ok",
        "service": "CodeMiner API",
        "version": "0.0.0.9001",
    }
