"""Tests for ``config.col_filters``: the recipe-wide column-filter setting."""

import json
from unittest.mock import MagicMock, patch

import pytest

import codeminer
from codeminer import config, with_col_filters, with_type

# One minimal call per endpoint function that takes ``col_filters``. All use
# ``return_raw=True`` so the mocked response needs no particular shape.
CALLS = {
    "DESCRIPTION": lambda **kw: codeminer.DESCRIPTION("asthma", type="ICD-10", **kw),
    "CODES_LIKE": lambda **kw: codeminer.CODES_LIKE("^J45", type="ICD-10", **kw),
    "CODES": lambda **kw: codeminer.CODES("J45", type="ICD-10", **kw),
    "CHILDREN": lambda **kw: codeminer.CHILDREN("J45", type="ICD-10", **kw),
    "N_CHILDREN": lambda **kw: codeminer.N_CHILDREN("J45", type="ICD-10", **kw),
    "PARENTS": lambda **kw: codeminer.PARENTS("J45", type="ICD-10", **kw),
    "N_PARENTS": lambda **kw: codeminer.N_PARENTS("J45", type="ICD-10", **kw),
    "ATTRIBUTES_FOR": lambda **kw: codeminer.ATTRIBUTES_FOR("J45", type="ICD-10", **kw),
    "HAS_ATTRIBUTES": lambda **kw: codeminer.HAS_ATTRIBUTES("J45", type="ICD-10", **kw),
    "RELATIONSHIP_TYPES_FROM": lambda **kw: codeminer.RELATIONSHIP_TYPES_FROM(
        "J45", type="ICD-10", **kw
    ),
    "RELATIONSHIP_TYPES_TO": lambda **kw: codeminer.RELATIONSHIP_TYPES_TO(
        "J45", type="ICD-10", **kw
    ),
    "RELATIONSHIP_TYPES": lambda **kw: codeminer.RELATIONSHIP_TYPES(
        type="ICD-10", **kw
    ),
    "MAP": lambda **kw: codeminer.MAP(
        "J45", from_type="ICD-10", to_type="Read v3", **kw
    ),
    "get_relationship_tree": lambda **kw: codeminer.get_relationship_tree(
        "J45", type="ICD-10", **kw
    ),
}

ALL_EDGES = {"relationship": {"SNOMED CT": None}}

