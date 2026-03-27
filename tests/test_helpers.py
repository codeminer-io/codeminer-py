"""Tests for _helpers.py: _get_base_url, _collect_codes, _api_request."""

import json
import math
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from codeminer._helpers import _get_base_url, _collect_codes, _api_request, _serialize_body
from codeminer.exceptions import CodeMinerError


def _mock_response(data, status_code=200):
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


# ---------------------------------------------------------------------------
# _get_base_url
# ---------------------------------------------------------------------------


class TestGetBaseUrl:
    def test_explicit_url_takes_priority(self):
        assert _get_base_url("http://custom:9000") == "http://custom:9000"

    def test_strips_trailing_slash(self):
        assert _get_base_url("http://custom:9000/") == "http://custom:9000"

    def test_env_var_fallback(self, monkeypatch):
        monkeypatch.setenv("CODEMINER_BASE_URL", "http://env:8080")
        assert _get_base_url(None) == "http://env:8080"

    def test_default_fallback(self, monkeypatch):
        monkeypatch.delenv("CODEMINER_BASE_URL", raising=False)
        assert _get_base_url(None) == "http://127.0.0.1:8000"

    def test_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("CODEMINER_BASE_URL", "http://env:8080")
        assert _get_base_url("http://explicit:9000") == "http://explicit:9000"


# ---------------------------------------------------------------------------
# _collect_codes
# ---------------------------------------------------------------------------


class TestCollectCodes:
    def test_string_args(self):
        codes, inferred_type = _collect_codes("J45", "E11", type="icd10")
        assert codes == ["J45", "E11"]
        assert inferred_type is None

    def test_empty_input(self):
        codes, inferred_type = _collect_codes()
        assert codes == []
        assert inferred_type is None

    def test_dataframe_input(self):
        df = pd.DataFrame({
            "code": ["J45", "E11"],
            "code_type": ["icd10", "icd10"],
        })
        codes, inferred_type = _collect_codes(df)
        assert codes == ["J45", "E11"]
        assert inferred_type == "icd10"

    def test_dataframe_without_code_column_raises(self):
        df = pd.DataFrame({"name": ["foo"]})
        with pytest.raises(ValueError, match="'code' column"):
            _collect_codes(df)

    def test_dataframe_multiple_types_raises(self):
        df = pd.DataFrame({
            "code": ["J45", "12345"],
            "code_type": ["icd10", "sct"],
        })
        with pytest.raises(ValueError, match="multiple code types"):
            _collect_codes(df)

    def test_dataframe_type_conflict_raises(self):
        df = pd.DataFrame({
            "code": ["J45"],
            "code_type": ["icd10"],
        })
        with pytest.raises(ValueError, match="conflicts"):
            _collect_codes(df, type="sct")

    def test_dataframe_type_matches(self):
        df = pd.DataFrame({
            "code": ["J45"],
            "code_type": ["icd10"],
        })
        codes, inferred_type = _collect_codes(df, type="icd10")
        assert codes == ["J45"]
        assert inferred_type == "icd10"

    def test_non_string_arg_raises(self):
        with pytest.raises(TypeError, match="string code arguments"):
            _collect_codes("J45", 123)


# ---------------------------------------------------------------------------
# _serialize_body
# ---------------------------------------------------------------------------


class TestSerializeBody:
    def test_inf_becomes_string(self):
        result = _serialize_body({"depth": math.inf})
        assert result["depth"] == "Inf"

    def test_none_preserved(self):
        result = _serialize_body({"col_filters": None})
        assert result["col_filters"] is None

    def test_normal_values_unchanged(self):
        result = _serialize_body({"pattern": "asthma", "depth": 2})
        assert result == {"pattern": "asthma", "depth": 2}


# ---------------------------------------------------------------------------
# _api_request
# ---------------------------------------------------------------------------


class TestApiRequest:
    @patch("codeminer._helpers.requests.post")
    def test_post_with_body_params(self, mock_post, success_response):
        mock_post.return_value = _mock_response(success_response)
        result = _api_request(
            "/DESCRIPTION",
            body_params={"pattern": "asthma", "type": "icd10"},
        )
        mock_post.assert_called_once()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "code" in result.columns

    @patch("codeminer._helpers.requests.get")
    def test_get_with_query_params(self, mock_get, metadata_response):
        mock_get.return_value = _mock_response(metadata_response)
        result = _api_request(
            "/metadata",
            query_params={"type": "lookup"},
            return_raw=True,
        )
        mock_get.assert_called_once()
        assert isinstance(result, dict)

    @patch("codeminer._helpers.requests.post")
    def test_return_raw(self, mock_post, success_response):
        mock_post.return_value = _mock_response(success_response)
        result = _api_request(
            "/CODES",
            body_params={"codes": ["J45"]},
            return_raw=True,
        )
        assert isinstance(result, dict)
        assert "result" in result

    @patch("codeminer._helpers.requests.post")
    def test_http_error_with_structured_error(self, mock_post, error_response):
        mock_post.return_value = _mock_response(error_response, status_code=422)
        with pytest.raises(CodeMinerError) as exc_info:
            _api_request("/CODES", body_params={"codes": ["J45"], "type": "foo"})
        assert exc_info.value.error_type == "codeminer_arg_validation_error"

    @patch("codeminer._helpers.requests.post")
    def test_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.ConnectionError("Connection refused")
        with pytest.raises(CodeMinerError, match="Failed to connect"):
            _api_request("/CODES", body_params={"codes": ["J45"]})

    @patch("codeminer._helpers.requests.post")
    def test_inf_serialized_in_body(self, mock_post, success_response):
        mock_post.return_value = _mock_response(success_response)
        _api_request(
            "/N_CHILDREN",
            body_params={"codes": ["73211009"], "depth": math.inf},
        )
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["depth"] == "Inf"

    @patch("codeminer._helpers.requests.post")
    def test_empty_response(self, mock_post):
        mock = MagicMock()
        mock.status_code = 200
        mock.text = ""
        mock_post.return_value = mock
        result = _api_request("/CODES", body_params={"codes": []})
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
