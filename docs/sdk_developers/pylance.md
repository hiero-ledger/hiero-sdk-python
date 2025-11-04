# Pylance: Improving Code Quality for Hiero SDK Developers



## Table of Contents

1. [Introduction](#introduction)

2. [Why Pylance Matters for Hiero SDK](#why-pylance-matters-for-hiero-sdk)

3. [Setting Up Pylance in VS Code](#setting-up-pylance-in-vs-code)

4. [Common Errors and What They Mean](#common-errors-and-what-they-mean)

5. [Fixing Invalid Imports and Calls](#fixing-invalid-imports-and-calls)

6. [Recommended Settings](#recommended-settings)

7. [Good Practices for Contributors](#good-practices-for-contributors)

8. [Summary](#summary)



---



## Introduction



When developing for the **Hiero Python SDK**, contributors must ensure their code is syntactically correct *and* references real functions, classes, and modules that exist in the SDK.



Many contributors unintentionally use:

- Invalid imports (modules or files that don’t exist)

- Function or class names that were misspelled or never defined

- Incorrect parameter names in constructors or methods



Such code **looks fine** visually but **fails to run or even pass tests**, making reviews difficult.



To fix this, we recommend using **Pylance** — a static analysis and type-checking tool built into **Visual Studio Code (VS Code)** that instantly shows errors and warnings *before* runtime.



---



## Why Pylance Matters for Hiero SDK



Pylance improves your development experience by:



- **Highlighting non-existent functions, parameters, and attributes**

  - e.g., using `minimum_amount` instead of `min_amount`

- **Flagging incorrect imports**

  - e.g., importing `hedera.account_id` instead of `hiero_sdk.account_id`

- **Revealing inaccessible private methods**

  - e.g., calling `_internal_method()` outside its intended class

- **Catching inconsistent types or unused variables**



This feedback loop saves time for both **you and the maintainers**, ensuring your PR is *ready for review* and runs correctly.



---



## Setting Up Pylance in VS Code



Follow these steps to enable Pylance in your local environment.



### 1. Install VS Code

If you haven’t already, download it from [https://code.visualstudio.com/](https://code.visualstudio.com/).



### 2. Install the Pylance Extension

1. Open VS Code.

2. Go to **Extensions** (Ctrl+Shift+X or Cmd+Shift+X on Mac).

3. Search for **“Pylance”**.

4. Click **Install**.



### 3. Verify Python Environment

Make sure your workspace is using the correct Python environment:

- Open the Command Palette → “Python: Select Interpreter”

- Choose your environment (e.g., `.venv`, `conda`, or global python)



### 4. Enable Pylance as Default Language Server

Go to your workspace settings (`.vscode/settings.json`) and add:



```json

{
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true
}

````



> 💡 You can also set `"python.analysis.typeCheckingMode": "strict"` for deeper checking, but “basic” is recommended for contributors.



---



## Common Errors and What They Mean



Let’s look at a real-world Hiero SDK example.



```python

CustomFractionalFee(
    numerator=numerator,
    denominator=denominator,
    minimum_amount=min_amount,
    maximum_amount=max_amount,
)

```



### Wrong Pylance output:



```

No parameter named "minimum_amount"
No parameter named "maximum_amount"

```



This means `minimum_amount` and `maximum_amount` **do not exist** in the constructor definition of `CustomFractionalFee`.



### Correct Usage:



Check the source definition:



```python

class CustomFractionalFee(CustomFee):
    def __init__(
        self,
        numerator: int = 0,
        denominator: int = 1,
        min_amount: int = 0,
        max_amount: int = 0,
        ...
    ):

```



So, you should instead write:



```python

CustomFractionalFee(
    numerator=numerator,
    denominator=denominator,
    min_amount=min_amount,
    max_amount=max_amount,
)

```


---

## Fixing Invalid Imports and Calls

Pylance is especially helpful when you import something that doesn’t exist — or when the import path changes depending on which folder you’re working from.

Example 1 — When working **inside `/src`**:

```python
from hiero_sdk.account.account_id import AccountId
```

Example 2 — When working **inside `/examples`**:

```python
from hiero_sdk_python import AccountId
```

> ✅ Both imports are correct.
> Use the first one when developing inside the SDK source (`/src`),
> and the second when writing or testing example scripts (`/examples`).

If you mix up these contexts, Pylance will display an error such as:

```
Import "hiero_sdk_python.account.account_id" could not be resolved
```

Using Pylance helps you catch such mismatched imports early and ensures your code runs correctly in its intended environment.

---


## Recommended Settings



Here’s a recommended configuration for Hiero SDK contributors:



```json

{
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,
  "editor.formatOnSave": true
}
```



### Advanced Settings (Optional)

For experienced contributors who want deeper code analysis and stricter checks, you can enable the following settings:

```json
{
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.autoImportCompletions": true,
  "editor.formatOnSave": true
}
````

**Explanation:**

* `"python.analysis.diagnosticMode": "workspace"` — runs analysis on your entire workspace, not just open files (may produce many warnings).
* `"python.analysis.typeCheckingMode": "strict"` — enables deeper static analysis and stricter type enforcement.
* `"python.analysis.autoImportCompletions": true` — automatically suggests imports when typing symbol names.

> ⚠️ Use these only if you're comfortable handling a larger number of warnings.



---



## Good Practices for Contributors



1. **Always fix all visible Pylance errors** before making a Pull Request.

2. **Hover over** red underlines to read error messages.

3. **Jump to definition** using Ctrl + Click (or Cmd + Click on Mac).

4. **Avoid “undefined” imports or attributes** — double-check class definitions.

5. **Run tests locally** after resolving Pylance errors.

6. **Keep your branch rebased** with `main` to prevent outdated references.



---



## Summary



Using Pylance helps maintain:



* Clean, correct, and understandable code

* Accurate imports and method calls

* Faster reviews and higher merge chances



Before every PR:



* ✅ Run Pylance checks

* ✅ Fix all highlighted issues

* ✅ Sign and document your commits



---



## References



* [VS Code Pylance Documentation](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)

* [Hiero SDK Contributing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/CONTRIBUTING.md)

* [Hiero SDK CHANGELOG](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/CHANGELOG.md)





---





