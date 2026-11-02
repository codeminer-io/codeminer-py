"""Validate that Python client functions match the OpenAPI spec from the API.

These tests require a running CodeMiner API server and are skipped by default.
Run with: pytest -m integration
"""

import inspect

import pytest
import requests

import codeminer
from codeminer._helpers import _get_base_url

pytestmark = pytest.mark.integration

# Python functions that correspond to API endpoints
ENDPOINT_FUNCTIONS = {
    "/DESCRIPTION": codeminer.DESCRIPTION,
    "/CODES_LIKE": codeminer.CODES_LIKE,
    "/CODES": codeminer.CODES,
    "/CHILDREN": codeminer.CHILDREN,
    "/N_CHILDREN": codeminer.N_CHILDREN,
    "/PARENTS": codeminer.PARENTS,
    "/N_PARENTS": codeminer.N_PARENTS,
    "/ATTRIBUTES_FOR": codeminer.ATTRIBUTES_FOR,
    "/HAS_ATTRIBUTES": codeminer.HAS_ATTRIBUTES,
    "/RELATIONSHIP_TYPES": codeminer.RELATIONSHIP_TYPES,
    "/RELATIONSHIP_TYPES_FROM": codeminer.RELATIONSHIP_TYPES_FROM,
    "/RELATIONSHIP_TYPES_TO": codeminer.RELATIONSHIP_TYPES_TO,
    "/MAP": codeminer.MAP,
    "/get_relationship_tree": codeminer.get_relationship_tree,
}

# Paging endpoints that the R client doesn't expose either
INTERNAL_ENDPOINTS = {
    "/CODES_ALL_CHUNK",
    "/CODES_LIKE_CHUNK",
    "/DESCRIPTION_CHUNK",
}

# Parameters that are Python-only (not in the API spec)
PYTHON_ONLY_PARAMS = {"return_raw", "base_url", "self"}

# Parameter name mappings: Python name -> API name
PARAM_RENAMES = {
    "from_type": "from",
    "to_type": "to",
    "codes": "codes",  # *codes -> codes
}


@pytest.fixture(scope="module")
def openapi_spec():
    """Fetch the OpenAPI spec from the running API."""
    base_url = _get_base_url(None)
    try:
        resp = requests.get(f"{base_url}/openapi.json", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("CodeMiner API not available")


def test_all_endpoints_have_python_functions(openapi_spec):
    """Every POST endpoint in the spec should have a corresponding Python function."""
    spec_paths = openapi_spec.get("paths", {})
    post_endpoints = {
        path for path, methods in spec_paths.items() if "post" in methods
    }

    python_endpoints = set(ENDPOINT_FUNCTIONS.keys())
    missing = post_endpoints - python_endpoints - INTERNAL_ENDPOINTS

    # Filter out test/internal endpoints
    missing = {p for p in missing if not p.startswith("/TEST_")}

    assert not missing, f"API endpoints without Python functions: {missing}"


def test_python_functions_have_endpoints(openapi_spec):
    """Every Python function should correspond to an API endpoint."""
    spec_paths = openapi_spec.get("paths", {})
    for endpoint in ENDPOINT_FUNCTIONS:
        assert endpoint.lower() in {
            p.lower() for p in spec_paths
        }, f"Python function for {endpoint} has no corresponding API endpoint"


def test_parameter_names_match(openapi_spec):
    """Python function parameters should match the API spec's requestBody schema."""
    spec_paths = openapi_spec.get("paths", {})

    for endpoint, func in ENDPOINT_FUNCTIONS.items():
        # Get API parameters from spec
        path_spec = spec_paths.get(endpoint, {})
        post_spec = path_spec.get("post", {})

        api_params = set()

        # Check requestBody schema properties
        request_body = post_spec.get("requestBody", {})
        content = request_body.get("content", {})
        json_schema = content.get("application/json", {}).get("schema", {})
        api_params.update(json_schema.get("properties", {}).keys())

        # Also check query parameters
        for param in post_spec.get("parameters", []):
            api_params.add(param["name"])

        if not api_params:
            continue

        # Get Python function parameters
        sig = inspect.signature(func)
        py_params = set()
        for name, param in sig.parameters.items():
            if name in PYTHON_ONLY_PARAMS:
                continue
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                py_params.add("codes")
                continue
            # Apply renames
            api_name = PARAM_RENAMES.get(name, name)
            py_params.add(api_name)

        # Filter internal API params (req, res)
        api_params -= {"req", "res"}

        missing_in_python = api_params - py_params
        assert not missing_in_python, (
            f"{endpoint}: API params not in Python function: {missing_in_python}"
        )
