"""Checks against a live CodeMiner API with a SNOMED CT database.

Set ``CODEMINER_LIVE_API_URL`` (for example ``http://localhost:8001``) to run
these; they are skipped otherwise, so CI is unaffected.
"""

import os

import pytest

import codeminer
from codeminer import config

pytestmark = pytest.mark.integration

LIVE_URL = os.environ.get("CODEMINER_LIVE_API_URL", "")
ALL_EDGES = {"relationship": {"SNOMED CT": None}}


@pytest.fixture(autouse=True)
def live_config():
    if not LIVE_URL:
        pytest.skip("CODEMINER_LIVE_API_URL not set")
    config.reset()
    config.base_url = LIVE_URL
    yield
    config.reset()


def _warfarin(**kwargs):
    # Warfarin (substance), with the ingredient relationship types
    return codeminer.HAS_ATTRIBUTES(
        "372756006",
        type="SNOMED CT",
        relationship_types=["127489000", "762949000", "10362801000001104"],
        **kwargs,
    )


def test_config_col_filters_applies_to_every_query():
    default = _warfarin()
    explicit = _warfarin(col_filters=ALL_EDGES)

    config.col_filters = ALL_EDGES
    via_config = _warfarin()
    explicit_default = _warfarin(col_filters="default")

    # Row order varies between calls, so compare sets of codes
    assert set(via_config["code"]) == set(explicit["code"])
    assert len(via_config) == len(explicit)
    assert explicit["code"].nunique() > 5 * default["code"].nunique()
    assert set(explicit_default["code"]) == set(default["code"])
