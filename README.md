
# Hiero SDK in Python

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/hiero-ledger/hiero-sdk-python/badge)](https://scorecard.dev/viewer/?uri=github.com/hiero-ledger/hiero-sdk-python)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/10697/badge)](https://bestpractices.coreinfrastructure.org/projects/10697)
[![License](https://img.shields.io/badge/license-apache2-blue.svg)](LICENSE)

A Python SDK for interacting with the Hedera Hashgraph platform.


## Quick Start

### Installing from PyPI

```bash
pip install --upgrade pip
pip install hiero-sdk-python
```

### Environment Configuration

Create a `.env` file in your project root with your Hedera testnet credentials.

**Full setup instructions:** [Setup Guide](docs/sdk_developers/setup.md)

**Don't have testnet credentials?** Get them free at [Hedera Portal](https://portal.hedera.com/)

A sample file is provided: [.env.example](.env.example)


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
- **[Changelog Guide](docs/sdk_developers/changelog_entry.md)** - How to write changelog entries
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

## Running Tests

```bash
uv run pytest
```

**For contributors:** Tests run automatically via [Hiero Solo Action](https://github.com/marketplace/actions/hiero-solo-action) when you push to a branch.

**Learn more:**
* [Testing with Hiero Solo](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)

---

## Community & Support

### Get Help

* **Discord**: [Hiero Python SDK Channel](https://discord.gg/hyperledger)
* **General Hedera Support**: [Developer Discord](https://discord.gg/UuQevYMP)
* **Issues**: [GitHub Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)

### Stay Updated

* **Blog**: [Hiero Blog](https://hiero.org/blog/)
* **Videos**: [LFDT YouTube Channel](https://www.youtube.com/@lfdecentralizedtrust/videos)
* **Community Calls**: [Hiero Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week) (Wednesdays, 2pm UTC)

---

## ⭐ Follow Us

If you find the Hiero Python SDK useful, there are three key ways you can support the project and stay up-to-date:

### Star the Repository

Click the **Star** button at the top right of the repository page.

* **What it means:** Starring is a simple way to bookmark the project. It saves the repository to your list of **Starred** repositories on GitHub, which you can find on your personal GitHub profile page. It shows appreciation for the work being done.

### Watch for Activity

Click the **Watch** button (next to the Star button).

* **What it means:** This allows you to choose what level of detail you want to monitor, from getting notified for all activity to only receiving alerts for security vulnerabilities. This is the best way to stay informed about new features and releases.

### Fork the Project

Click the **Fork** button (at the top right).

* **What it means:** Forking creates a complete copy of the repository under your personal GitHub account. This is the first step required if you plan to submit contributions (like Pull Requests) or if you want to use the codebase as a starting point for your own project.

## Contributions

We welcome contributions! Whether you're:
* 🐛 Reporting bugs
* 💡 Suggesting features
* 📝 Improving documentation
* 💻 Writing code

**Start here:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

**Latest release:** Check [PyPI](https://pypi.org/project/hiero-sdk-python/) or [GitHub Releases](https://github.com/hiero-ledger/hiero-sdk-python/releases)