"""Infix set-operation combinators for composing code lists.

Provides ``OR``, ``AND``, and ``NOT`` operators that can be used with
the ``>>OP>>`` infix syntax to combine DataFrames::

    DESCRIPTION("diab", type="icd10") >>AND>> (
        CHILDREN("E10", type="icd10") >>OR>> CHILDREN("E11", type="icd10")
    )
"""

import pandas as pd

from ._codelist import CodeList


class Infix:
    """Wrapper enabling ``>>operator>>`` infix syntax for binary functions."""

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
def OR(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame | CodeList:
    """Union of two DataFrames (set OR).

    Returns a :class:`CodeList` when the result has the required columns,
    otherwise a plain :class:`pd.DataFrame`.

    Parameters
    ----------
    df1 : pd.DataFrame
        First code list.
    df2 : pd.DataFrame
        Second code list.

    Returns
    -------
    pd.DataFrame | CodeList
        Combined rows, deduplicated.
    """
    return CodeList._wrap(
        pd.concat([df1, df2]).drop_duplicates().reset_index(drop=True)
    )


@Infix
def AND(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame | CodeList:
    """Intersection of two DataFrames (set AND).

    Returns a :class:`CodeList` when the result has the required columns,
    otherwise a plain :class:`pd.DataFrame`.

    Parameters
    ----------
    df1 : pd.DataFrame
        First code list.
    df2 : pd.DataFrame
        Second code list.

    Returns
    -------
    pd.DataFrame | CodeList
        Rows present in both DataFrames.
    """
    return CodeList._wrap(df1.merge(df2, how="inner"))


@Infix
def NOT(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame | CodeList:
    """Set difference: rows in df1 but not in df2 (set NOT).

    Returns a :class:`CodeList` when the result has the required columns,
    otherwise a plain :class:`pd.DataFrame`.

    Parameters
    ----------
    df1 : pd.DataFrame
        Base code list.
    df2 : pd.DataFrame
        Codes to exclude.

    Returns
    -------
    pd.DataFrame | CodeList
        Rows from df1 not found in df2.
    """
    merged = df1.merge(df2, how="left", indicator=True)
    return CodeList._wrap(
        merged[merged["_merge"] == "left_only"]
        .drop(columns=["_merge"])
        .reset_index(drop=True)
    )
