"""Tests for _auth.py and auth wiring through _api_request."""

import json
from unittest.mock import MagicMock, patch

import pytest

from codeminer import (
    CODES,
    CodeMinerError,
    auth_bearer_token,
    auth_clear,
    auth_current,
    auth_custom,
    auth_describe,
    auth_dev_user,
    auth_none,
    auth_use,
    default_auth,
)
from codeminer._auth import AuthStrategy


def _make_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(data)
    mock.json.return_value = data
    return mock


@pytest.fixture(autouse=True)
def _reset_auth(monkeypatch):
    """Each test starts with no session-wide strategy and no env override."""
    monkeypatch.delenv("CODEMINER_DEV_USER", raising=False)
    auth_clear()
    yield
    auth_clear()


class TestAuthDevUser:
    def test_attaches_x_dev_user_header(self):
        strategy = auth_dev_user("alasdair")
        kwargs = strategy({"headers": {}})
        assert kwargs["headers"]["X-Dev-User"] == "alasdair"

    def test_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.setenv("CODEMINER_DEV_USER", "from-env")
        strategy = auth_dev_user()
        kwargs = strategy({"headers": {}})
        assert kwargs["headers"]["X-Dev-User"] == "from-env"

    def test_no_op_when_user_id_blank(self):
        strategy = auth_dev_user("")
        kwargs = strategy({"headers": {}})
        assert "X-Dev-User" not in kwargs["headers"]

    def test_creates_headers_dict_if_missing(self):
        strategy = auth_dev_user("alice")
        kwargs = strategy({})
        assert kwargs["headers"]["X-Dev-User"] == "alice"


class TestAuthBearer:
    def test_attaches_authorization_header(self):
        strategy = auth_bearer_token("abc.def.ghi")
        kwargs = strategy({"headers": {}})
        assert kwargs["headers"]["Authorization"] == "Bearer abc.def.ghi"


class TestAuthCustom:
    def test_wraps_callable(self):
        def add_header(req):
            req.setdefault("headers", {})["X-Test"] = "1"
            return req

        strategy = auth_custom(add_header, description="test strategy")
        assert isinstance(strategy, AuthStrategy)
        assert strategy.description == "test strategy"
        kwargs = strategy({"headers": {}})
        assert kwargs["headers"]["X-Test"] == "1"


class TestAuthUse:
    def test_sets_session_wide_strategy(self):
        strategy = auth_dev_user("alice")
        auth_use(strategy)
        assert auth_current() is strategy

    def test_clear_resets_to_default(self):
        auth_use(auth_dev_user("alice"))
        auth_clear()
        assert auth_current().kind == "none"

    def test_wraps_bare_callable(self):
        def custom(req):
            return req

        wrapped = auth_use(custom)
        assert isinstance(wrapped, AuthStrategy)
        assert wrapped.kind == "custom"

    def test_rejects_non_callable(self):
        with pytest.raises(TypeError):
            auth_use("not a callable")


class TestDefaultAuth:
    def test_returns_none_when_env_unset(self):
        assert default_auth().kind == "none"

    def test_returns_dev_user_when_env_set(self, monkeypatch):
        monkeypatch.setenv("CODEMINER_DEV_USER", "alasdair")
        strategy = default_auth()
        assert strategy.kind == "dev_user"
        kwargs = strategy({"headers": {}})
        assert kwargs["headers"]["X-Dev-User"] == "alasdair"


class TestAuthDescribe:
    def test_describes_active_strategy(self):
        auth_use(auth_dev_user("alice"))
        assert "alice" in auth_describe()

    def test_describes_explicit_strategy(self):
        assert auth_describe(auth_none()) == "No authentication"


class TestAuthAppliedToRequest:
    """End-to-end: auth_use() sets a strategy, and _api_request applies it."""

    def test_dev_user_header_sent_on_post(self, success_response):
        auth_use(auth_dev_user("alasdair"))
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock_post:
            CODES("J45", type="icd10")
            sent_headers = mock_post.call_args.kwargs["headers"]
            assert sent_headers["X-Dev-User"] == "alasdair"

    def test_no_auth_header_when_strategy_is_none(self, success_response):
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(success_response),
        ) as mock_post:
            CODES("J45", type="icd10")
            sent_headers = mock_post.call_args.kwargs["headers"]
            assert "X-Dev-User" not in sent_headers
            assert "Authorization" not in sent_headers


class TestUnauthorizedErrorDisplay:
    """The plumber auth filter returns ``{'error': ['Unauthorized']}`` (a
    bare list, not the structured shape the regular endpoints use). That used
    to crash _raise_api_error with AttributeError. Verify it now produces a
    clean CodeMinerError."""

    def test_401_unauthorized(self):
        unauthorized = {"error": ["Unauthorized"]}
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(unauthorized, status_code=401),
        ):
            with pytest.raises(CodeMinerError) as exc_info:
                CODES("J45", type="icd10")
            assert "Unauthorized" in str(exc_info.value)
            assert exc_info.value.error_type == "http_401"

    def test_string_error_payload(self):
        payload = {"error": "boom"}
        with patch(
            "codeminer._helpers.requests.post",
            return_value=_make_response(payload, status_code=500),
        ):
            with pytest.raises(CodeMinerError) as exc_info:
                CODES("J45", type="icd10")
            assert "boom" in str(exc_info.value)
