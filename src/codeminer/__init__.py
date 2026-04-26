"""Python client for the CodeMiner clinical code API.

Search strategies may be composed using infix operators::

    DESCRIPTION("diab", type="icd10") >>AND>> (
        CHILDREN("E10", type="icd10") >>OR>> CHILDREN("E11", type="icd10")
    )
"""

__version__ = "0.2.0"

from ._auth import (
    AuthStrategy,
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
from ._client import (
    ATTRIBUTES_FOR,
    CHILDREN,
    CODES,
    CODES_LIKE,
    DESCRIPTION,
    HAS_ATTRIBUTES,
    MAP,
    N_CHILDREN,
    N_PARENTS,
    PARENTS,
    RELATIONSHIP_TYPES_FROM,
    RELATIONSHIP_TYPES_TO,
    check_api_connection,
    get_codeminer_metadata,
)
from ._combinators import AND, NOT, OR
from ._config import config, with_type
from .exceptions import CodeMinerError

__all__ = [
    "DESCRIPTION",
    "CODES_LIKE",
    "CODES",
    "CHILDREN",
    "N_CHILDREN",
    "PARENTS",
    "N_PARENTS",
    "ATTRIBUTES_FOR",
    "HAS_ATTRIBUTES",
    "RELATIONSHIP_TYPES_FROM",
    "RELATIONSHIP_TYPES_TO",
    "MAP",
    "check_api_connection",
    "get_codeminer_metadata",
    "OR",
    "AND",
    "NOT",
    "config",
    "with_type",
    "CodeMinerError",
    "AuthStrategy",
    "auth_none",
    "auth_dev_user",
    "auth_bearer_token",
    "auth_custom",
    "auth_use",
    "auth_clear",
    "auth_current",
    "auth_describe",
    "default_auth",
]
