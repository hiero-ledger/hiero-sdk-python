# Hiero Python SDK – Running Examples

This guide shows you how to run the example scripts included in the SDK.

---

## Running Examples

From the project root, you can run any example file directly:

```bash
uv run examples/name_of_file.py
```

If they must be run as a module, use:

```bash
uv run -m examples.name_of_module
```

If you are using your own venv, you can also use:
```bash
python examples/name_of_file.py
python -m examples.name_of_module
```

### Optional Dependencies for Examples

Some example scripts (notably those related to Ethereum / EVM functionality) require **optional dependencies** that are not installed by default.

If you encounter import errors related to Ethereum libraries, install the ETH extra before running those examples.

#### Using uv (recommended)

```bash
uv sync --dev --extra eth
```

#### Using pip

```bash
pip install -e ".[eth]"
```

You'll need your environment variables and uv set up as outlined in /README.md [README](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README.md)



