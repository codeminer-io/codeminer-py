"""Tests for _client.py: all 14 public API functions."""

import json
import math
from unittest.mock import patch, call, MagicMock

import pandas as pd
import pytest

from codeminer import (
    DESCRIPTION,
    CODES_LIKE,
    CODES,
    CHILDREN,
    N_CHILDREN,
    PARENTS,
    N_PARENTS,
    ATTRIBUTES_FOR,
    HAS_ATTRIBUTES,
    RELATIONSHIP_TYPES,
    RELATIONSHIP_TYPES_FROM,
    RELATIONSHIP_TYPES_TO,
    MAP,
    check_api_connection,
    get_codeminer_metadata,
    get_relationship_tree,
)


def _make_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


# Helper to patch requests.post and return a standard success response
def _mock_post(success_response):
    return patch(
        "codeminer._helpers.requests.post",
        return_value=_make_response(success_response),
    )


def _mock_get(response_data):
    return patch(
        "codeminer._helpers.requests.get",
        return_value=_make_response(response_data),
    )


# ---------------------------------------------------------------------------
# Pattern-based functions
# ---------------------------------------------------------------------------


class TestDESCRIPTION:
    def test_sends_correct_endpoint_and_body(self, success_response):
        with _mock_post(success_response) as mock:
            DESCRIPTION("asthma", type="icd10")
            body = mock.call_args.kwargs["json"]
            assert mock.call_args.args[0].endswith("/DESCRIPTION")
            assert body["pattern"] == "asthma"
            assert body["type"] == "icd10"
            assert body["ignore_case"] is True
            assert body["lookup_version"] == "latest"

    def test_returns_dataframe(self, success_response):
        with _mock_post(success_response):
            result = DESCRIPTION("asthma", type="icd10")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2

    def test_return_raw(self, success_response):
        with _mock_post(success_response):
            result = DESCRIPTION("asthma", type="icd10", return_raw=True)
            assert isinstance(result, dict)


class TestCODES_LIKE:
    def test_sends_correct_body(self, success_response):
        with _mock_post(success_response) as mock:
            CODES_LIKE("^J45", type="icd10")
            body = mock.call_args.kwargs["json"]
            assert body["pattern"] == "^J45"
            assert "ignore_case" not in body


# ---------------------------------------------------------------------------
# Code-based functions
# ---------------------------------------------------------------------------


class TestCODES:
    def test_string_args(self, success_response):
        with _mock_post(success_response) as mock:
            CODES("J45", "E11", type="icd10")
            body = mock.call_args.kwargs["json"]
            assert body["codes"] == ["J45", "E11"]
            assert body["type"] == "icd10"

    def test_dataframe_input(self, success_response):
        df = pd.DataFrame({"code": ["J45"], "code_type": ["icd10"]})
        with _mock_post(success_response) as mock:
            CODES(df)
            body = mock.call_args.kwargs["json"]
            assert body["codes"] == ["J45"]
            assert body["type"] == "icd10"


