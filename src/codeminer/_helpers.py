"""Internal helpers: base URL resolution, codes input collection, API request."""

from __future__ import annotations

import math
import os
from typing import Union

import pandas as pd
import requests

from ._config import config
from .exceptions import CodeMinerError
from ._conditions import _print_conditions, _raise_api_error

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def _get_base_url(base_url: str | None) -> str:
    """Resolve the API base URL.

    Resolution order: explicit argument > ``config.base_url`` >
    ``CODEMINER_BASE_URL`` env var > ``"http://127.0.0.1:8000"``.

    Parameters
    ----------
    base_url : str | None
        Explicit URL, or ``None`` to use config/env/default.

    Returns
    -------
    str
        The resolved base URL with any trailing slash stripped.
    """
    url = (
        base_url
        or config.base_url
        or os.environ.get("CODEMINER_BASE_URL", DEFAULT_BASE_URL)
    )
    return url.rstrip("/")


def _collect_codes(
    *codes: str | pd.DataFrame,
    type: str | None = None,
) -> tuple[list[str], str | None]:
    """Normalize variadic code input.

    Mirrors R's ``collect_codes_input()`` from ``codeminer/R/codelist-utils.R``.
    Accepts either multiple string arguments or a single DataFrame with
    ``code`` and ``code_type`` columns.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Individual code strings, or a single DataFrame with ``code`` and
        ``code_type`` columns.
    type : str | None
        Explicit code type. If a DataFrame is passed and has a ``code_type``
        column, the types must be consistent.

    Returns
    -------
    tuple[list[str], str | None]
        ``(codes_list, inferred_type)`` where ``inferred_type`` is extracted
        from the DataFrame if applicable, otherwise ``None``.

    Raises
    ------
    ValueError
        If input is invalid or type conflicts are detected.
    """
    if len(codes) == 0:
        return ([], None)

    # Single DataFrame input
    if len(codes) == 1 and isinstance(codes[0], pd.DataFrame):
        df = codes[0]

        if "code" not in df.columns:
            raise ValueError(
                "DataFrame must have a 'code' column."
            )

        codes_list = df["code"].astype(str).tolist()

        # Extract code_type from DataFrame if present
        df_type = None
        if "code_type" in df.columns:
            unique_types = df["code_type"].unique()
            if len(unique_types) != 1:
                raise ValueError(
                    f"DataFrame has multiple code types: {unique_types.tolist()}"
                )
            df_type = str(unique_types[0])

            # Check for conflict with explicit type
            if type is not None and df_type != type:
                raise ValueError(
                    f"Explicit type '{type}' conflicts with DataFrame "
                    f"code_type '{df_type}'."
                )

        return (codes_list, df_type)

    # Multiple string arguments
    for c in codes:
        if not isinstance(c, str):
            raise TypeError(
                f"Expected string code arguments, got {c.__class__.__name__}. "
                "Pass either individual code strings or a single DataFrame."
            )

    return (list(codes), None)


def _api_request(
    endpoint: str,
    *,
    body_params: dict | None = None,
    query_params: dict | None = None,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Make a request to the CodeMiner API.

    Mirrors R's ``api_request()`` in ``codeminer.api/R/client-helpers.R``.

    Parameters
    ----------
    endpoint : str
        API endpoint path (e.g. ``"/DESCRIPTION"``).
    body_params : dict | None
        If provided, send a POST request with JSON body.
    query_params : dict | None
        If provided (and no body_params), send a GET request with query params.
    return_raw : bool
        If ``True``, return the parsed JSON dict instead of a DataFrame.
    base_url : str | None
        Override the base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of results, or raw JSON dict if ``return_raw=True``.

    Raises
    ------
    CodeMinerError
        On HTTP errors or connection failures.
    """
    url = _get_base_url(base_url)
    full_url = f"{url}{endpoint}"

    try:
        if body_params is not None:
            # Serialize math.inf as "Inf" string for JSON
            body = _serialize_body(body_params)
            response = requests.post(full_url, json=body)
        else:
            response = requests.get(full_url, params=query_params or {})
    except requests.RequestException as e:
        raise CodeMinerError(
            f"Failed to connect to CodeMiner API at {full_url}: {e}"
        ) from e

    # Handle HTTP errors
    if response.status_code >= 400:
        try:
            err = response.json()
        except ValueError:
            raise CodeMinerError(
                f"API error {response.status_code}: {response.text}"
            )

        if "error" in err:
            # Replay any warnings/messages that came with the error
            _print_conditions(err)
            _raise_api_error(err["error"], response.status_code)
        else:
            raise CodeMinerError(
                f"API error {response.status_code}: {err}"
            )

    # Empty body
    if not response.text:
        return {} if return_raw else pd.DataFrame()

    try:
        data = response.json()
    except ValueError:
        raise CodeMinerError("Invalid JSON response from API")

    # Replay warnings and messages
    _print_conditions(data)

    if return_raw:
        return data

    # Normal success → DataFrame
    result = data.get("result", data)
    if isinstance(result, list):
        return pd.DataFrame(result)
    elif isinstance(result, dict):
        return pd.DataFrame(result)
    else:
        return pd.DataFrame()


def _serialize_body(params: dict) -> dict:
    """Prepare body params for JSON serialization.

    - Converts ``math.inf`` to the string ``"Inf"`` (R convention).
    - Keeps ``None`` values for keys where null is meaningful (e.g. col_filters).

    Parameters
    ----------
    params : dict
        The body parameters.

    Returns
    -------
    dict
        The serialized parameters.
    """
    result = {}
    for key, value in params.items():
        if isinstance(value, float) and math.isinf(value):
            result[key] = "Inf"
        else:
            result[key] = value
    return result
