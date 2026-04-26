"""Lightweight ``pd.DataFrame`` subclass for clinical-code lists.

Mirrors the R sibling package's ``codeminer_codelist`` S3 class
(see ``codeminer/R/codelist-class.R``). Construction is lenient — like R's
``as_codelist`` it does not validate — while :meth:`CodeList.validate` runs
the strict checks (required columns present, character dtype, no NAs,
single ``code_type``). The :meth:`CodeList._wrap` factory is the boundary
helper: it returns a ``CodeList`` only when the required columns are
present, otherwise the input data frame is returned unchanged.
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("code", "description", "code_type")


class CodeList(pd.DataFrame):
    """A ``pd.DataFrame`` carrying ``code``, ``description``, ``code_type`` columns.

    The constructor itself is lenient (mirrors R's ``as_codelist``): it does
    not validate. Validation belongs to :meth:`validate` for strict R-style
    checks, or to the :meth:`_wrap` factory for the column-presence check
    used at API and combinator boundaries.

    Examples
    --------
    >>> CodeList({"code": ["J45"], "description": ["Asthma"], "code_type": ["icd10"]})
    """

    _metadata: list[str] = []

    @property
    def _constructor(self):
        return CodeList

    @classmethod
    def _wrap(cls, df: pd.DataFrame) -> "CodeList | pd.DataFrame":
        """Return ``df`` as a ``CodeList`` if it has the required columns, else as-is."""
        if all(c in df.columns for c in REQUIRED_COLUMNS):
            return cls(df)
        return df

    def validate(self) -> str:
        """Run strict R-style validation and return the unique ``code_type``.

        Mirrors ``validate_codeminer_codelist`` in the R package: required
        columns present, all character/object dtype, no NAs in required
        columns, and exactly one unique ``code_type``.

        Returns
        -------
        str
            The unique ``code_type`` value.

        Raises
        ------
        ValueError
            If any validation rule fails.
        """
        missing = [c for c in REQUIRED_COLUMNS if c not in self.columns]
        if missing:
            raise ValueError(
                f"Data frame is missing required columns: {missing}. "
                f"Required: {list(REQUIRED_COLUMNS)}."
            )

        non_char = [
            c for c in REQUIRED_COLUMNS
            if not pd.api.types.is_string_dtype(self[c])
        ]
        if non_char:
            raise ValueError(
                f"All required columns must be character (string) dtype. "
                f"Non-character columns: {non_char}."
            )

        cols_with_na = [c for c in REQUIRED_COLUMNS if self[c].isna().any()]
        if cols_with_na:
            raise ValueError(
                f"Data frame contains missing values in required columns: {cols_with_na}."
            )

        unique_types = self["code_type"].unique().tolist()
        if len(unique_types) == 0:
            raise ValueError("The 'code_type' column is empty.")
        if len(unique_types) > 1:
            raise ValueError(
                f"The 'code_type' column must contain only one unique value. "
                f"Found {len(unique_types)}: {unique_types}."
            )

        return str(unique_types[0])

    def _header_lines(self) -> list[str]:
        n = len(self)
        plural = "" if n == 1 else "s"
        lines = [f"<CodeList: {n} code{plural}>"]
        if "code_type" in self.columns and n > 0:
            non_na = self["code_type"].dropna().unique()
            if len(non_na) == 1:
                lines.append(f'Code type: "{non_na[0]}"')
        return lines

    def __repr__(self) -> str:
        header = "\n".join(self._header_lines())
        return f"{header}\n\n{super().__repr__()}"

    def _repr_html_(self) -> str:
        header_html = "<br>".join(self._header_lines())
        body = super()._repr_html_() or ""
        return f'<div>{header_html}</div>\n{body}'
