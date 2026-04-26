"""Tests for the CodeList class (mirrors R codeminer_codelist)."""

import pickle

import pandas as pd
import pytest

from codeminer import CodeList


# ---------------------------------------------------------------------------
# Construction & class identity
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_construct_from_dict_succeeds(self):
        cl = CodeList({
            "code": ["J45"],
            "description": ["Asthma"],
            "code_type": ["icd10"],
        })
        assert isinstance(cl, CodeList)
        assert isinstance(cl, pd.DataFrame)
        assert len(cl) == 1

    def test_construct_from_records_succeeds(self):
        cl = CodeList([
            {"code": "J45", "description": "Asthma", "code_type": "icd10"},
            {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        ])
        assert list(cl["code"]) == ["J45", "E11"]

    def test_construct_lenient_with_missing_columns(self):
        # Mirrors R's as_codelist: construction does not validate.
        # Use validate() (strict) or _wrap() (column-presence) for checks.
        cl = CodeList({"code": ["J45"], "description": ["Asthma"]})
        assert isinstance(cl, CodeList)

    def test_construct_empty_frame(self):
        # Pandas internals construct empty intermediates; must not raise.
        assert isinstance(CodeList(), CodeList)
        assert isinstance(CodeList(pd.DataFrame()), CodeList)

    def test_construct_allows_mixed_code_types(self):
        # Lenient: __init__ does not reject mixed types (R's as_codelist
        # behaviour). Only validate() rejects.
        cl = CodeList({
            "code": ["J45", "73211009"],
            "description": ["Asthma", "Diabetes"],
            "code_type": ["icd10", "sct"],
        })
        assert len(cl) == 2


# ---------------------------------------------------------------------------
# Repr (mirrors R print.codeminer_codelist)
# ---------------------------------------------------------------------------


class TestRepr:
    def test_repr_single_type(self):
        cl = CodeList([
            {"code": "J45", "description": "Asthma", "code_type": "icd10"},
            {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        ])
        text = repr(cl)
        assert "<CodeList: 2 codes>" in text
        assert 'Code type: "icd10"' in text

    def test_repr_singular_one_code(self):
        cl = CodeList([{"code": "J45", "description": "Asthma", "code_type": "icd10"}])
        assert "<CodeList: 1 code>" in repr(cl)
        assert "1 codes>" not in repr(cl)

    def test_repr_mixed_types_omits_code_type_line(self):
        cl = CodeList({
            "code": ["J45", "73211009"],
            "description": ["Asthma", "Diabetes"],
            "code_type": ["icd10", "sct"],
        })
        text = repr(cl)
        assert "<CodeList: 2 codes>" in text
        assert "Code type:" not in text

    def test_repr_empty(self):
        cl = CodeList()
        assert "<CodeList: 0 codes>" in repr(cl)

    def test_repr_html_includes_header(self):
        cl = CodeList([{"code": "J45", "description": "Asthma", "code_type": "icd10"}])
        html = cl._repr_html_()
        assert "CodeList: 1 code" in html
        assert 'Code type: &quot;icd10&quot;' in html or 'Code type: "icd10"' in html


# ---------------------------------------------------------------------------
# Constructor propagation
# ---------------------------------------------------------------------------


class TestConstructorPropagation:
    @pytest.fixture
    def cl(self):
        return CodeList([
            {"code": "J45", "description": "Asthma", "code_type": "icd10"},
            {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        ])

    def test_copy_preserves_type(self, cl):
        assert isinstance(cl.copy(), CodeList)

    def test_loc_preserves_type(self, cl):
        result = cl.loc[cl["code"] == "J45"]
        assert isinstance(result, CodeList)
        assert len(result) == 1

    def test_pickle_roundtrip(self, cl):
        round_tripped = pickle.loads(pickle.dumps(cl))
        assert isinstance(round_tripped, CodeList)
        assert list(round_tripped["code"]) == ["J45", "E11"]


# ---------------------------------------------------------------------------
# _wrap factory
# ---------------------------------------------------------------------------


class TestWrap:
    def test_wrap_returns_codelist_when_columns_present(self):
        df = pd.DataFrame([{"code": "J45", "description": "Asthma", "code_type": "icd10"}])
        result = CodeList._wrap(df)
        assert isinstance(result, CodeList)

    def test_wrap_returns_dataframe_when_columns_missing(self):
        df = pd.DataFrame([{"table_name": "icd10_lookup", "code_type": "icd10", "version": "2024"}])
        result = CodeList._wrap(df)
        assert isinstance(result, pd.DataFrame)
        assert not isinstance(result, CodeList)


# ---------------------------------------------------------------------------
# validate() — mirrors R validate_codeminer_codelist
# ---------------------------------------------------------------------------


class TestValidate:
    def test_validate_returns_unique_code_type_on_success(self):
        cl = CodeList([
            {"code": "J45", "description": "Asthma", "code_type": "icd10"},
            {"code": "E11", "description": "Type 2 DM", "code_type": "icd10"},
        ])
        assert cl.validate() == "icd10"

    def test_validate_rejects_mixed_code_types(self):
        cl = CodeList({
            "code": ["J45", "73211009"],
            "description": ["Asthma", "Diabetes"],
            "code_type": ["icd10", "sct"],
        })
        with pytest.raises(ValueError, match="one unique value"):
            cl.validate()

    def test_validate_rejects_na_in_required_columns(self):
        cl = CodeList({
            "code": ["J45", "E11"],
            "description": ["Asthma", None],
            "code_type": ["icd10", "icd10"],
        })
        with pytest.raises(ValueError, match="missing values"):
            cl.validate()

    def test_validate_rejects_non_string_columns(self):
        # Build via plain DataFrame then re-wrap so we bypass __init__'s
        # column-presence check (which it would still pass).
        df = pd.DataFrame({
            "code": [1, 2],  # ints, not strings
            "description": ["a", "b"],
            "code_type": ["icd10", "icd10"],
        })
        cl = CodeList(df)
        with pytest.raises(ValueError, match="character"):
            cl.validate()
