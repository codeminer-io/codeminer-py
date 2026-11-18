"""Public API functions mirroring the R codeminer.api package.

Each function corresponds to a POST endpoint on the CodeMiner API server,
with parameter names matching the R package as closely as possible.

Parameters with config-aware defaults use the ``_unset`` sentinel. Resolution
order: explicit argument > ``config`` value > hardcoded default.
"""

from __future__ import annotations

import math
from typing import Union

import pandas as pd
import requests

from ._config import _resolve, _resolve_raw, _unset
from ._helpers import _api_request, _collect_codes, _get_base_url
from .exceptions import CodeMinerError

# ---------------------------------------------------------------------------
# Pattern-based search functions
# ---------------------------------------------------------------------------


def DESCRIPTION(
    pattern: str,
    type: str | None = _unset,
    lookup_version: str = _unset,
    ignore_case: bool = True,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Search for codes by description pattern.

    Parameters
    ----------
    pattern : str
        Regex pattern to match against code descriptions.
    type : str | None
        Code type to search (e.g. ``"ICD-10"``, ``"SNOMED CT"``). Falls back to
        ``config.type`` if not provided.
    lookup_version : str
        Version of the lookup table to use.
    ignore_case : bool
        Whether pattern matching should be case-insensitive.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. ``"default"`` for standard filters,
        ``None`` for no filtering, or a dict for custom filters. Falls back
        to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of matching codes, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> DESCRIPTION("asthma", type="ICD-10")
    >>> DESCRIPTION("diabet", type="SNOMED CT", ignore_case=True)
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    body_params = {
        "pattern": pattern,
        "type": type,
        "lookup_version": lookup_version,
        "ignore_case": ignore_case,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/DESCRIPTION",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def CODES_LIKE(
    pattern: str,
    type: str | None = _unset,
    lookup_version: str = _unset,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Search for codes matching a regex pattern on the code itself.

    Parameters
    ----------
    pattern : str
        Regex pattern to match against codes (e.g. ``"^J45"``).
    type : str | None
        Code type to search.
    lookup_version : str
        Version of the lookup table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of matching codes, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> CODES_LIKE("^J45", type="ICD-10")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    body_params = {
        "pattern": pattern,
        "type": type,
        "lookup_version": lookup_version,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/CODES_LIKE", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


# ---------------------------------------------------------------------------
# Code-based lookup functions
# ---------------------------------------------------------------------------


def CODES(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    lookup_version: str = _unset,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Look up specific codes and their descriptions.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Individual code strings, or a single DataFrame with ``code`` and
        ``code_type`` columns.
    type : str | None
        Code type (e.g. ``"ICD-10"``, ``"SNOMED CT"``).
    lookup_version : str
        Version of the lookup table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of code information, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> CODES("J45", "E11", type="ICD-10")
    >>> CODES(existing_codelist)
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/CODES", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def CHILDREN(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get codes and all of their descendants in the hierarchy.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Parent code(s) to find children of.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of the input codes and their descendants, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> CHILDREN("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/CHILDREN", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def N_CHILDREN(
    *codes: str | pd.DataFrame,
    depth: int | float = 1,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get codes and their descendants to a specified depth in the hierarchy.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Parent code(s) to find descendants of.
    depth : int | float
        Number of levels to traverse, at least 1. Use ``math.inf`` for unlimited
        depth.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of the input codes and their descendants, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> N_CHILDREN("73211009", depth=2, type="SNOMED CT")
    >>> N_CHILDREN("73211009", depth=math.inf, type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "depth": depth,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/N_CHILDREN", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def PARENTS(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get codes and all of their ancestors in the hierarchy.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Child code(s) to find parents of.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of the input codes and their ancestors, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> PARENTS("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/PARENTS", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def N_PARENTS(
    *codes: str | pd.DataFrame,
    depth: int | float = 1,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get codes and their ancestors to a specified depth in the hierarchy.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Child code(s) to find ancestors of.
    depth : int | float
        Number of levels to traverse, at least 1. Use ``math.inf`` for unlimited
        depth.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of the input codes and their ancestors, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> N_PARENTS("73211009", depth=2, type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "depth": depth,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/N_PARENTS", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def ATTRIBUTES_FOR(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    relationship_types: list[str] | pd.DataFrame | None = None,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get attribute codes related to the specified codes.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to get attributes for.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    relationship_types : list[str] | pd.DataFrame | None
        Filter by specific relationship types. Can be a list of strings or
        a DataFrame with a ``code`` column.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of attribute codes, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> ATTRIBUTES_FOR("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)

    # Normalize relationship_types: DataFrame → list of strings
    if isinstance(relationship_types, pd.DataFrame):
        relationship_types = relationship_types["code"].tolist()

    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "relationship_types": relationship_types,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/ATTRIBUTES_FOR",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def HAS_ATTRIBUTES(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    lookup_version: str = _unset,
    relationship_version: str = _unset,
    relationship_types: list[str] | pd.DataFrame | None = None,
    preferred_description_only: bool = True,
    max_nodes: int = 20000,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Check which codes have attributes of specified types.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to check for attributes.
    type : str | None
        Code type.
    lookup_version : str
        Version of the lookup table to use.
    relationship_version : str
        Version of the relationship table to use.
    relationship_types : list[str] | pd.DataFrame | None
        Filter by specific relationship types. Can be a list of strings or
        a DataFrame with a ``code`` column.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    max_nodes : int
        Ceiling on the number of codes the traversal can accumulate before
        the server raises an error.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of results, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> HAS_ATTRIBUTES("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)

    if isinstance(relationship_types, pd.DataFrame):
        relationship_types = relationship_types["code"].tolist()

    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "lookup_version": lookup_version,
        "relationship_version": relationship_version,
        "relationship_types": relationship_types,
        "preferred_description_only": preferred_description_only,
        "max_nodes": max_nodes,
        "col_filters": col_filters,
    }
    return _api_request(
        "/HAS_ATTRIBUTES",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def RELATIONSHIP_TYPES_FROM(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    relationship_version: str = _unset,
    lookup_version: str = _unset,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get the types of relationships originating from the specified codes.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to query.
    type : str | None
        Code type.
    relationship_version : str
        Version of the relationship table to use.
    lookup_version : str
        Version of the lookup table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of relationship types, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> RELATIONSHIP_TYPES_FROM("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "relationship_version": relationship_version,
        "lookup_version": lookup_version,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/RELATIONSHIP_TYPES_FROM",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def RELATIONSHIP_TYPES_TO(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    relationship_version: str = _unset,
    lookup_version: str = _unset,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Get the types of relationships pointing to the specified codes.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to query.
    type : str | None
        Code type.
    relationship_version : str
        Version of the relationship table to use.
    lookup_version : str
        Version of the lookup table to use.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of relationship types, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> RELATIONSHIP_TYPES_TO("73211009", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "relationship_version": relationship_version,
        "lookup_version": lookup_version,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/RELATIONSHIP_TYPES_TO",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def RELATIONSHIP_TYPES(
    pattern: str | None = None,
    type: str | None = _unset,
    relationship_version: str = _unset,
    lookup_version: str = _unset,
    ignore_case: bool = True,
    preferred_description_only: bool = True,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """List the relationship types in a code type's relationship table.

    Parameters
    ----------
    pattern : str | None
        Regex pattern to match against relationship type descriptions. If
        ``None``, return all relationship types.
    type : str | None
        Code type.
    relationship_version : str
        Version of the relationship table to use.
    lookup_version : str
        Version of the lookup table to use.
    ignore_case : bool
        Whether pattern matching should be case-insensitive.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of relationship types, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> RELATIONSHIP_TYPES(type="SNOMED CT")
    >>> RELATIONSHIP_TYPES("finding site", type="SNOMED CT")
    """
    type = _resolve(type, "type")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    body_params = {
        "pattern": pattern,
        "type": type,
        "relationship_version": relationship_version,
        "lookup_version": lookup_version,
        "ignore_case": ignore_case,
        "preferred_description_only": preferred_description_only,
        "col_filters": col_filters,
    }
    return _api_request(
        "/RELATIONSHIP_TYPES",
        body_params=body_params,
        return_raw=return_raw,
        base_url=base_url,
    )


def MAP(
    *codes: str | pd.DataFrame,
    from_type: str | None = _unset,
    to_type: str | None = _unset,
    map_version: str = _unset,
    lookup_version: str = _unset,
    col_filters: str | dict | None = _unset,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict:
    """Map codes from one coding system to another.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to map.
    from_type : str | None
        Source code type (e.g. ``"ICD-10"``). Named ``from_type`` because
        ``from`` is a Python reserved word; maps to the ``from`` API parameter.
        Falls back to ``config.map_from`` if not provided (mirroring R's
        ``codeminer.map_from`` option).
    to_type : str | None
        Target code type (e.g. ``"SNOMED CT"``). Falls back to ``config.map_to``
        if not provided (mirroring R's ``codeminer.map_to`` option).
    map_version : str
        Version of the mapping table to use.
    lookup_version : str
        Version of the lookup table to use.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict
        A DataFrame of mapped codes, or raw JSON if ``return_raw=True``.

    Examples
    --------
    >>> MAP("4939", from_type="ICD-9", to_type="ICD-10")
    """
    from_type = _resolve(from_type, "map_from")
    to_type = _resolve(to_type, "map_to")
    map_version = _resolve(map_version, "map_version", "latest")
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=from_type)
    body_params = {
        "codes": collected_codes,
        "from": df_type or from_type,
        "to": to_type,
        "map_version": map_version,
        "lookup_version": lookup_version,
        "col_filters": col_filters,
    }
    return _api_request(
        "/MAP", body_params=body_params, return_raw=return_raw, base_url=base_url
    )


def get_relationship_tree(
    *codes: str | pd.DataFrame,
    type: str | None = _unset,
    expand_to_descendants: bool = True,
    max_codes: int = 10000,
    relationship_version: str = _unset,
    lookup_version: str = _unset,
    col_filters: str | dict | None = _unset,
    preferred_description_only: bool = True,
    return_raw: bool = False,
    base_url: str | None = None,
) -> dict:
    """Get the hierarchy around a set of codes as nodes and edges.

    Parameters
    ----------
    *codes : str | pd.DataFrame
        Code(s) to build the tree from.
    type : str | None
        Code type.
    expand_to_descendants : bool
        If ``True``, include the descendants of the input codes.
    max_codes : int
        Ceiling on the number of codes in the tree.
    relationship_version : str
        Version of the relationship table to use.
    lookup_version : str
        Version of the lookup table to use.
    col_filters : str | dict | None
        Column filter specification. Falls back to ``config.col_filters``.
    preferred_description_only : bool
        If ``True``, return only preferred descriptions.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    dict
        A dict with ``"nodes"`` and ``"edges"`` DataFrames, or raw JSON if
        ``return_raw=True``.

    Examples
    --------
    >>> tree = get_relationship_tree("E11", type="ICD-10")
    >>> tree["edges"]
    """
    type = _resolve(type, "type")
    relationship_version = _resolve(
        relationship_version, "relationship_version", "latest"
    )
    lookup_version = _resolve(lookup_version, "lookup_version", "latest")
    col_filters = _resolve_raw(col_filters, "col_filters")

    collected_codes, df_type = _collect_codes(*codes, type=type)
    body_params = {
        "codes": collected_codes,
        "type": df_type or type,
        "expand_to_descendants": expand_to_descendants,
        "max_codes": max_codes,
        "relationship_version": relationship_version,
        "lookup_version": lookup_version,
        "col_filters": col_filters,
        "preferred_description_only": preferred_description_only,
    }

    # Always get raw to handle the nested structure ourselves
    raw = _api_request(
        "/get_relationship_tree",
        body_params=body_params,
        return_raw=True,
        base_url=base_url,
    )

    if return_raw:
        return raw

    result = raw.get("result", raw)
    return {
        "nodes": pd.DataFrame(result["nodes"]),
        "edges": pd.DataFrame(result["edges"]),
    }


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def check_api_connection(url: str | None = None) -> bool:
    """Check if the CodeMiner API is available.

    Tests connection by calling the ``/health`` endpoint. Prints diagnostic
    information using rich formatting.

    Parameters
    ----------
    url : str | None
        API base URL to check. If ``None``, uses the default resolution.

    Returns
    -------
    bool
        ``True`` if the API is reachable, ``False`` otherwise.

    Examples
    --------
    >>> check_api_connection()
    >>> check_api_connection("http://myserver:9000")
    """
    from rich.console import Console

    console = Console(stderr=True)
    resolved_url = _get_base_url(url)

    try:
        response = requests.get(f"{resolved_url}/health", timeout=5)
        response.raise_for_status()
        body = response.json()
        console.print(
            f"[green]✔[/green] API is available at [link]{resolved_url}[/link]"
        )
        console.print(
            f"[cyan]ℹ[/cyan] Service: {body.get('service', '?')}, "
            f"Version: {body.get('version', '?')}"
        )
        return True
    except Exception as e:
        console.print(
            f"[red]✖[/red] Failed to connect to API at [link]{resolved_url}[/link]"
        )
        console.print(f"[cyan]ℹ[/cyan] Error: {e}")
        return False


def get_codeminer_metadata(
    type: str | list[str] | None = None,
    return_raw: bool = False,
    base_url: str | None = None,
) -> pd.DataFrame | dict[str, pd.DataFrame] | dict:
    """Get metadata about the CodeMiner database tables.

    Returns metadata about the lookup, mapping, and relationship tables
    available in the CodeMiner database connected to the API server.

    Parameters
    ----------
    type : str | list[str] | None
        Metadata type(s) to return. One or more of ``"lookup"``,
        ``"mapping"``, ``"relationship"``. If ``None``, returns all three.
    return_raw : bool
        If ``True``, return the raw JSON response dict.
    base_url : str | None
        Override the API base URL.

    Returns
    -------
    pd.DataFrame | dict[str, pd.DataFrame] | dict
        If a single type is requested, a DataFrame. If multiple types, a
        dict of DataFrames keyed by type name. If ``return_raw=True``, the
        raw JSON dict.

    Examples
    --------
    >>> get_codeminer_metadata()
    >>> get_codeminer_metadata("lookup")
    >>> get_codeminer_metadata(["lookup", "mapping"])
    """
    if type is None:
        type = ["lookup", "mapping", "relationship"]
    if isinstance(type, str):
        type = [type]

    type_str = ",".join(type)
    query_params = {"type": type_str}

    # Always get raw to handle the nested structure ourselves
    raw = _api_request(
        "/metadata", query_params=query_params, return_raw=True, base_url=base_url
    )

    if return_raw:
        return raw

    result = raw.get("result", raw)

    # Single type → DataFrame
    if len(type) == 1:
        if isinstance(result, list):
            return pd.DataFrame(result)
        elif isinstance(result, dict):
            return pd.DataFrame(result)
        return pd.DataFrame()

    # Multiple types → dict of DataFrames
    if isinstance(result, dict):
        return {k: pd.DataFrame(v) for k, v in result.items()}

    return result
