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

## Authentication

When the server is running with auth enabled, set a strategy once per session:

```python
from codeminer import auth_use, auth_dev_user, auth_bearer_token

# Dev-user mode (server set with CODEMINER_DEV_AUTH=1)
auth_use(auth_dev_user("username"))

# JWT / bearer token mode (server set with PLUMBER_SECRET)
auth_use(auth_bearer_token("eyJhbGciOi..."))
```

`auth_dev_user()` reads the `CODEMINER_DEV_USER` environment variable when no
`user_id` is passed; if that variable is set, it is also picked up
automatically by `default_auth()` so you don't have to call `auth_use()` at
all. Use `auth_clear()` to drop the session-wide setting and `auth_describe()`
to inspect the active strategy.

## Development

```bash
git clone <repo-url>
cd codeminer-py
poetry install
poetry run pytest
```

## License

MIT
