"""Auth strategies for the codeminer client.

Mirrors the R ``codeminer.api`` package's ``auth.R``. A "strategy" is a
callable that receives the kwargs about to be passed to ``requests.request()``
and may mutate them (typically by adding headers). The ``auth_*()`` factories
below return such callables, wrapped with metadata for printing and
introspection.

Set a session-wide strategy with :func:`auth_use`; per-call overrides via the
``auth`` parameter on ``_api_request`` still take precedence.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

RequestKwargs = dict
Strategy = Callable[[RequestKwargs], RequestKwargs]


class AuthStrategy:
    """A request modifier wrapped with kind/description metadata.

    Instances are callable: ``strategy(request_kwargs) -> request_kwargs``.
    """

    def __init__(self, fn: Strategy, kind: str, description: str):
        if not callable(fn):
            raise TypeError("Strategy fn must be callable.")
        self.fn = fn
        self.kind = kind
        self.description = description

    def __call__(self, request_kwargs: RequestKwargs) -> RequestKwargs:
        return self.fn(request_kwargs)

    def __repr__(self) -> str:
        return (
            f"<AuthStrategy kind={self.kind!r} "
            f"description={self.description!r}>"
        )


def auth_none() -> AuthStrategy:
    """Strategy that leaves the request unchanged."""
    return AuthStrategy(
        fn=lambda req: req,
        kind="none",
        description="No authentication",
    )


def auth_dev_user(user_id: Optional[str] = None) -> AuthStrategy:
    """Attach an ``X-Dev-User`` header.

    Only useful when the server is running with ``CODEMINER_DEV_AUTH=1``
    (development setups).

    Parameters
    ----------
    user_id : str | None
        User identifier. If ``None``, falls back to the
        ``CODEMINER_DEV_USER`` environment variable. If both are empty, the
        strategy is a no-op.

    Examples
    --------
    >>> auth_use(auth_dev_user("username"))
    """
    if user_id is None:
        user_id = os.environ.get("CODEMINER_DEV_USER", "")

    def _apply(req: RequestKwargs) -> RequestKwargs:
        if not user_id:
            return req
        headers = req.setdefault("headers", {})
        headers["X-Dev-User"] = user_id
        return req

    description = (
        f"Dev user '{user_id}' (X-Dev-User header)"
        if user_id
        else "Dev user (inactive — CODEMINER_DEV_USER not set)"
    )
    return AuthStrategy(fn=_apply, kind="dev_user", description=description)


def auth_bearer_token(token: str) -> AuthStrategy:
    """Attach an ``Authorization: Bearer <token>`` header (JWT mode)."""

    def _apply(req: RequestKwargs) -> RequestKwargs:
        headers = req.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return req

    return AuthStrategy(
        fn=_apply,
        kind="bearer",
        description="Bearer token (Authorization header)",
    )


def auth_custom(
    fn: Strategy, description: str = "Custom auth strategy"
) -> AuthStrategy:
    """Wrap an arbitrary request-modifier as a strategy with metadata."""
    return AuthStrategy(fn=fn, kind="custom", description=description)


_current_strategy: Optional[AuthStrategy] = None


def auth_use(strategy) -> AuthStrategy:
    """Set the auth strategy used by all subsequent API calls.

    A bare callable is wrapped as a custom strategy automatically.
    """
    global _current_strategy
    if not callable(strategy):
        raise TypeError("strategy must be callable.")
    if not isinstance(strategy, AuthStrategy):
        strategy = auth_custom(strategy)
    _current_strategy = strategy
    return strategy


def auth_clear() -> None:
    """Remove any session-wide setting; falls back to :func:`default_auth`."""
    global _current_strategy
    _current_strategy = None


def default_auth() -> AuthStrategy:
    """Resolve the fallback strategy when nothing has been set with auth_use().

    Returns :func:`auth_dev_user` if ``CODEMINER_DEV_USER`` is set in the
    environment, otherwise :func:`auth_none`.
    """
    if os.environ.get("CODEMINER_DEV_USER", ""):
        return auth_dev_user()
    return auth_none()


def auth_current() -> AuthStrategy:
    """Return the strategy that the next API call would use."""
    return _current_strategy or default_auth()


def auth_describe(strategy: Optional[AuthStrategy] = None) -> str:
    """Human-readable description of a strategy (defaults to current)."""
    s = strategy if strategy is not None else auth_current()
    return getattr(s, "description", "Custom auth strategy (no description)")
