# Windows Setup Guide

This guide provides a step-by-step walkthrough for setting up the Hiero Python SDK development environment specifically for Windows users. We will use PowerShell and `uv` for dependency management.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Fork and Clone](#fork-and-clone)
- [Add Upstream Remote](#add-upstream-remote)
- [Install uv](#install-uv)
- [Install Dependencies](#install-dependencies)
- [Optional Dependencies](#optional-dependencies)
- [Generate Protobufs](#generate-protobufs)
- [Environment Setup](#environment-setup)
- [Verify Your Setup](#verify-your-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Git for Windows**: [Download and install Git](https://gitforwindows.org/).
2.  **Python 3.10+**: [Download and install Python](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is checked during installation.
3.  **GitHub Account**: You will need a GitHub account to fork the repository.
4.  **Chocolatey**: For Windows 10 users, you must install Chocolatey. A link for install can be found here [Chocolatey Install](https://chocolatey.org/install). Make sure Chocolatey is added to PATH.

---

## Fork and Clone

1.  Navigate to the [hiero-sdk-python repository](https://github.com/hiero-ledger/hiero-sdk-python) and click the **Fork** button.
2.  Open **PowerShell** and run the following commands to clone your fork:

```powershell
# Clone the repository
git clone https://github.com/<your-username>/hiero-sdk-python.git

# Navigate into the project directory
cd hiero-sdk-python
```

---

## Add Upstream Remote

Connect your local repository to the original Hiero SDK repository. This allows you to keep your fork synchronized with the latest changes.

```powershell
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

**What this does:**
- `origin` = your fork (where you push your changes)
- `upstream` = the original repository (where you pull updates from)

Verify your remotes are configured correctly:

```powershell
git remote -v
```

You should see:
```
origin    https://github.com/<your-username>/hiero-sdk-python.git (fetch)
origin    https://github.com/<your-username>/hiero-sdk-python.git (push)
upstream  https://github.com/hiero-ledger/hiero-sdk-python.git (fetch)
upstream  https://github.com/hiero-ledger/hiero-sdk-python.git (push)
```

---

## Install uv

The Hiero Python SDK uses `uv` for extremely fast Python package and environment management.

1.  In your PowerShell window, run the following command to install `uv`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> ⚠️ **Important**: After the installation finishes, you **must** close your current PowerShell window and open a new one for the changes to take effect. Alternatively, you can reload your environment variables.

2.  Verify the installation by running:
```powershell
uv --version
```

---

## Install Dependencies

Once `uv` is installed and you are inside the project directory, run:

```powershell
uv sync
```

This command will:
- Download and install the correct Python version (if needed)
- Create a virtual environment
- Install all project dependencies
- Install development tools (pytest, ruff, etc.)

---

## Optional Dependencies

Some SDK features (such as Ethereum-related functionality) rely on optional dependencies that are not installed by default.

These optional dependencies are required for:
- Integration tests covering ETH-specific features
- Running ETH-related example scripts

If you are working on ETH functionality, running ETH-related tests, or executing ETH examples, install the ETH extra explicitly:

```powershell
uv sync --dev --extra eth
```

To install all available extras (useful for full-matrix testing):

```powershell
uv sync --dev --all-extras
```

---

## Generate Protobufs

The SDK requires generated protobuf files to communicate with the network. Run the following command to generate them:

```powershell
uv run python generate_proto.py
```

---

## Environment Setup

Create a `.env` file in the project root for your Hedera testnet credentials:

```powershell
Copy-Item .env.example .env
```

Edit the `.env` file with your credentials:

```
OPERATOR_ID=0.0.YOUR_ACCOUNT_ID
OPERATOR_KEY=your_private_key_here
NETWORK=testnet
```

**Don't have a testnet account?**
Get free testnet credentials at [Hedera Portal](https://portal.hedera.com/)

**Optional environment variables:**
```
ADMIN_KEY=...
SUPPLY_KEY=...
FREEZE_KEY=...
RECIPIENT_ID=...
TOKEN_ID=...
TOPIC_ID=...
VERIFY_CERTS=true  # Enable certificate verification for TLS (default: true)
```

These are only needed if you're customizing example scripts.

---

## Verify Your Setup

Run the unit test suite to ensure your local setup is working:

```powershell
uv run pytest tests/unit
```

You should see unit tests passing. Integration tests are expected to fail locally without the required network/test environment.

If you encounter errors, check that:
- All dependencies installed correctly (`uv sync`)
- Protocol buffers were generated (`uv run python generate_proto.py`)
- Your `.env` file has valid credentials

---

## Troubleshooting

### `uv` is not recognized
If you receive an error stating that `uv` is not recognized as a cmdlet or function, ensure that the installation path (typically `%USERPROFILE%\.local\bin`) is added to your Windows Environment Variables (PATH).

### Execution Policy Restrictions
If you encounter errors running scripts in PowerShell, you may need to adjust your execution policy. Run PowerShell as an Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Module not found" errors

Ensure dependencies and protobufs are installed:
```powershell
uv sync
uv run python generate_proto.py
```

### Tests fail with network errors

Check your `.env` file:
- Is `OPERATOR_ID` correct?
- Is `OPERATOR_KEY` correct?
- Is `NETWORK` set to `testnet`?

Test your credentials at [Hedera Portal](https://portal.hedera.com/)

### Git Bash Alternative
While this guide focuses on PowerShell, you can also use **Git Bash**. If using Git Bash, follow the [Standard Setup Guide](setup.md) as it behaves similarly to a Unix shell.

---

## Need Help?

- **Installation issues?** Check the [uv documentation](https://docs.astral.sh/uv/)
- **Hedera testnet?** Visit [Hedera Portal](https://portal.hedera.com/)
- **Git questions?** See [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- **General questions?** Ask on the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger)
