# Hiero SDK in Python

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/hiero-ledger/hiero-sdk-python/badge)](https://scorecard.dev/viewer/?uri=github.com/hiero-ledger/hiero-sdk-python)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/10697/badge)](https://bestpractices.coreinfrastructure.org/projects/10697)
[![License](https://img.shields.io/badge/license-apache2-blue.svg)](LICENSE)

A Python SDK for interacting with the Hedera Hashgraph platform.

## Features

- **Token Operations**: Create, mint, transfer, freeze, and manage tokens (fungible and NFTs)
- **Consensus Service**: Create topics, submit messages, and query topic info
- **Account Management**: Create accounts, transfer HBAR, and query balances
- **Smart Contracts**: Deploy and execute smart contracts
- **File Service**: Store and manage files on the network
- **And more**: Schedule transactions, node operations, PRNG, and more

---

## Quick Start

### Installing from PyPI

```bash
pip install --upgrade pip
pip install hiero-sdk-python
```

### Basic Usage

```python
from hiero_sdk_python import Client, AccountBalanceQuery

# Connect to testnet
client = Client.for_testnet()
client.set_operator(account_id, private_key)

# Query account balance
balance = AccountBalanceQuery(account_id=account_id).execute(client)
print(f"Balance: {balance.hbars} HBAR")
```

**See more examples:** [Running Examples Guide](docs/sdk_users/running_examples.md)

---

## For Contributors

### 🚀 Want to Contribute?

We'd love your help! Here's how to get started:

1. **Read the contribution guide** → [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Set up your development environment** → [Setup Guide](docs/sdk_developers/setup.md)
3. **Learn the workflow** → [Workflow Guide](docs/sdk_developers/workflow.md)

### 📋 Key Requirements

All contributions must:
- ✅ Have **signed commits** (GPG + DCO) - [Signing Guide](docs/sdk_developers/signing.md)
- ✅ Update the **changelog** - [Changelog Guide](docs/sdk_developers/changelog.md)
- ✅ Pass all tests
- ✅ Follow code quality standards

**Ready to start?** → [Setup Guide](docs/sdk_developers/setup.md)

---

## Documentation

### For SDK Users

- **[Running Examples](docs/sdk_users/running_examples.md)** - Complete guide to all SDK operations with code examples
- **[Examples Directory](examples/)** - Ready-to-run example scripts

### For SDK Developers

- **[Contributing Guide](CONTRIBUTING.md)** - Start here!
- **[Setup Guide](docs/sdk_developers/setup.md)** - First-time environment setup
- **[Workflow Guide](docs/sdk_developers/workflow.md)** - Day-to-day development workflow
- **[Signing Guide](docs/sdk_developers/signing.md)** - GPG and DCO commit signing (required)
- **[Changelog Guide](docs/sdk_developers/changelog.md)** - How to write changelog entries
- **[Rebasing Guide](docs/sdk_developers/rebasing.md)** - Keep your branch up-to-date
- **[Merge Conflicts Guide](docs/sdk_developers/merge_conflicts.md)** - Resolve conflicts
- **[Typing Guide](docs/sdk_developers/types.md)** - Python type hints
- **[Linting Guide](docs/sdk_developers/linting.md)** - Code quality tools

### Hedera Network Resources

- [Hedera Documentation](https://docs.hedera.com/)
- [Hedera Protobufs](https://github.com/hashgraph/hedera-protobufs)
- [Get Testnet Account](https://portal.hedera.com/) - Free testnet credentials
- [Hedera Testnet Guide](https://docs.hedera.com/guides/testnet)

### Other SDKs

- [Hiero JavaScript SDK](https://github.com/hiero-ledger/hiero-sdk-js)
- [Hiero Java SDK](https://github.com/hiero-ledger/hiero-sdk-java)
- [Hiero Go SDK](https://github.com/hiero-ledger/hiero-sdk-go)

---

## Installation

### For Users (PyPI)

```bash
pip install --upgrade pip
pip install hiero-sdk-python
```

### For Contributors (From Source)

**Full setup instructions:** [Setup Guide](docs/sdk_developers/setup.md)

This covers:
- Forking and cloning the repository
- Installing uv package manager
- Installing dependencies
- Generating protocol buffers
- Setting up environment variables
- Running tests to verify setup

---

## Environment Configuration

Create a `.env` file in your project root with your Hedera testnet credentials.

**Full setup instructions:** [Setup Guide](docs/sdk_developers/setup.md)

**Don't have testnet credentials?** Get them free at [Hedera Portal](https://portal.hedera.com/)

A sample file is provided: [.env.example](.env.example)

---

## Running Tests

```bash
uv run pytest
```

**For contributors:** Tests run automatically via [Hiero Solo Action](https://github.com/marketplace/actions/hiero-solo-action) when you push to a branch.

**Learn more:**
- [Testing with Hiero Solo](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)
- [Workflow Guide](docs/sdk_developers/workflow.md)

---

## Community & Support

### Get Help

- **Discord**: [Hiero Python SDK Channel](https://discord.com/channels/905194001349627914/1336494517544681563)
- **General Hedera Support**: [Developer Discord](https://discord.com/channels/373889138199494658/1106578684573388900)
- **Issues**: [GitHub Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)

### Stay Updated

- **Blog**: [Hiero Blog](https://hiero.org/blog/)
- **Videos**: [LFDT YouTube Channel](https://www.youtube.com/@lfdecentralizedtrust/videos)
- **Community Calls**: [Hiero Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week) (Wednesdays, 2pm UTC)

### Contributing

We welcome contributions! Whether you're:
- 🐛 Reporting bugs
- 💡 Suggesting features
- 📝 Improving documentation
- 💻 Writing code

**Start here:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

## Project Status

- ✅ Active development
- ✅ Production ready
- ✅ Community maintained
- ✅ Regular releases

**Latest release:** Check [PyPI](https://pypi.org/project/hiero-sdk-python/) or [GitHub Releases](https://github.com/hiero-ledger/hiero-sdk-python/releases)