# First-Time Setup Guide

This guide walks you through setting up your development environment for contributing to the Hiero Python SDK.

## Table of Contents

- [Repository Setup](#repository-setup)
- [Installation](#installation)
  - [Installing from PyPI](#installing-from-pypi)
  - [Installing from Source](#installing-from-source)
  - [Local Editable Installation](#local-editable-installation)
- [Generate Protocol Buffers](#generate-protocol-buffers)
- [Environment Setup](#environment-setup)
- [Setup Checklist](#examples)
- [Troubleshooting](#troubleshooting)

---

## Repository Setup

Before you begin, make sure you have:
- **Git** installed ([Download Git](https://git-scm.com/downloads))
- **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))
- A **GitHub account** ([Sign up](https://github.com/join))

### Step 1: Fork the Repository

Forking creates your own copy of the Hiero Python SDK that you can modify freely.

1. Go to [https://github.com/hiero-ledger/hiero-sdk-python](https://github.com/hiero-ledger/hiero-sdk-python)
2. Click the **Fork** button in the top-right corner
3. Select your GitHub account as the destination

You now have your own fork at `https://github.com/YOUR_USERNAME/hiero-sdk-python`

### Step 2: Clone Your Fork

Clone your fork to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/hiero-sdk-python.git
cd hiero-sdk-python
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 3: Add Upstream Remote

Connect your local repository to the original Hiero SDK repository. This allows you to keep your fork synchronized with the latest changes.

```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

**What this does:**
- `origin` = your fork (where you push your changes)
- `upstream` = the original repository (where you pull updates from)

### Step 4: Verify Your Remotes

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

---

## Installation

### Installing from PyPI

The latest release of this SDK is published to PyPI. You can install it with:

```
pip install --upgrade pip
pip install hiero-sdk-python
```

This will pull down a stable release along with the required dependencies.


### Installing from Source

You can also clone the repo and install dependencies using uv:
`uv` is an ultra-fast Python package and project manager. It replaces `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`,
`virtualenv`, and more.

#### Install uv

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
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Other installation methods:** [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

#### Verify Installation

```bash
uv --version
```

## Install Dependencies

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


## Generate Protocol Buffers

The SDK uses protocol buffers to communicate with the Hedera network. Generate the Python code from the protobuf definitions:

```bash
uv run python generate_proto.py
```

---


## Environment Setup

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
VERIFY_CERTS=true  # Enable certificate verification for TLS (default: true)
```

These are only needed if you're customizing example scripts.

**Note on TLS:** The SDK uses TLS by default for hosted networks (testnet, mainnet, previewnet). For local networks (solo, localhost), TLS is disabled by default.

### Verify Your Setup

Run the test suite to ensure everything is working:

```bash
uv run pytest
```

You should see tests passing. If you encounter errors, check that:
- All dependencies installed correctly (`uv sync`)
- Protocol buffers were generated (`uv run python generate_proto.py`)
- Your `.env` file has valid credentials

---

## Troubleshooting

### "uv: command not found"

Make sure `uv` is in your PATH. After installation, you may need to restart your terminal or run:

```bash
source ~/.bashrc  # or ~/.zshrc on macOS
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


## Need Help?

- **Installation issues?** Check the [uv documentation](https://docs.astral.sh/uv/)
- **Hedera testnet?** Visit [Hedera Portal](https://portal.hedera.com/)
- **Git questions?** See [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- **General questions?** Ask on the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger)
(or, if logged in, straight in the [related Hiero Python SDK Group](https://discord.com/channels/905194001349627914/1336494517544681563))