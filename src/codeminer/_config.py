"""Global configuration and context managers for the codeminer client.

Mirrors R's ``options()`` system. Set persistent defaults on the ``config``
singleton, or use ``with_type()`` for temporary overrides::

    import codeminer

    codeminer.config.type = "sct"
    DESCRIPTION("diabetes")  # uses sct

    with codeminer.with_type("bnf"):
        bnf_codes = CODES("0204")  # uses bnf

    MAP(bnf_codes)  # from_type inferred from DataFrame, to_type from config (sct)
"""

from __future__ import annotations

from contextlib import contextmanager


class _Unset:
    """Sentinel for 'argument not provided by caller'."""

    def __repr__(self):
        return "<unset>"

    def __bool__(self):
        return False


_unset = _Unset()


class CodeMinerConfig:
    """Global configuration for the codeminer client.

    Set attributes to change defaults for all subsequent function calls.
    Explicit function arguments always take priority over config values.

    Attributes
    ----------
    type : str | None
        Default code type (e.g. ``"icd10"``, ``"sct"``). Also used as the
        default ``to_type`` for :func:`MAP`, mirroring R's behaviour where
        ``codeminer.code_type`` also sets ``codeminer.map_to``.
    lookup_version : str
        Default lookup table version.
    relationship_version : str
        Default relationship table version.
    map_version : str
        Default mapping table version.
    base_url : str | None
        API base URL. If ``None``, falls back to the ``CODEMINER_BASE_URL``
        environment variable, then ``"http://127.0.0.1:8000"``.
    """

    def __init__(self):
        self.type: str | None = None
        self.lookup_version: str = "latest"
        self.relationship_version: str = "latest"
        self.map_version: str = "latest"
        self.base_url: str | None = None

    def reset(self):
        """Reset all options to their defaults."""
        self.__init__()

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"CodeMinerConfig({attrs})"


config = CodeMinerConfig()


def _resolve(value, config_attr, default=None):
    """Resolve a parameter value: explicit arg > config > default.

    Parameters
    ----------
    value
        The value passed by the caller. If ``_unset``, look up the config.
    config_attr : str
        Attribute name on the ``config`` singleton.
    default
        Fallback if both the caller and config provide no value.

    Returns
    -------
    The resolved value.
    """
    if not isinstance(value, _Unset):
        return value
    config_value = getattr(config, config_attr)
    if config_value is not None:
        return config_value
    return default


@contextmanager
def with_type(type: str):
    """Temporarily set the default code type.

    Mirrors R's ``with_type()`` / ``icd10()`` / ``sct()`` helpers. The
    previous value is restored when the block exits, even on exception.

    Parameters
    ----------
    type : str
        The code type to use within the block.

    Examples
    --------
    >>> with with_type("bnf"):
    ...     bnf_codes = CODES("0204")
    """
    old_type = config.type
    config.type = type
    try:
        yield
    finally:
        config.type = old_type
