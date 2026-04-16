# Ruff

This README provides an introduction to using Ruff with the Hiero Python SDK. We use uv to manage the environment and Ruff to replace Pylint, Isort, and Black.

---

## 📋 What Is Ruff?

[Ruff](https://docs.astral.sh/ruff/) is an extremely fast Python linter and formatter written in Rust. It provides near-instant feedback and automatically fixes common errors.

## 🎯 Why Use Ruff?

**Performance:** Near instant feedback, even on large codebases.

**All-in-One:** Replaces `pylint`, `flake8`, `isort`, and `black`.

**Auto-Fixing:** Can automatically fix many lint errors (like unused imports or improper sorting).

**Built-in Formatting:** Provides a unified formatter that follows community standards.

## ⚙️ Installation
We use **uv** to manage the Hiero Python SDK environment. Ruff is included in the `lint` dependency group.

```bash
# Using uv (Recommended)
uv add --dev ruff

# Using pip
pip install ruff

# Using Poetry
poetry add --dev ruff

# Using Conda
conda install -c conda-forge ruff
```
>**TIP!**
>Make sure `ruff` is available in the same virtual environment (`.venv`) you use to run the Hiero SDK. If using **uv**, simply running `uv sync` will set everything up for you automatically.


## ▶️ Usage

### Linting (Checking for errors)

We check for logic bugs, unused variables, and style violations.

```bash
# Check the entire source directory
uv run ruff check src/

# Check a specific folder
uv run ruff check src/hiero_sdk_python/tokens/

# Check a single file
uv run ruff check src/hiero_sdk_python/tokens/token_dissociate_transaction.py

# Check and automatically fix safe errors (like unused imports)
uv run ruff check --fix
```

### Formatting (Cleaning up code)

Automatically fix indentation, spacing, and quotes.
```bash
# Format the entire project
uv run ruff format .

# Format all files in a specific folder
uv run ruff format src/hiero_sdk_python/tokens/

# Format a single file
uv run ruff format src/hiero_sdk_python/tokens/token_dissociate_transaction.py
```

### The "Check Everything" Command

If you want to run both the linter and the formatter check in one go, use:
```bash
uv run ruff check . && uv run ruff format --check .
```

### VS Code Integration (Optional)

1. **Install** the Ruff extension by Astral.
2. **Select Interpreter:** `Ctrl + Shift + P` -> `Python: Select Interpreter` -> Choose the `.venv` created by uv.
3. **Automatic Cleanup:** Add this to your `settings.json` to fix imports and format every time you save:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "always",
      "source.organizeImports.ruff": "always"
    }
  },
  "ruff.native-config": true,
  "ruff.importStrategy": "fromEnvironment"
}
```


## 🛠️ Handling Linting Issues

### Manual vs. Automatic Fixes

Ruff is smart, but it won't change your code if it might break logic.

- **Auto-Fixed:** Unused imports, unsorted imports (Isort-style), and basic whitespace.

- **Manual Action Required:** Complex issues like unused function arguments (`ARG001`), overly complex logic (`C901`), or missing docstrings. You must refactor these yourself based on the terminal output.


### Ignoring Rules (Suppressing Warnings)

Sometimes, a linter rule conflicts with a specific technical requirement. You can tell Ruff to ignore a line using the `# noqa` comment followed by the error code.

```python
# Ignore a specific error on a line
import unused_module  # noqa: F401

# Ignore multiple errors on a line
x = 1 # noqa: E701, F841
```
Each error has a code. You can look up the full details of any code in the [Ruff Documentation](https://docs.astral.sh/ruff/rules/).

> **Global Ignore:** To disable linting for an entire file (e.g., an auto-generated file), add `# ruff: noqa` to the very top

## 📝 Example Output
**When issues are found:**

If Ruff detects violations, it provides the file path, line number, and a specific error code (e.g., ARG001 or I001).
Plaintext

```text
src/hiero_sdk_python/tokens/nft_id.py:14:4: ARG001 Unused function argument: `tokenId`
src/hiero_sdk_python/tokens/token_dissociate_transaction.py:1:1: I001 Import block is un-sorted or un-formatted
Found 2 errors.
```

**When everything is correct (Success):**

If the linter finds no issues, it will exit silently or show a clean summary.

```text
All checks passed! ✨
```
For formatting, Ruff will confirm how many files were modified or left unchanged:

```text
68 files left unchanged
```

---

Happy linting! 🚀
