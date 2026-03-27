"""Tests for _conditions.py: condition formatting and display."""

import pytest

from codeminer._conditions import _format_condition, _raise_api_error
from codeminer.exceptions import CodeMinerError


class TestFormatCondition:
    def test_error_bullet(self):
        lines = _format_condition({"x": "Something failed"})
        assert len(lines) == 1
        assert "✖" in lines[0]
        assert "Something failed" in lines[0]

    def test_warning_bullet(self):
        lines = _format_condition({"!": "Watch out"})
        assert "!" in lines[0]

    def test_info_bullet(self):
        lines = _format_condition({"i": "Hint text"})
        assert "ℹ" in lines[0]

    def test_multiple_bullets(self):
        lines = _format_condition({
            "x": "Error message",
            "i": "Some info",
            "*": "A bullet",
        })
        assert len(lines) == 3

    def test_unknown_bullet_type(self):
        lines = _format_condition({"?": "Unknown"})
        assert "Unknown" in lines[0]


class TestRaiseApiError:
    def test_raises_codeminer_error(self):
        parsed = {
            "error_type": "codeminer_arg_validation_error",
            "error_message": {"x": "Bad input", "i": "Try again"},
        }
        with pytest.raises(CodeMinerError) as exc_info:
            _raise_api_error(parsed, 422)
        assert exc_info.value.error_type == "codeminer_arg_validation_error"

    def test_preserves_error_message(self):
        parsed = {
            "error_type": "test_error",
            "error_message": {"x": "msg"},
        }
        with pytest.raises(CodeMinerError) as exc_info:
            _raise_api_error(parsed, 422)
        assert exc_info.value.error_message == {"x": "msg"}

    def test_string_error_message(self):
        parsed = {
            "error_type": "Backend Error",
            "error_message": "Something went wrong",
        }
        with pytest.raises(CodeMinerError):
            _raise_api_error(parsed, 500)
