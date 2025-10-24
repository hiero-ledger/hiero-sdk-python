# Hiero SDK in Python

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/hiero-ledger/hiero-sdk-python/badge)](https://scorecard.dev/viewer/?uri=github.com/hiero-ledger/hiero-sdk-python)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/10697/badge)](https://bestpractices.coreinfrastructure.org/projects/10697)
[![License](https://img.shields.io/badge/license-apache2-blue.svg)](LICENSE)

This is a Python SDK for interacting with the Hedera Hashgraph platform. It allows developers to:

- Manage Token Transactions like Create, Mint Fungible, Mint Non-Fungible, Associate, Dissociate, Transfer, Freeze, Unfreeze & Delete
- Manage Consensus Transactions like Topic Create, Update, Delete
- Submit Topic Messages
- Query Account Balance, Transaction Receipts, Topic Infos and Messages

## Table of Contents

- [Installation](#installation)
  - [Installing from PyPI](#installing-from-pypi)
  - [Installing from Source](#installing-from-source)
  - [Local Editable Installation](#local-editable-installation)
- [Environment Setup](#environment-setup)
- [Running Tests](#running-tests)
- [Contributing](#contributing)

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

1. Install `uv`:

`uv` is an ultra-fast Python package and project manager. It replaces `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`,
`virtualenv`, and more.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If on macOS, you can also install `uv` using Homebrew:

```bash
brew install uv
```

Other installation methods can be found [here](https://docs.astral.sh/uv/getting-started/installation/).

2. Clone this repository:

```bash
git clone https://github.com/hiero-ledger/hiero-sdk-python.git
cd hiero-sdk-python
```

3. Install dependencies:

One of the really nice features of `uv` is that it will download and manage the correct version of python and build
with the correct version of python based on the `.python-version`  file in the project. This means you don't have to
worry about managing multiple versions of python on your machine!

```bash
uv sync
uv run python generate_proto.py
```

**Note:** By default, `uv sync` will install the `dev` and `lint` dependency groups, which include tools like `pytest` and `ruff`. If you need to install only the project's core dependencies, use the `--no-default-groups flag`.

To update to a newer version of the protobuf libraries, edit the `generate_proto.py` file and change the version number
and then rerun it.


### Local Editable Installation

For active development, you can install the repo in editable mode. That way, changes in your local code are immediately reflected when you import:

```
git clone https://github.com/hiero-ledger/hiero-sdk-python.git
cd hiero-sdk-python
pip install --upgrade pip
pip install -e .
```

Now you can run example scripts like python `examples/account_create.py`, and it will import from your local hiero_sdk_python code.


## Environment Setup

Before using the SDK, you need to configure your environment variables for the operator account and other credentials.
Create a .env file in the root of your project with the following (replace with your environment variables):

```
OPERATOR_ID=0.0.1234xx
OPERATOR_KEY=af20e47d590300506032b657004220420...
NETWORK=testnet

# optional:
ADMIN_KEY=af20e47d59032b65700321009308ecfdf...
SUPPLY_KEY =302a300506032b6570032100c5e4af5..."
FREEZE_KEY=302a300306072b65700321009308ecfdf...
RECIPIENT_ID=0.0.789xx
TOKEN_ID=0.0.100xx
TOPIC_ID=0.0.200xx
FREEZE_ACCOUNT_ID=0.0.100
```

The only environment variables needed are OPERATOR_ID, OPERATOR_KEY and NETWORK. The rest is optional (if customisation of the example scripts is needed).

A [sample .env](.env.example) file is provided in the root of this project. If you do not have an account on
the Hedera testnet, you can easily get one from the [Hedera Portal](https://portal.hedera.com/). Learn more about
testnet [here](https://docs.hedera.com/guides/testnet).

## Running Tests

To run the test suite for the SDK, use the following command:
```
uv run pytest 
```

The test file in the root of this project will be automatically run when pushing onto a branch.
This is done by running 'Hiero Solo Action'. Read more about it here:

- [Github Marketplace](https://github.com/marketplace/actions/hiero-solo-action)
- [Blog Post by Hendrik Ebbers](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)

#### Output:
```
Account creation successful. New Account ID: 0.0.5025xxx
New Account Private Key: 228a06c363b0eb328434d51xxx...
New Account Public Key: 8f444e36e8926def492adxxx...
Token creation successful. Token ID: 0.0.5025xxx
Token association successful.
Token dissociation successful.
Token minting successful.
Token transfer successful.
Token freeze successful.
Token Unfreeze successful.
Token deletion successful.
Topic creation successful.
Topic Message submitted.
Topic update successful.
Topic deletion successful.
```

## Contributing

We appreciate your interest in improving the Hiero Python SDK!
Interested in helping out? We'd love for you to contribute!

Before you start, it's **essential** that you carefully read our main contribution guide: **[CONTRIBUTING.md](./CONTRIBUTING.md)**. This document is your roadmap to making a successful contribution.

Following the steps in this guide is the best way to ensure your pull request (PR) can be merged smoothly. It covers crucial requirements, including:

* How to get your commits **verified** (which is mandatory for merging).
* The correct way to update the **changelog** with your changes.
* The full step-by-step workflow for submitting code.

Our guide also explains how you can contribute in other ways, like submitting **bug reports** and proposing new **feature requests**.

### Links
- [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563)
- [Hedera Developer Support Discord](https://discord.com/channels/373889138199494658/1106578684573388900).
- [Hiero Blog](https://hiero.org/blog/)
- [LFDT Youtube Channel](https://www.youtube.com/@lfdecentralizedtrust/videos)
- [Hiero LFTD Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)


## License

This project is licensed under the Apache License.
