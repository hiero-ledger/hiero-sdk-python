# Pylint
This is a markdown file, click Ctrl+Shift+V to view or click open preview.

This README provides an introduction to using Pylint with the Hiero Python SDK.

---

## 📋 What Is Pylint?

[Pylint](https://pylint.pycqa.org/) is a static code analysis tool for Python that checks for programming errors, helps enforce a coding standard, and offers suggestions for refactoring. It parses your code without executing it, analyzing syntax, semantics, and style.
 
## 🎯 Why Use Pylint?
Using Pylint is currently optional but it can help to:

* **Detect Errors**: Catches bugs before runtime.
* **Ensure Consistent Style**: Helps us apply PEP 8 and the team's custom conventions via configuration.
* **Code Quality Metrics**: Provides a maintainability score to track improvements over time.
* **Refactoring Aid**: Highlights unused imports, duplicate code, and other refactoring opportunities.

## ⚙️ Installation
In the project root:

```bash
# Using pip (recommended)
pip install --dev pylint

# Using Poetry
poetry add --dev pylint

# Using Conda
conda install -c conda-forge pylint
```

Make sure that `pylint` is available in the same virtual environment or interpreter you use to run hiero.

## 🛠 Configuration

1. Immediately generate a default pylint configuration file:

   ```bash
   pylint --generate-rcfile > .pylintrc
   ```

2. Open this new file: `.pylintrc` and customize as needed (or leave as defaults).

## ▶️ Running Pylint

### Single File
Write pylint with the path to the file you want to check.
For example:

```bash
pylint src/hiero_sdk_python/tokens/token_dissociate_transaction.py
```

### Entire Package
You can check entire folders or package if desired:

```bash
pylint src/hiero_sdk_python/tokens
pylint src/hiero_sdk_python
```

### VS Code Integration
Pylint can be integrated to become much more user-friendly in VS Code.

#### Install and enable the extension for Pylint:

Search in extensions:
ms-python.pylint

#### Once downloaded, point to a Python interpreter.
Run ⇧⌘P → Python: Select Interpreter and pick the venv or interpreter you’re using. 
Be sure to point to the correct path or add the correct path.

For example, if you're using a venv/virtualenv
source .venv/bin/activate
pip install pylint
Check /location, it should not be: 
Location: /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages
It should be more like:
Location: /Users/../../hedera_sdk_python/.venv/lib/python3.10/site-packages

#### Verify installation in that environment:
```bash
python -m pip show pylint
```

#### Reload:
⌘+Shift+P → type → Developer: Reload Window

Next, in the terminal, in the output section, click the dropdown and select Pylint.

You might need to update settings.json (vscode) with something like:
  // — Pylint extension settings —
  "pylint.enabled": true,
  "pylint.importStrategy": "fromEnvironment",
  "pylint.args": [
    "--rcfile=${workspaceFolder}/hedera_sdk_python/.pylintrc"
    ]


You can also just run through terminal:
```bash
 pylint src/hiero_sdk_python/tokens/token_dissociate_transaction.py
```

## 📝 Example Output

```text
************* Module hiero_sdk_python.tokens.nft_id
src/hiero_sdk_python/tokens/nft_id.py:44:0: C0301: Line too long (112/100) (line-too-long)
src/hiero_sdk_python/tokens/nft_id.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/hiero_sdk_python/tokens/nft_id.py:14:4: C0103: Attribute name "tokenId" doesn't conform to snake_case naming style (invalid-name)
------------------------------------
Your code has been rated at 8.50/10
```

## ✅ Next Steps

* Tweak `.pylintrc` to gradually enable more strict rules.
* Integrate Pylint to your VS code.
* Integrate Pylint into your CI pipeline (GitHub Actions, GitLab CI).
* Combine with other packages.

---

Happy linting! 🚀
