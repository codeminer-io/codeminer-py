# codeminer

Python client for the CodeMiner clinical code API.

## Installation

```bash
poetry add codeminer
```

## Quick Start

```python
from codeminer import DESCRIPTION, CODES, CHILDREN, MAP, AND, OR, NOT

# Search by description
asthma_codes = DESCRIPTION("asthma", type="ICD-10")

# Look up specific codes
codes = CODES("J45", "E11", type="ICD-10")

# Navigate hierarchies
children = CHILDREN("73211009", type="SNOMED CT")

# Map between coding systems
mapped = MAP("J45", from_type="ICD-10", to_type="SNOMED CT")

# Compose search strategies with infix operators
diabetes = DESCRIPTION("diabet", type="ICD-10") >>AND>> (
    CHILDREN("E10", type="ICD-10") >>OR>> CHILDREN("E11", type="ICD-10")
)
```

## Configuration

The API base URL is resolved in this order:

1. Explicit `base_url` parameter on each function call
2. `CODEMINER_BASE_URL` environment variable
3. Default: `http://127.0.0.1:8000`

```python
from codeminer import check_api_connection

check_api_connection()
```

## Development

```bash
git clone <repo-url>
cd codeminer-py
poetry install
poetry run pytest
```

## License

MIT
