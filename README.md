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
pip install python-dotenv
```

### Environment Configuration

Create a `.env` file in your project root with your Hedera testnet credentials.

**Full setup instructions:** [Setup Guide](docs/sdk_developers/setup.md)

**Don't have testnet credentials?** Get them free at [Hedera Portal](https://portal.hedera.com/)

A sample file is provided: [.env.example](.env.example)


### Basic Usage

```python
import os
from dotenv import load_dotenv
from hiero_sdk_python import Network, Client, CryptoGetAccountBalanceQuery, AccountId, PrivateKey

# Connect to testnet
load_dotenv()
network = Network("testnet")
client = Client(network)

operator_id = AccountId.from_string(os.getenv("OPERATOR_ID",""))
operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY",""))

client.set_operator(operator_id, operator_key)

# Query account balance
balance = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client)
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
- [Testing with Hiero Solo](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)

---

## Community & Support

### Get Help

- **Discord**: - [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger) (signed in users can use this [direct link to the Python SDK Channel](https://discord.com/channels/905194001349627914/1336494517544681563))
- **General Hedera Support**: - [Hedera Developer Discord](https://discord.com/invite/hederahashgraph)
- **Issues**: [GitHub Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)

### Stay Updated

- **Blog**: [Hiero Blog](https://hiero.org/blog/)
- **Videos**: [LFDT YouTube Channel](https://www.youtube.com/@lfdecentralizedtrust/videos)
- **Community Calls**: [Hiero Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week) (Wednesdays, 2pm UTC)

---

### ⭐ Follow Us

If you find the Hiero Python SDK useful, here are three ways you can support the project and stay up-to-date **on the official repository page**: [**hiero-ledger/hiero-sdk-python**](https://github.com/hiero-ledger/hiero-sdk-python).

* **Star the Repository:** Click **Star** to bookmark the project and show your support.
* **Watch for Activity:** Click **Watch** to set your notification level, ensuring you stay updated on new features and releases.
* **Fork the Project:** Click **Fork** to create your own copy, the first step for contributions.

---

## Contributions

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

**Latest release:** Check [PyPI](https://pypi.org/project/hiero-sdk-python/) or [GitHub Releases](https://github.com/hiero-ledger/hiero-sdk-python/releases)
