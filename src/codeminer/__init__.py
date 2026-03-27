"""Python client for the CodeMiner clinical code API.

Search strategies may be composed using infix operators::

    DESCRIPTION("diab", type="icd10") >>AND>> (
        CHILDREN("E10", type="icd10") >>OR>> CHILDREN("E11", type="icd10")
    )
"""

__version__ = "0.2.0"

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
from ._codelist import CodeList
from ._combinators import AND, NOT, OR
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
    "CodeList",
    "CodeMinerError",
]