class TestCHILDREN:
    def test_includes_relationship_version(self, success_response):
        with _mock_post(success_response) as mock:
            CHILDREN("73211009", type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["relationship_version"] == "latest"


class TestN_CHILDREN:
    def test_depth_parameter(self, success_response):
        with _mock_post(success_response) as mock:
            N_CHILDREN("73211009", depth=2, type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["depth"] == 2

    def test_inf_depth(self, success_response):
        with _mock_post(success_response) as mock:
            N_CHILDREN("73211009", depth=math.inf, type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["depth"] == "Inf"


class TestPARENTS:
    def test_sends_correct_endpoint(self, success_response):
        with _mock_post(success_response) as mock:
            PARENTS("73211009", type="sct")
            assert mock.call_args.args[0].endswith("/PARENTS")


class TestN_PARENTS:
    def test_inf_depth(self, success_response):
        with _mock_post(success_response) as mock:
            N_PARENTS("73211009", depth=math.inf, type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["depth"] == "Inf"


class TestATTRIBUTES_FOR:
    def test_relationship_types_as_list(self, success_response):
        with _mock_post(success_response) as mock:
            ATTRIBUTES_FOR("73211009", type="sct", relationship_types=["116680003"])
            body = mock.call_args.kwargs["json"]
            assert body["relationship_types"] == ["116680003"]

    def test_relationship_types_as_dataframe(self, success_response):
        rt_df = pd.DataFrame({"code": ["116680003", "363698007"]})
        with _mock_post(success_response) as mock:
            ATTRIBUTES_FOR("73211009", type="sct", relationship_types=rt_df)
            body = mock.call_args.kwargs["json"]
            assert body["relationship_types"] == ["116680003", "363698007"]


class TestHAS_ATTRIBUTES:
    def test_sends_correct_endpoint(self, success_response):
        with _mock_post(success_response) as mock:
            HAS_ATTRIBUTES("73211009", type="sct")
            assert mock.call_args.args[0].endswith("/HAS_ATTRIBUTES")


class TestRELATIONSHIP_TYPES_FROM:
    def test_includes_lookup_options(self, success_response):
        with _mock_post(success_response) as mock:
            RELATIONSHIP_TYPES_FROM("73211009", type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["lookup_version"] == "latest"
            assert body["preferred_description_only"] is True
            assert body["relationship_version"] == "latest"


class TestRELATIONSHIP_TYPES_TO:
    def test_sends_correct_endpoint(self, success_response):
        with _mock_post(success_response) as mock:
            RELATIONSHIP_TYPES_TO("73211009", type="sct")
            assert mock.call_args.args[0].endswith("/RELATIONSHIP_TYPES_TO")


class TestRELATIONSHIP_TYPES:
    def test_sends_pattern(self, success_response):
        with _mock_post(success_response) as mock:
            RELATIONSHIP_TYPES("finding site", type="sct")
            assert mock.call_args.args[0].endswith("/RELATIONSHIP_TYPES")
            body = mock.call_args.kwargs["json"]
            assert body["pattern"] == "finding site"
            assert body["ignore_case"] is True

    def test_pattern_is_optional(self, success_response):
        with _mock_post(success_response) as mock:
            RELATIONSHIP_TYPES(type="sct")
            assert mock.call_args.kwargs["json"]["pattern"] is None


class TestMaxNodes:
    @pytest.mark.parametrize(
        "func", [CHILDREN, N_CHILDREN, PARENTS, N_PARENTS, ATTRIBUTES_FOR, HAS_ATTRIBUTES]
    )
    def test_sent_to_server(self, func, success_response):
        with _mock_post(success_response) as mock:
            func("73211009", type="sct", max_nodes=50)
            assert mock.call_args.kwargs["json"]["max_nodes"] == 50


class TestGetRelationshipTree:
    TREE = {
        "result": {
            "nodes": [
                {"code": "E11", "term": "Diabetes", "in_input_set": True},
                {"code": "E110", "term": "With coma", "in_input_set": False},
            ],
            "edges": [{"parent": "E11", "child": "E110"}],
        }
    }

    def test_returns_nodes_and_edges(self):
        with _mock_post(self.TREE) as mock:
            tree = get_relationship_tree("E11", type="icd10")
            assert mock.call_args.args[0].endswith("/get_relationship_tree")
            assert mock.call_args.kwargs["json"]["codes"] == ["E11"]
            assert list(tree) == ["nodes", "edges"]
            assert tree["nodes"]["code"].tolist() == ["E11", "E110"]
            assert len(tree["edges"]) == 1

    def test_empty_edges(self):
        leaf = {"result": {"nodes": [{"code": "E110"}], "edges": []}}
        with _mock_post(leaf):
            tree = get_relationship_tree("E110", type="icd10")
            assert tree["edges"].empty

    def test_return_raw(self):
        with _mock_post(self.TREE):
            raw = get_relationship_tree("E11", type="icd10", return_raw=True)
            assert raw == self.TREE


class TestMAP:
    def test_from_type_maps_to_from_key(self, success_response):
        with _mock_post(success_response) as mock:
            MAP("J45", from_type="icd10", to_type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["from"] == "icd10"
            assert body["to"] == "sct"
            assert "from_type" not in body
            assert "to_type" not in body

    def test_includes_map_version(self, success_response):
        with _mock_post(success_response) as mock:
            MAP("J45", from_type="icd10", to_type="sct")
            body = mock.call_args.kwargs["json"]
            assert body["map_version"] == "latest"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


class TestCheckApiConnection:
    def test_returns_true_on_success(self, health_response):
        with _mock_get(health_response):
            assert check_api_connection() is True

    def test_returns_false_on_failure(self):
        import requests as req_lib
        with patch(
            "codeminer._client.requests.get",
            side_effect=req_lib.ConnectionError("refused"),
        ):
            assert check_api_connection() is False


class TestGetCodeminerMetadata:
    def test_single_type_returns_dataframe(self, metadata_response):
        with _mock_get(metadata_response):
            result = get_codeminer_metadata("lookup")
            assert isinstance(result, pd.DataFrame)

    def test_default_requests_all_types(self, metadata_response):
        with _mock_get(metadata_response) as mock:
            get_codeminer_metadata()
            params = mock.call_args.kwargs.get("params", mock.call_args[1].get("params", {}))
            assert params["type"] == "lookup,mapping,relationship"

    def test_return_raw(self, metadata_response):
        with _mock_get(metadata_response):
            result = get_codeminer_metadata(return_raw=True)
            assert isinstance(result, dict)
