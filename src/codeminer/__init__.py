"""
This is a Python wrapper for the codeminer API.
Search strategies may be composed using the infix operators, e.g.:
`DESCRIPTION("diab", "icd10") >>AND>> (CHILDREN("E10", "icd10") >>OR>> CHILDREN("E11", "icd10"))`
"""

__version__ = "0.1.0"

from .client import DESCRIPTION, CODES, CHILDREN, OR, AND, NOT, CodeMinerError

__all__ = [
    "DESCRIPTION",
    "CODES", 
    "CHILDREN",
    "OR",
    "AND",
    "NOT",
    "CodeMinerError"
]
