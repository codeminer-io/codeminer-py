# codeminer-py

Python client library for the CodeMiner clinical code mapping API.

## Overview

`codeminer-py` is a Python wrapper that provides a clean, pythonic interface to the CodeMiner REST API. It enables Python users to access clinical code mapping functionality without needing R.

## Features

- 🐍 **Pure Python**: No R dependencies required
- 🔍 **Code Lookup**: Search and validate clinical codes
- 🔄 **Code Mapping**: Transform between coding systems
- 🌳 **Hierarchical Queries**: Navigate code hierarchies
- 🔐 **Authentication**: Support for customer API tokens
- 📊 **Pandas Integration**: Return results as DataFrames
- ⚡ **Async Support**: Asynchronous API calls available

## Installation

```bash
pip install codeminer
```

Or for development:

```bash
git clone https://github.com/your-org/codeminer-py.git
cd codeminer-py
pip install -e .
```

## Quick Start

```python
from codeminer import CodeMinerClient

# Initialize client (uses public API)
client = CodeMinerClient()

# Look up ICD-10 codes
codes = client.lookup_codes(["I21", "I22"], code_type="icd10")
print(codes)

# Map codes between systems
mapped = client.map_codes(
    codes=["I21.0", "I21.1"], 
    from_system="icd10", 
    to_system="phecode"
)
print(mapped)

# Get child codes
children = client.get_children("I21", code_type="icd10")
print(children)
```

## Customer API Usage

For customer-specific endpoints with authentication:

```python
from codeminer import CodeMinerClient

# Initialize with customer token
client = CodeMinerClient(
    api_key="your-customer-api-token",
    base_url="https://api.codeminer.your-domain.com"
)

# Access customer-specific features
codelists = client.get_codelists()
bulk_results = client.bulk_process(data)
```

## API Reference

### Core Methods

- `lookup_codes(codes, code_type)` - Look up code information
- `map_codes(codes, from_system, to_system)` - Map between coding systems
- `get_children(code, code_type)` - Get child codes in hierarchy
- `get_parents(code, code_type)` - Get parent codes in hierarchy
- `search_descriptions(query, code_type)` - Search by description

### Customer Methods (requires API key)

- `get_codelists()` - List custom codelists
- `create_codelist(name, codes)` - Create new codelist
- `bulk_process(data)` - Process large datasets
- `get_usage_stats()` - Get API usage statistics

## Configuration

Set environment variables:

```bash
export CODEMINER_API_KEY="your-api-key"
export CODEMINER_BASE_URL="https://api.codeminer.your-domain.com"
```

Or configure programmatically:

```python
client = CodeMinerClient(
    api_key="your-api-key",
    base_url="https://api.codeminer.your-domain.com",
    timeout=30,
    retry_attempts=3
)
```

## Development

### Prerequisites
- Python 3.8+
- requests
- pandas
- aiohttp (for async support)

### Setup

```bash
git clone https://github.com/your-org/codeminer-py.git
cd codeminer-py
pip install -e ".[dev]"
```

### Testing

```bash
pytest tests/
```

### Building

```bash
python -m build
```

## Related Projects

- **[codeminer](https://github.com/your-org/codeminer)**: Core R package
- **[codeminer-api](https://github.com/your-org/codeminer-api)**: REST API service
- **[codeminer-app](https://github.com/your-org/codeminer-app)**: Web application

## License

MIT © Alasdair Warwick
