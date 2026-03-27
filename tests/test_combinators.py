"""Tests for _combinators.py: Infix OR, AND, NOT operators."""

import pandas as pd
import pytest

from codeminer import OR, AND, NOT


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