# The bodies the calls above sent before ``config.col_filters`` existed. With
# the config at its default they must still be sent unchanged.
GOLDEN_BODIES = {
    "DESCRIPTION": {
        "pattern": "asthma",
        "type": "ICD-10",
        "lookup_version": "latest",
        "ignore_case": True,
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "CODES_LIKE": {
        "pattern": "^J45",
        "type": "ICD-10",
        "lookup_version": "latest",
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "CODES": {
        "codes": ["J45"],
        "type": "ICD-10",
        "lookup_version": "latest",
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "CHILDREN": {
        "codes": ["J45"],
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "N_CHILDREN": {
        "codes": ["J45"],
        "depth": 1,
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "PARENTS": {
        "codes": ["J45"],
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "N_PARENTS": {
        "codes": ["J45"],
        "depth": 1,
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "ATTRIBUTES_FOR": {
        "codes": ["J45"],
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "relationship_types": None,
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "HAS_ATTRIBUTES": {
        "codes": ["J45"],
        "type": "ICD-10",
        "lookup_version": "latest",
        "relationship_version": "latest",
        "relationship_types": None,
        "preferred_description_only": True,
        "max_nodes": 20000,
        "col_filters": "default",
    },
    "RELATIONSHIP_TYPES_FROM": {
        "codes": ["J45"],
        "type": "ICD-10",
        "relationship_version": "latest",
        "lookup_version": "latest",
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "RELATIONSHIP_TYPES_TO": {
        "codes": ["J45"],
        "type": "ICD-10",
        "relationship_version": "latest",
        "lookup_version": "latest",
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "RELATIONSHIP_TYPES": {
        "pattern": None,
        "type": "ICD-10",
        "relationship_version": "latest",
        "lookup_version": "latest",
        "ignore_case": True,
        "preferred_description_only": True,
        "col_filters": "default",
    },
    "MAP": {
        "codes": ["J45"],
        "from": "ICD-10",
        "to": "Read v3",
        "map_version": "latest",
        "lookup_version": "latest",
        "col_filters": "default",
    },
    "get_relationship_tree": {
        "codes": ["J45"],
        "type": "ICD-10",
        "expand_to_descendants": True,
        "max_codes": 10000,
        "relationship_version": "latest",
        "lookup_version": "latest",
        "col_filters": "default",
        "preferred_description_only": True,
    },
}


def _make_response():
    data = {"result": [], "warnings": [["Warnings: 0"]], "messages": [["Messages: 0"]]}
    mock = MagicMock()
    mock.status_code = 200
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


@pytest.fixture(autouse=True)
def reset_config():
    config.reset()
    yield
    config.reset()


def _sent_body(name, **kwargs):
    with patch(
        "codeminer._helpers.requests.post", return_value=_make_response()
    ) as mock:
        CALLS[name](return_raw=True, **kwargs)
        return mock.call_args.kwargs["json"]


@pytest.mark.parametrize("name", list(CALLS))
class TestColFiltersConfig:
    def test_unset_config_sends_todays_body(self, name):
        body = _sent_body(name)
        assert body == GOLDEN_BODIES[name]
        assert body["col_filters"] == "default"

    def test_config_applies(self, name):
        config.col_filters = ALL_EDGES
        assert _sent_body(name)["col_filters"] == ALL_EDGES

    def test_explicit_argument_wins(self, name):
        config.col_filters = ALL_EDGES
        other = {"lookup": {"ICD-10": {"status": ["1"]}}}
        assert _sent_body(name, col_filters=other)["col_filters"] == other
        assert _sent_body(name, col_filters="default")["col_filters"] == "default"
        body = _sent_body(name, col_filters=None)
        assert "col_filters" in body and body["col_filters"] is None

    def test_none_config_turns_filtering_off(self, name):
        config.col_filters = None
        body = _sent_body(name)
        assert "col_filters" in body and body["col_filters"] is None

    def test_reset_restores_default(self, name):
        config.col_filters = ALL_EDGES
        config.reset()
        assert _sent_body(name)["col_filters"] == "default"


def test_default_is_the_string_default():
    assert config.col_filters == "default"


def test_with_type_leaves_col_filters_alone():
    config.col_filters = ALL_EDGES
    with with_type("BNF"):
        assert config.col_filters == ALL_EDGES
    assert config.col_filters == ALL_EDGES


def test_misspelt_attribute_is_an_error():
    with pytest.raises(AttributeError, match="colfilters"):
        config.colfilters = ALL_EDGES


# with_col_filters -----------------------------------------------------------


class TestWithColFilters:
    def test_applies_for_the_block_and_restores(self):
        assert _sent_body("CODES")["col_filters"] == "default"
        with with_col_filters(ALL_EDGES):
            assert _sent_body("CODES")["col_filters"] == ALL_EDGES
        assert _sent_body("CODES")["col_filters"] == "default"
        assert config.col_filters == "default"

    def test_none_turns_filtering_off(self):
        with with_col_filters(None):
            assert _sent_body("CODES")["col_filters"] is None
        assert config.col_filters == "default"

    def test_merges_by_table_key_over_config(self):
        config.col_filters = {"lookup": {"SNOMED CT": {"active_description": ["1"]}}}
        with with_col_filters(ALL_EDGES):
            assert config.col_filters == {
                "lookup": {"SNOMED CT": {"active_description": ["1"]}},
                "relationship": {"SNOMED CT": None},
            }
        assert config.col_filters == {
            "lookup": {"SNOMED CT": {"active_description": ["1"]}}
        }

    def test_inner_entry_replaces_the_table_not_the_type(self):
        config.col_filters = {"lookup": {"ICD-10": {"a": ["1"]}}}
        with with_col_filters({"lookup": {"SNOMED CT": None}}):
            assert config.col_filters == {
                "lookup": {"ICD-10": {"a": ["1"]}, "SNOMED CT": None}
            }

    def test_nested_blocks_stack(self):
        with with_col_filters(ALL_EDGES):
            with with_col_filters({"lookup": {"SNOMED CT": None}}):
                assert config.col_filters == {
                    "relationship": {"SNOMED CT": None},
                    "lookup": {"SNOMED CT": None},
                }
            assert config.col_filters == ALL_EDGES

    def test_block_inside_none_config_starts_from_nothing(self):
        config.col_filters = None
        with with_col_filters(ALL_EDGES):
            assert config.col_filters == ALL_EDGES
        assert config.col_filters is None

    def test_restores_on_exception(self):
        with pytest.raises(RuntimeError):
            with with_col_filters(ALL_EDGES):
                raise RuntimeError("boom")
        assert config.col_filters == "default"

    def test_does_not_mutate_the_caller_or_the_old_value(self):
        old = {"lookup": {"SNOMED CT": {"a": ["1"]}}}
        config.col_filters = old
        given = {"lookup": {"ICD-10": None}}
        with with_col_filters(given):
            pass
        assert old == {"lookup": {"SNOMED CT": {"a": ["1"]}}}
        assert given == {"lookup": {"ICD-10": None}}

    def test_rejects_non_dict(self):
        with pytest.raises(TypeError, match="col_filters must be a dict"):
            with with_col_filters("default"):
                pass
