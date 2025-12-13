---
description: Repository Information Overview
alwaysApply: true
---

# hiero-sdk-python Information

## Summary
A Hiero SDK in pure Python for interacting with the Hedera Hashgraph platform. It allows developers to interact with the Hedera network, including managing accounts, tokens, smart contracts, and files.

## Structure
- **src/hiero_sdk_python**: Main source code for the SDK, organized by functionality (account, contract, token, etc.).
- **tests**: Contains `unit` and `integration` tests.
- **examples**: Ready-to-run example scripts demonstrating various SDK operations.
- **docs**: Documentation for SDK users and developers.
- **.github**: CI/CD workflows and templates.

## Language & Runtime
**Language**: Python
**Version**: >=3.10, <3.14
**Build System**: pdm (backend), setuptools
**Package Manager**: pip, uv (for dev/tests)

## Dependencies
**Main Dependencies**:
- grpcio-tools
- protobuf
- grpcio
- cryptography
- python-dotenv
- requests
- pycryptodome
- eth-abi
- rlp
- eth-keys

**Development Dependencies**:
- pytest
- ruff
- mypy
- typing-extensions

## Build & Installation
```bash
# Install from PyPI
pip install hiero-sdk-python

# Install for development
pip install -e .
```

## Testing

**Framework**: pytest
**Test Location**: `tests/` (split into `unit` and `integration`)
**Configuration**: `pytest.ini`, `pyproject.toml`

**Run Command**:

```bash
uv run pytest
```

## Validation

**Linting**: ruff, mypy
**Configuration**: `pyproject.toml`, `mypy.ini`
