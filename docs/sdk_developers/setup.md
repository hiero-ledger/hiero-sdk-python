# First-Time Setup Guide

This guide walks you through setting up your development environment for contributing to the Hiero Python SDK.

## Prerequisites

Before you begin, make sure you have:
- **Git** installed ([Download Git](https://git-scm.com/downloads))
- **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))
- A **GitHub account** ([Sign up](https://github.com/join))

## Step 1: Fork the Repository

Forking creates your own copy of the Hiero Python SDK that you can modify freely.

1. Go to [https://github.com/hiero-ledger/hiero-sdk-python](https://github.com/hiero-ledger/hiero-sdk-python)
2. Click the **Fork** button in the top-right corner
3. Select your GitHub account as the destination

You now have your own fork at `https://github.com/YOUR_USERNAME/hiero-sdk-python`

## Step 2: Clone Your Fork

Clone your fork to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/hiero-sdk-python.git
cd hiero-sdk-python
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Add Upstream Remote

Connect your local repository to the original Hiero SDK repository. This allows you to keep your fork synchronized with the latest changes.

```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

**What this does:**
- `origin` = your fork (where you push your changes)
- `upstream` = the original repository (where you pull updates from)

### Verify Your Remotes

Check that both remotes are configured correctly:

```bash
git remote -v
```

You should see:
```
origin    https://github.com/YOUR_USERNAME/hiero-sdk-python.git (fetch)
origin    https://github.com/YOUR_USERNAME/hiero-sdk-python.git (push)
upstream  https://github.com/hiero-ledger/hiero-sdk-python.git (fetch)
upstream  https://github.com/hiero-ledger/hiero-sdk-python.git (push)
```

## Step 4: Install uv Package Manager

We use `uv` - an ultra-fast Python package and project manager that replaces `pip`, `virtualenv`, `poetry`, and more.

### Install uv

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On macOS (using Homebrew):**
```bash
brew install uv
```

**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Other installation methods:** [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

### Verify Installation

```bash
uv --version
```

## Step 5: Install Dependencies

`uv` automatically manages the correct Python version based on the `.python-version` file in the project, so you don't need to worry about version conflicts.

```bash
uv sync
```

**What this does:**
- Downloads and installs the correct Python version (if needed)
- Creates a virtual environment
- Installs all project dependencies
- Installs development tools (pytest, ruff, etc.)

### Alternative: pip Editable Install

If you prefer using `pip` instead of `uv`, you can install in editable mode:

```bash
pip install --upgrade pip
pip install -e .
```

**Note:** This method requires you to have Python 3.10+ already installed on your system. Changes to your local code will be immediately reflected when you import the SDK.

### Generate Protocol Buffers

The SDK uses protocol buffers to communicate with the Hedera network. Generate the Python code from the protobuf definitions:

```bash
uv run python generate_proto.py
```

## Step 6: Set Up Environment Variables

Create a `.env` file in the project root for your Hedera testnet credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```bash
OPERATOR_ID=0.0.YOUR_ACCOUNT_ID
OPERATOR_KEY=your_private_key_here
NETWORK=testnet
```

**Don't have a testnet account?**
Get free testnet credentials at [Hedera Portal](https://portal.hedera.com/)

**Optional environment variables:**
```bash
ADMIN_KEY=...
SUPPLY_KEY=...
FREEZE_KEY=...
RECIPIENT_ID=...
TOKEN_ID=...
TOPIC_ID=...
```

These are only needed if you're customizing example scripts.

## Step 7: Verify Your Setup

Run the test suite to ensure everything is working:

```bash
uv run pytest
```

You should see tests passing. If you encounter errors, check that:
- All dependencies installed correctly (`uv sync`)
- Protocol buffers were generated (`uv run python generate_proto.py`)
- Your `.env` file has valid credentials

## Step 8: Run an Example

Test that you can interact with the Hedera network:

```bash
uv run python examples/account_balance.py
```

You should see your account balance printed to the console.

## Troubleshooting

### "uv: command not found"

Make sure `uv` is in your PATH. After installation, you may need to restart your terminal or run:

```bash
source ~/.bashrc  # or ~/.zshrc on macOS
```

### "Permission denied" when cloning

Make sure you're using the HTTPS URL (not SSH) if you haven't set up SSH keys with GitHub:
```bash
# Use HTTPS (works without SSH setup)
git clone https://github.com/YOUR_USERNAME/hiero-sdk-python.git

# Not SSH (requires SSH key setup)
# git clone git@github.com:YOUR_USERNAME/hiero-sdk-python.git
```

### "Module not found" errors

**If using uv:**
```bash
uv sync
uv run python generate_proto.py
```

**If using pip:**
```bash
pip install -e .
python generate_proto.py
```

### Tests fail with network errors

Check your `.env` file:
- Is `OPERATOR_ID` correct?
- Is `OPERATOR_KEY` correct?
- Is `NETWORK` set to `testnet`?

Test your credentials at [Hedera Portal](https://portal.hedera.com/)

## Understanding Your Setup

Here's what your project structure looks like now:

```
hiero-sdk-python/
├── .venv/                  # Virtual environment (created by uv)
├── src/
│   └── hiero_sdk_python/   # SDK source code
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── examples/               # Example scripts
├── docs/                   # Documentation
├── .env                    # Your credentials (never commit this!)
├── .env.example            # Template for .env
├── pyproject.toml          # Project configuration
└── .python-version         # Python version used by uv
```

## Next Steps

✅ Your development environment is ready!

**Next:** [Set up commit signing →](signing.md)

Once you've configured GPG signing, you'll be ready to start contributing. See the [Development Workflow Guide](workflow.md) for day-to-day development practices.

## Quick Reference

**Update your fork's main branch:**
```bash
git checkout main
git fetch upstream
git pull upstream main
```

**Run tests:**
```bash
# Using uv
uv run pytest

# Using pip
pytest
```

**Run an example:**
```bash
# Using uv
uv run python examples/script_name.py

# Using pip
python examples/script_name.py
```

**Check installed packages:**
```bash
# Using uv
uv pip list

# Using pip
pip list
```

## Need Help?

- **Installation issues?** Check the [uv documentation](https://docs.astral.sh/uv/)
- **Hedera testnet?** Visit [Hedera Portal](https://portal.hedera.com/)
- **Git questions?** See [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- **General questions?** Ask on [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563)