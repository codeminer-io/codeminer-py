# codeminer

<!-- badges: start -->
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
<!-- badges: end -->

Python client for the [CodeMiner](https://github.com/codeminer-io/codeminer) REST
API. Search clinical coding systems such as ICD-10, SNOMED CT, Read codes and
BNF, walk their hierarchies, map between them, and build codelists as pandas
data frames.

This package is alpha software, so its interface may change between releases.

## Installation

Requires Python 3.10 or later.

```bash
uv add codeminer
```

Or with pip:

```bash
pip install codeminer
```

For the latest development version, install from GitHub:

```bash
pip install git+https://github.com/codeminer-io/codeminer-py
```

## Connecting to a server

The client holds no clinical code data. Every call goes to a CodeMiner API
server, so you need one to query.

**If you have a server URL**, set it before making any calls:

```bash
export CODEMINER_BASE_URL="https://your-server.example.org"
```

**If you don't**, run one locally with dummy data. This needs R and takes a few
lines, using [codeminer.api](https://github.com/codeminer-io/codeminer.api):

```r
# install.packages("pak")
pak::pak("codeminer-io/codeminer.api")

codeminer::create_dummy_database()
codeminer.api::run_codeminer_api()
```

The server listens on `http://127.0.0.1:8000`, which is the client's default.
Leave it running and check the connection from Python:

```python
from codeminer import check_api_connection

check_api_connection()
```

The dummy database is a small sample for trying things out, so don't use it for
real codelists. It has no SNOMED CT. To build a full database, see the
[codeminer documentation](https://codeminer-io.github.io/codeminer/).

## Quick start

```python
from codeminer import CHILDREN, CODES, CODES_LIKE, DESCRIPTION, MAP, PARENTS

# Search descriptions with a regular expression
asthma = DESCRIPTION("asthma", type="ICD-10")

# Search the codes themselves
e11 = CODES_LIKE("^E11", type="ICD-10")

# Look up specific codes
codes = CODES("J45", "E11", type="ICD-10")

# A code and all of its descendants
t2dm = CHILDREN("E11", type="ICD-10")

# A code and all of its ancestors
ancestors = PARENTS("E113", type="ICD-10")

# Map between coding systems
mapped = MAP("4939", from_type="ICD-9", to_type="ICD-10")
```

`N_CHILDREN()` and `N_PARENTS()` do the same as `CHILDREN()` and `PARENTS()`, but
stop after a set number of levels. Results include the codes you started from.

```python
from codeminer import N_CHILDREN

N_CHILDREN("E11", depth=1, type="ICD-10")
```

`get_relationship_tree()` returns a hierarchy as `nodes` and `edges` data frames.

For systems with attribute relationships, such as SNOMED CT, use
`ATTRIBUTES_FOR()`, `HAS_ATTRIBUTES()`, `RELATIONSHIP_TYPES()`,
`RELATIONSHIP_TYPES_FROM()` and `RELATIONSHIP_TYPES_TO()`.

## Code types

The `type` argument must match a code type on the server exactly, for example
`"ICD-10"` or `"SNOMED CT"`. Ask the server what it offers, because this depends
on how its database was built:

```python
from codeminer import get_codeminer_metadata

get_codeminer_metadata("lookup")[["code_type", "lookup_version"]]
get_codeminer_metadata("mapping")[["from_code_type", "to_code_type"]]
```

Pass `"relationship"` for the hierarchies, or no argument to get all three as a
dictionary.

ICD codes are stored without dots, so use `E113` rather than `E11.3`. `MAP()`
needs a mapping table in either direction between the two code types. Codes
missing from that table are left out of the result, with a warning.

## Working with results

Query functions return a `CodeList`, a `pandas.DataFrame` subclass with `code`,
`description` and `code_type` columns. Anything that works on a data frame works
here.

```python
from codeminer import CHILDREN, DESCRIPTION

asthma = DESCRIPTION("asthma", type="ICD-10")

asthma.to_csv("asthma.csv", index=False)

CHILDREN(asthma)   # `type` is taken from the code_type column
asthma.validate()  # returns "ICD-10", or raises ValueError if the list is invalid
```

`validate()` checks that the required columns are present and hold strings, that
they have no missing values, and that there is a single code type. Dropping a
required column leaves a `CodeList` that can't pass these checks.

## Combining code lists

Use `>>OR>>`, `>>AND>>` and `>>NOT>>` to union, intersect and subtract results of
the same code type:

```python
from codeminer import AND, CHILDREN, DESCRIPTION, NOT, OR

# Diabetes codes under E10 or E11
diabetes = DESCRIPTION("diabet", type="ICD-10") >>AND>> (
    CHILDREN("E10", type="ICD-10") >>OR>> CHILDREN("E11", type="ICD-10")
)

# Without ketoacidosis
diabetes >>NOT>> DESCRIPTION("ketoacidosis", type="ICD-10")
```

## Configuration

Set defaults on `config` to avoid repeating arguments. Explicit arguments always
take priority.

```python
import codeminer
from codeminer import CODES, DESCRIPTION, MAP, with_type

codeminer.config.type = "ICD-10"
DESCRIPTION("asthma")

# `MAP()` has its own defaults
codeminer.config.map_from = "ICD-9"
codeminer.config.map_to = "ICD-10"
MAP("4939")

# Switch code type for a block. This also sets the `MAP()` target.
with with_type("ICD-9"):
    CODES("4939")

codeminer.config.reset()
```

| Option | Default | Description |
|---|---|---|
| `type` | `None` | Code type, not used by `MAP()` |
| `map_from`, `map_to` | `None` | Source and target code types for `MAP()` |
| `lookup_version` | `"latest"` | Lookup table version |
| `relationship_version` | `"latest"` | Relationship table version |
| `map_version` | `"latest"` | Mapping table version |
| `base_url` | `None` | API server URL |

The server URL is resolved in this order:

1. The `base_url` argument on a function call
2. `config.base_url`
3. The `CODEMINER_BASE_URL` environment variable
4. `http://127.0.0.1:8000`

## Authentication

If your server requires authentication, set a strategy once per session:

```python
from codeminer import auth_bearer_token, auth_dev_user, auth_use

# A JSON Web Token
auth_use(auth_bearer_token("your-token"))

# A development server's user header
auth_use(auth_dev_user("username"))
```

`auth_dev_user()` with no argument reads the `CODEMINER_DEV_USER` environment
variable. If that variable is set, the client uses it without calling
`auth_use()`. Use `auth_describe()` to see the active strategy, `auth_clear()` to
remove it, and `auth_custom()` to supply your own.

## Errors and warnings

Failed requests raise `CodeMinerError`, including connection failures and unknown
code types. Warnings and messages from the server are printed to stderr.

```python
from codeminer import CodeMinerError, DESCRIPTION

try:
    DESCRIPTION("asthma", type="not-a-code-type")
except CodeMinerError as e:
    print(e)
```

## Development

```bash
git clone https://github.com/codeminer-io/codeminer-py.git
cd codeminer-py
uv sync
uv run pytest
```

The tests in `tests/test_spec_sync.py` compare the client with a running API
server, and they are skipped if none is available.

## Related projects

- [codeminer](https://github.com/codeminer-io/codeminer): the R package that
  builds and queries the database.
- [codeminer.api](https://github.com/codeminer-io/codeminer.api): the REST API
  server.

## Licence

This client is released under the [MIT Licence](https://github.com/codeminer-io/codeminer-py/blob/main/LICENSE). The API server and
clinical code data have their own terms, and much of that data is licensed by its
publishers.
