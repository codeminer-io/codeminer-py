"""Tests for _config.py: config object, with_type, _resolve."""

import json
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from codeminer._config import config, with_type, _resolve, _unset, CodeMinerConfig
from codeminer import DESCRIPTION, CODES, CHILDREN, MAP


def _make_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


@pytest.fixture
def success_response():
    return {
        "result": [{"code": "J45", "description": "Asthma", "code_type": "icd10"}],
        "warnings": [["Warnings: 0"]],
        "messages": [["Messages: 0"]],
    }


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before each test."""
    config.reset()
    yield
    config.reset()


# ---------------------------------------------------------------------------
# _resolve
# ---------------------------------------------------------------------------


class TestResolve:
    def test_explicit_value_wins(self):
        config.type = "sct"
        assert _resolve("icd10", "type") == "icd10"

    def test_config_value_used_when_unset(self):
        config.type = "sct"
        assert _resolve(_unset, "type") == "sct"

    def test_default_used_when_both_unset(self):
        config.type = None
        assert _resolve(_unset, "type", "fallback") == "fallback"

    def test_none_when_all_unset(self):
        config.type = None
        assert _resolve(_unset, "type") is None

    def test_explicit_none_passes_through(self):
        config.type = "sct"
        assert _resolve(None, "type") is None


# ---------------------------------------------------------------------------
# CodeMinerConfig
# ---------------------------------------------------------------------------


class TestConfig:
    def test_defaults(self):
        assert config.type is None
        assert config.lookup_version == "latest"
        assert config.relationship_version == "latest"
        assert config.map_version == "latest"
        assert config.base_url is None

    def test_set_and_get(self):
        config.type = "icd10"
        assert config.type == "icd10"

    def test_reset(self):
        config.type = "icd10"
        config.base_url = "http://custom:9000"
        config.reset()
        assert config.type is None
        assert config.base_url is None

    def test_repr(self):
        r = repr(config)
        assert "CodeMinerConfig" in r
        assert "type=" in r


# ---------------------------------------------------------------------------
# with_type
# ---------------------------------------------------------------------------


class TestWithType:
    def test_sets_type_temporarily(self):
        config.type = "sct"
        with with_type("bnf"):
            assert config.type == "bnf"
        assert config.type == "sct"

    def test_restores_on_exception(self):
        config.type = "sct"
        with pytest.raises(ValueError):
            with with_type("bnf"):
                assert config.type == "bnf"
                raise ValueError("test")
        assert config.type == "sct"

    def test_nested(self):
        config.type = "sct"
        with with_type("icd10"):
            assert config.type == "icd10"
            with with_type("bnf"):
                assert config.type == "bnf"
            assert config.type == "icd10"
        assert config.type == "sct"


# ---------------------------------------------------------------------------
# Integration: config affects client functions
# ---------------------------------------------------------------------------


class TestConfigIntegration:
    def test_config_type_used_by_description(self, success_response):
        config.type = "icd10"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            DESCRIPTION("asthma")
            body = mock.call_args.kwargs["json"]
            assert body["type"] == "icd10"

    def test_explicit_type_overrides_config(self, success_response):
        config.type = "icd10"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            DESCRIPTION("asthma", type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["type"] == "sct"

    def test_with_type_affects_codes(self, success_response):
        config.type = "sct"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            with with_type("bnf"):
                CODES("0204")
            body = mock.call_args.kwargs["json"]
            assert body["type"] == "bnf"

    def test_config_type_used_as_map_to_type(self, success_response):
        config.type = "sct"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            MAP("J45", from_type="icd10")
            body = mock.call_args.kwargs["json"]
            assert body["to"] == "sct"
            assert body["from"] == "icd10"

    def test_config_lookup_version(self, success_response):
        config.lookup_version = "2024-01"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            CODES("J45", type="icd10")
            body = mock.call_args.kwargs["json"]
            assert body["lookup_version"] == "2024-01"

    def test_config_base_url(self, success_response):
        config.base_url = "http://custom:9000"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            DESCRIPTION("asthma", type="icd10")
            url = mock.call_args.args[0]
            assert url.startswith("http://custom:9000")

    def test_config_base_url_overridden_by_explicit(self, success_response):
        config.base_url = "http://custom:9000"
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock:
            DESCRIPTION("asthma", type="icd10", base_url="http://explicit:8000")
            url = mock.call_args.args[0]
            assert url.startswith("http://explicit:8000")
