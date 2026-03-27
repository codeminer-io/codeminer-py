"""CodeList: a lightweight DataFrame subclass for clinical code lists.

Mirrors R's ``codeminer_codelist`` S3 class. A ``CodeList`` is a
``pd.DataFrame`` with required columns ``code``, ``description``, and
``code_type`` (all string), where ``code_type`` contains exactly one
unique value.
"""

from __future__ import annotations

import pandas as pd
from rich.console import Console

_codelist_cols = ("code", "description", "code_type")

_console = Console(stderr=True)


class CodeList(pd.DataFrame):
    """A DataFrame of clinical codes with a single code type.

    Subclasses :class:`pd.DataFrame` and adds validation and a custom
    repr mirroring R's ``print.codeminer_codelist()``.

    Parameters
    ----------
    data : dict | list | pd.DataFrame
        Data to construct the CodeList from. Must contain columns
        ``code``, ``description``, and ``code_type``.
    *args, **kwargs
        Passed through to :class:`pd.DataFrame`.
    """

    @property
    def _constructor(self):
        return CodeList

    @property
    def code_type(self) -> str | None:
        """The single code type, or ``None`` if the CodeList is empty."""
        if "code_type" not in self.columns or len(self) == 0:
            return None
        return self["code_type"].iloc[0]

    def __repr__(self) -> str:
        n = len(self)
        label = "code" if n == 1 else "codes"
        header = f"CodeList: {n} {label}"

        lines = [header]
        ct = self.code_type
        if ct is not None:
            lines.append(f"Code type: {ct}")
        lines.append("")
        lines.append(pd.DataFrame.__repr__(self))
        return "\n".join(lines)

    def _repr_html_(self) -> str:
        n = len(self)
        label = "code" if n == 1 else "codes"
        ct = self.code_type

        header = f"<strong>CodeList</strong>: {n} {label}"
        if ct is not None:
            header += f" &middot; Code type: {ct}"

        return header + "<br>" + pd.DataFrame._repr_html_(self)


def _as_codelist(df: pd.DataFrame) -> pd.DataFrame | CodeList:
    """Wrap a DataFrame as a CodeList if it has the required columns.

    Mirrors R's ``api_request()`` logic::

        if (all(c("code", "description", "code_type") %in% names(result)))
            class(result) <- c("codeminer_codelist", class(result))

    Returns the original DataFrame unchanged if columns are missing or
    ``code_type`` has multiple values.
    """
    if not all(col in df.columns for col in _codelist_cols):
        return df

    if len(df) == 0:
        return CodeList(df)

    if df["code_type"].nunique() != 1:
        return pd.DataFrame(df) if isinstance(df, CodeList) else df

    return CodeList(df)
