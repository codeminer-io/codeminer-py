"""
Python wrapper for the CodeMiner API.

Search strategies may be composed using infix operators, e.g.:

DESCRIPTION("diab", "icd10") >>AND>> (
    CHILDREN("E10", "icd10") >>OR>> CHILDREN("E11", "icd10")
)
"""

import os
from typing import List, Optional, Union
from urllib.parse import urljoin

import requests
import pandas as pd

try:
    from rich import print as rprint
    USE_RICH = True
except ImportError:
    USE_RICH = False


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------

class CodeMinerError(Exception):
    """Custom exception for CodeMiner client errors."""
    pass


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def _get_base_url(base_url: Optional[str]) -> str:
    """Resolve which base URL to use."""
    return base_url or os.environ.get("CODEMINER_BASE_URL", DEFAULT_BASE_URL)


def _validate_code_type(code_type: str):
    """Validate code_type argument."""
    valid = {"sct", "icd10"}
    if code_type not in valid:
        raise ValueError(f"code_type must be one of {valid}, got {code_type!r}")


def _api_call(
    endpoint: str,
    params: dict,
    base_url: Optional[str] = None,
    raw: bool = False
) -> Union[pd.DataFrame, dict]:
    """
    Low-level API GET wrapper.
    Returns a DataFrame or raw JSON depending on `raw`.
    """
    url = _get_base_url(base_url)
    full_url = urljoin(url + "/", endpoint)

    try:
        response = requests.get(full_url, params=params)
    except requests.RequestException as e:
        raise CodeMinerError(f"Error communicating with the CodeMiner API: {e}") from e

    if response.status_code >= 400:
        # Try structured JSON error
        try:
            err = response.json()
        except ValueError:
            raise CodeMinerError(f"API error {response.status_code}: {response.text}")

        # Show CLI-style bullets if present
        if USE_RICH and "error" in err:
            rprint(f"[bold red]API Error ({err['error']['error_type']}):[/]")
            for item in err["error"]["error_message"]:
                for nm, msg in item.items():
                    rprint(f"  {nm}: {msg}")

        raise CodeMinerError(err)

    # Empty body → empty DataFrame
    if not response.text:
        return {} if raw else pd.DataFrame()

    try:
        data = response.json()
    except ValueError:
        raise CodeMinerError("Invalid JSON from API")

    if raw:
        return data

    # Normal success → DataFrame with results
    if "result" in data:
        return pd.DataFrame(data["result"])
    else:
        return pd.DataFrame(data)


# ---------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------

def DESCRIPTION(
    pattern: str,
    code_type: str,
    base_url: Optional[str] = None,
    raw: bool = False
) -> pd.DataFrame:
    """Search descriptions by regex pattern."""
    _validate_code_type(code_type)
    return _api_call(
        "DESCRIPTION",
        {"pattern": pattern, "code_type": code_type},
        base_url,
        raw=raw
    )


def CODES(
    codes: List[str],
    code_type: str,
    base_url: Optional[str] = None,
    raw: bool = False
) -> pd.DataFrame:
    """Look up descriptions for specific codes."""
    _validate_code_type(code_type)
    return _api_call(
        "CODES",
        {"codes": codes, "code_type": code_type},
        base_url,
        raw=raw
    )


def CHILDREN(
    codes: List[str],
    code_type: str,
    base_url: Optional[str] = None,
    raw: bool = False
) -> pd.DataFrame:
    """Return descendant codes."""
    _validate_code_type(code_type)
    return _api_call(
        "CHILDREN",
        {"codes": codes, "code_type": code_type},
        base_url,
        raw=raw
    )


# ---------------------------------------------------------------------
# Infix combinators
# ---------------------------------------------------------------------

class Infix:
    """Simple infix operator helper."""
    def __init__(self, function):
        self.function = function

    def __rlshift__(self, other):
        return Infix(lambda x: self.function(other, x))

    def __lshift__(self, other):
        return self.function(other)

    def __rrshift__(self, other):
        return Infix(lambda x: self.function(other, x))

    def __rshift__(self, other):
        return self.function(other)


@Infix
def OR(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Union of two DataFrames."""
    return pd.concat([df1, df2]).drop_duplicates().reset_index(drop=True)


@Infix
def AND(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Intersection of two DataFrames."""
    return df1.merge(df2, how="inner")


@Infix
def NOT(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Set difference: df1 - df2."""
    merged = df1.merge(df2, how="left", indicator=True)
    return merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
