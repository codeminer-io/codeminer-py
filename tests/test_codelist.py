"""Tests for CodeList class and _as_codelist helper."""

import pandas as pd
import pytest

from codeminer._codelist import CodeList, _as_codelist, _codelist_cols
from codeminer._combinators import AND, OR, NOT


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def icd10_df():
    return pd.DataFrame({
        "code": ["J45", "J45.0", "J45.1"],
        "description": ["Asthma", "Allergic asthma", "Nonallergic asthma"],
        "code_type": ["ICD-10", "ICD-10", "ICD-10"],
    })


@pytest.fixture
def icd10_codelist(icd10_df):
    return CodeList(icd10_df)


@pytest.fixture
def sct_codelist():
    return CodeList({
        "code": ["195967001", "389145006"],
        "description": ["Asthma", "Allergic asthma"],
        "code_type": ["SNOMED CT", "SNOMED CT"],
    })


# ---------------------------------------------------------------------------
# CodeList construction
# ---------------------------------------------------------------------------


class TestCodeListConstruction:
    def test_from_dataframe(self, icd10_df):
        cl = CodeList(icd10_df)
        assert isinstance(cl, CodeList)
        assert isinstance(cl, pd.DataFrame)
        assert len(cl) == 3

    def test_from_dict(self):
        cl = CodeList({
            "code": ["E10"],
            "description": ["Type 1 diabetes"],
            "code_type": ["ICD-10"],
        })
        assert isinstance(cl, CodeList)
        assert len(cl) == 1

    def test_empty_codelist(self):
        cl = CodeList({
            "code": [],
            "description": [],
            "code_type": [],
        })
        assert isinstance(cl, CodeList)
        assert len(cl) == 0


# ---------------------------------------------------------------------------
# code_type property
# ---------------------------------------------------------------------------


class TestCodeType:
    def test_single_type(self, icd10_codelist):
        assert icd10_codelist.code_type == "ICD-10"

    def test_empty_codelist(self):
        cl = CodeList({"code": [], "description": [], "code_type": []})
        assert cl.code_type is None

    def test_no_code_type_column(self):
        cl = CodeList({"code": ["J45"], "description": ["Asthma"]})
        assert cl.code_type is None


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestRepr:
    def test_header_present(self, icd10_codelist):
        r = repr(icd10_codelist)
        assert "CodeList: 3 codes" in r
        assert "Code type: ICD-10" in r

    def test_singular_code(self):
        cl = CodeList({
            "code": ["J45"],
            "description": ["Asthma"],
            "code_type": ["ICD-10"],
        })
        assert "CodeList: 1 code" in repr(cl)

    def test_empty_repr(self):
        cl = CodeList({"code": [], "description": [], "code_type": []})
        r = repr(cl)
        assert "CodeList: 0 codes" in r


# ---------------------------------------------------------------------------
# _as_codelist helper
# ---------------------------------------------------------------------------


class TestAsCodelist:
    def test_wraps_valid_dataframe(self, icd10_df):
        result = _as_codelist(icd10_df)
        assert isinstance(result, CodeList)

    def test_skips_missing_columns(self):
        df = pd.DataFrame({"code": ["J45"], "description": ["Asthma"]})
        result = _as_codelist(df)
        assert not isinstance(result, CodeList)
        assert isinstance(result, pd.DataFrame)

    def test_skips_multiple_code_types(self):
        df = pd.DataFrame({
            "code": ["J45", "195967001"],
            "description": ["Asthma", "Asthma"],
            "code_type": ["ICD-10", "SNOMED CT"],
        })
        result = _as_codelist(df)
        assert not isinstance(result, CodeList)

    def test_wraps_empty_with_correct_columns(self):
        df = pd.DataFrame({"code": [], "description": [], "code_type": []})
        result = _as_codelist(df)
        assert isinstance(result, CodeList)


# ---------------------------------------------------------------------------
# _collect_codes integration
# ---------------------------------------------------------------------------


class TestCollectCodesWithCodeList:
    def test_codelist_infers_type(self, icd10_codelist):
        from codeminer._helpers import _collect_codes

        codes, inferred_type = _collect_codes(icd10_codelist)
        assert codes == ["J45", "J45.0", "J45.1"]
        assert inferred_type == "ICD-10"

    def test_codelist_type_conflict_raises(self, icd10_codelist):
        from codeminer._helpers import _collect_codes

        with pytest.raises(ValueError, match="conflicts"):
            _collect_codes(icd10_codelist, type="SNOMED CT")


# ---------------------------------------------------------------------------
# Combinators preserve CodeList
# ---------------------------------------------------------------------------


class TestCombinatorsPreserveCodeList:
    def test_or_returns_codelist(self, icd10_codelist):
        other = CodeList({
            "code": ["J46"],
            "description": ["Status asthmaticus"],
            "code_type": ["ICD-10"],
        })
        result = icd10_codelist >>OR>> other
        assert isinstance(result, CodeList)
        assert len(result) == 4

    def test_and_returns_codelist(self, icd10_codelist):
        other = CodeList({
            "code": ["J45", "J46"],
            "description": ["Asthma", "Status asthmaticus"],
            "code_type": ["ICD-10", "ICD-10"],
        })
        result = icd10_codelist >>AND>> other
        assert isinstance(result, CodeList)
        assert len(result) == 1
        assert result["code"].iloc[0] == "J45"

    def test_not_returns_codelist(self, icd10_codelist):
        exclude = CodeList({
            "code": ["J45"],
            "description": ["Asthma"],
            "code_type": ["ICD-10"],
        })
        result = icd10_codelist >>NOT>> exclude
        assert isinstance(result, CodeList)
        assert "J45" not in result["code"].values
        assert len(result) == 2

    def test_or_mixed_types_returns_dataframe(self, icd10_codelist, sct_codelist):
        result = icd10_codelist >>OR>> sct_codelist
        # Multiple code_types, so should NOT be a CodeList
        assert not isinstance(result, CodeList)
        assert isinstance(result, pd.DataFrame)
