# Bandit

This README provides an introduction to using Bandit with the Hiero Python SDK. We use uv to manage the environment and Bandit to handle static security analysis and vulnerability scanning.

## What Is Bandit?

[Bandit](https://bandit.readthedocs.io/en/latest/) is a security-focused static analysis tool designed to find common security vulnerabilities and flaws in Python code.

## 🎯 Why Use Bandit?

**Vulnerability Detection:** Catches critical security flaws like hardcoded passwords, shell injections, weak cryptography, and unsafe serialization.

**Fine-Grained Severity Rules:** Categorizes threats into Low, Medium, and High severities to establish structural pass/fail criteria.


## ⚙️ Installation

We use **uv** to manage the Hiero Python SDK environment. Bandit is included in the `lint` dependency group.

### The Recommended Way (Using uv)
The below command will simply pull down the latest dependencies and synchronize your local environment in one step:
```bash
uv sync
```

### Alternative Installation Layouts

If you need to install Bandit manually into an alternate isolated setup or are using a different environment manager, use the corresponding configuration below:
```bash
# Explicitly add to the development group via uv
uv add --group lint bandit

# Using classic pip inside an active virtualenv
pip install bandit

# Using Poetry
poetry add --group lint bandit

# Using Conda
conda install -c conda-forge bandit
```
> [!TIP]
> Make sure `bandit` is available in the same virtual environment (`.venv`) you use to run the Hiero SDK. If using **uv**, simply running `uv sync` will set everything up for you automatically.

## ▶️ Usage

### Manual Checking for vulnerabilities

We run security checks against our package source paths and active development scripts.

```bash
# Check the entire source directory recursively
uv run bandit -c bandit.yml -r src/

# Check multiple active development folders together
uv run bandit -c bandit.yml -r src/ tck/ tests/

# Run with custom thresholds
uv run bandit -c bandit.yml -l -r src/

# Run checks and generate a clean text log report file
uv run bandit -c bandit.yml -r src/ --format txt --output bandit_report.txt
```

### Run using Pre-Commit Hook

If you want to run the Bandit using the `pre-commit` configuration, use:

```bash
uv run pre-commit run --all-files
```

## 🛠️ Handling Security Issues

###  How Severity Levels Affect Commits
Unlike code formatters, Bandit will never modify your code automatically. Security risks must be reviewed and patched manually based on their tier:

- **Low Severity (Warnings):** Issues like public parameter keywords triggering hardcoded credential filters (`B106`) or standard pseudo-random generators (`B311`) or any other low severity issue print directly to your screen as warnings, but will not block your commit.

- **Medium & High Severity (Blockers):** High-risk flaws like deprecated cryptographic libraries (`B413`), exposed keys, or command injections throw a failure execution code and instantly halt your commit.

### Inline Suppressions (`# nosec`)

Sometimes an abstract pattern triggers a false positive that has been reviewed and verified as safe. You can silence individual lines using the inline `# nosec` statement followed by the specific issue ID.

```python
# Suppress alerts for executing a fixed, safe system command
import subprocess
subprocess.Popen(["/bin/ls", "-l"], shell=False)  # nosec B602, B607

# Tell Bandit this specific assert statement is intentional and safe
assert user_role == "admin"  # nosec B101
```

### Targeted Rule Suppressions
Instead of disabling a rule globally or littering your files with `# nosec` comments, you can use Bandit's plugin-specific configuration blocks to skip rules for matching file patterns.

```yml
# bandit.yml

# Global directory exclusions
exclude_dirs: ['.clusterfuzzlite/**']

# Targeted plugin rule overrides
assert_used:
  skips:
    - '**/tests/**/*.py'

exec_used:
  skips:
    - '**/tests/mocks/**/*.py'
```

**Global Suppressions:** If a specific rule is completely irrelevant to entire codebase, do not add `# nosec` everywhere. Instead, permanently drop it by adding the error code to the `skips` list inside `bandit.yml` file.

```yml
skips: ["B101", "B601", "B413"]
```

## 📝 Example Output

### When structural vulnerabilities are found:

If Bandit discovers a violation that meets or exceeds your active severity threshold (Medium or High), it halts execution, rejects the commit, and provides a detailed breakdown including the issue ID, line numbers, and its Common Weakness Enumeration (CWE) classification:

```text
Run started: 2026-05-31 18:00:20.408359+00:00

Test results:
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, possible injection.
   Severity: High   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   Location: src/example_module/utils.py:12:4
11       def execute_user_query(user_input):
12           subprocess.Popen(user_input, shell=True)
13

--------------------------------------------------
Code scanned:
        Total lines of code: 23318
Run metrics:
        Total issues (by severity): Low: 3, Medium: 0, High: 1
```

### When security scans clear successfully:

If project satisfies active gating baseline, it finishes with a clean summary report:
```text
Code scanned:
        Total lines of code: 23318
        Total lines skipped (#nosec): 2

Run metrics:
        Total issues (by severity): Low: 0, Medium: 0, High: 0

bandit...................................................................Passed
```

Happy scanning! 🛡️
