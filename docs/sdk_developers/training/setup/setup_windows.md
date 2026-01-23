# Windows Setup Guide

This guide provides a step-by-step walkthrough for setting up the Hiero Python SDK development environment specifically for Windows users. We will use PowerShell and `uv` for dependency management.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Fork and Clone](#fork-and-clone)
- [Install uv](#install-uv)
- [Install Dependencies](#install-dependencies)
- [Generate Protobufs](#generate-protobufs)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Git for Windows**: [Download and install Git](https://gitforwindows.org/).
2.  **Python 3.10+**: [Download and install Python](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is checked during installation.
3.  **GitHub Account**: You will need a GitHub account to fork the repository.

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

This command will create a virtual environment and install all necessary development dependencies automatically.

---

## Generate Protobufs

The SDK requires generated protobuf files to communicate with the network. Run the following command to generate them:

```powershell
uv run python generate_proto.py
```

---

## Troubleshooting

### `uv` is not recognized
If you receive an error stating that `uv` is not recognized as a cmdlet or function, ensure that the installation path (typically `%USERPROFILE%\.local\bin`) is added to your Windows Environment Variables (PATH).

### Execution Policy Restrictions
If you encounter errors running scripts in PowerShell, you may need to adjust your execution policy. Run PowerShell as an Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Git Bash Alternative
While this guide focuses on PowerShell, you can also use **Git Bash**. If using Git Bash, follow the [Standard Setup Guide](02_installing_hiero_python_sdk.md) as it behaves similarly to a Unix shell.

