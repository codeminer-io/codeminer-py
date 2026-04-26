"""Tests for _combinators.py: Infix OR, AND, NOT operators."""

import pandas as pd
import pytest

from codeminer import OR, AND, NOT, CodeList


@pytest.fixture
def df1():
    return pd.DataFrame({
        "code": ["J45", "E11", "E10"],
        "description": ["Asthma", "Type 2 DM", "Type 1 DM"],
    })


@pytest.fixture
def df2():
    return pd.DataFrame({
        "code": ["E11", "I10"],
        "description": ["Type 2 DM", "Hypertension"],
    })


class TestOR:
    def test_union(self, df1, df2):
        result = df1 >>OR>> df2
        assert set(result["code"]) == {"J45", "E11", "E10", "I10"}

    def test_deduplication(self, df1, df2):
        result = df1 >>OR>> df2
        assert len(result[result["code"] == "E11"]) == 1


class TestAND:
    def test_intersection(self, df1, df2):
        result = df1 >>AND>> df2
        assert list(result["code"]) == ["E11"]

    def test_empty_intersection(self):
        a = pd.DataFrame({"code": ["A"]})
        b = pd.DataFrame({"code": ["B"]})
        result = a >>AND>> b
        assert len(result) == 0


class TestNOT:
    def test_set_difference(self, df1, df2):
        result = df1 >>NOT>> df2
        assert set(result["code"]) == {"J45", "E10"}

    def test_not_everything(self, df1):
        result = df1 >>NOT>> df1
        assert len(result) == 0


class TestComposition:
    def test_chained_operations(self, df1, df2):
        # (df1 OR df2) AND df1 == df1
        result = (df1 >>OR>> df2) >>AND>> df1
        assert set(result["code"]) == {"J45", "E11", "E10"}


# ---------------------------------------------------------------------------
# CodeList preservation through combinators
# ---------------------------------------------------------------------------


@pytest.fixture
def cl1():
    return CodeList([
        {"code": "J45", "description": "Asthma", "code_type": "icd10"},
        {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        {"code": "E10", "description": "Type 1 DM", "code_type": "icd10"},
    ])


@pytest.fixture
def cl2():
    return CodeList([
        {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        {"code": "I10", "description": "Hypertension", "code_type": "icd10"},
    ])


class TestCodeListPreservation:
    def test_or_returns_codelist(self, cl1, cl2):
        result = cl1 >>OR>> cl2
        assert isinstance(result, CodeList)
        assert set(result["code"]) == {"J45", "E11", "E10", "I10"}

    def test_and_returns_codelist(self, cl1, cl2):
        result = cl1 >>AND>> cl2
        assert isinstance(result, CodeList)
        assert list(result["code"]) == ["E11"]

    def test_not_returns_codelist(self, cl1, cl2):
        result = cl1 >>NOT>> cl2
        assert isinstance(result, CodeList)
        assert set(result["code"]) == {"J45", "E10"}

    def test_or_with_mixed_types_returns_codelist(self):
        a = CodeList([{"code": "J45", "description": "Asthma", "code_type": "icd10"}])
        b = CodeList([{"code": "73211009", "description": "Diabetes", "code_type": "sct"}])
        result = a >>OR>> b
        assert isinstance(result, CodeList)
        assert len(result) == 2

    def test_combinator_with_two_column_inputs_returns_dataframe(self, df1, df2):
        # df1/df2 lack 'code_type' — _wrap should degrade.
        result = df1 >>OR>> df2
        assert isinstance(result, pd.DataFrame)
        assert not isinstance(result, CodeList)
