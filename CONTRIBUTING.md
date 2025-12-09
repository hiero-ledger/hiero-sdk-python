# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK!

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
  - [Code Contributions](#-code-contributions)
  - [Bug Reports](#-bug-reports)
  - [Feature Requests](#-feature-requests)
  - [Blog Posts](#-blog-posts)
- [Developer Resources](#developer-resources)
- [Community & Support](#community--support)
- [Cheatsheet](#cheatsheet)
- [Common Issues](#common-issues)

---

## Ways to Contribute

### 💻 Code Contributions

**Get started:** See [Steup Guide](docs/sdk_developers/setup.md)

**Quick workflow:**
1. Find/create an issue → [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)
2. Get assigned (comment "I'd like to work on this")
3. Follow the [Workflow Guide](docs/sdk_developers/workflow.md)
4. Submit a PR

**Requirements:**
- Signed commits (GPG + DCO) - [Signing Guide](docs/sdk_developers/signing.md)
- Updated changelog - [Changelog Guide](docs/sdk_developers/changelog_entry.md)
- Tests pass
- Code quality checks - [Checklist](docs/sdk_developers/checklist.md)


#### ⚠️ A Note on Breaking Changes

**Avoid breaking changes** when possible. If necessary:
1. Create a new issue explaining the benefits
2. Wait for approval
3. Submit as a separate PR with:
   - Reasons for the change
   - Backwards compatibility plan
   - Tests
   - Changelog documentation

---

### 🐛 Bug Reports

Found a bug? Help us fix it!

**See here** → [Bug Reports](docs/sdk_developers/bug.md)

---

### 💡 Feature Requests

Have an idea? We'd love to hear it!

1. **Search existing requests** - Avoid duplicates
2. **[Create a Feature Request](https://github.com/hiero-ledger/hiero-sdk-python/issues/new)**
3. **Describe:**
   - What problem does it solve?
   - How should it work?
   - Example code (if applicable)

**Want to implement it yourself?** Comment on the issue and we'll assign you!

---

### 📝 Blog Posts

Want to write about the Hiero Python SDK?

We welcome blog posts! Whether you're sharing a tutorial, case study, or your experience building with the SDK, we'd love to feature your content.

**Quick overview:**
- Blog posts are submitted to the [Hiero Website Repository](https://github.com/hiero-ledger/hiero-website)
- Written in Markdown with Hugo frontmatter
- Review process through PR

**Full guide with step-by-step instructions:** [Blog Post Guide](docs/sdk_developers/blog.md)

---

## Developer Resources

### Essential Guides

| Guide | What It Covers |
|-------|----------------|
| [Setup](docs/sdk_developers/setup.md) | Fork, clone, install, configure |
| [Workflow](docs/sdk_developers/workflow.md) | Branching, committing, PRs |
| [Signing](docs/sdk_developers/signing.md) | GPG + DCO commit signing |
| [Changelog](docs/sdk_developers/changelog_entry.md) | Writing changelog entries |
| [Checklist](docs/sdk_developers/checklist.md) | Pre-submission checklist |
| [Rebasing](docs/sdk_developers/rebasing.md) | Keeping branch updated |
| [Merge Conflicts](docs/sdk_developers/merge_conflicts.md) | Resolving conflicts |
| [Types](docs/sdk_developers/types.md) | Python type hints |
| [Linting](docs/sdk_developers/linting.md) | Code quality tools |

---

## Cheatsheet

### First-Time Setup
```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/hiero-sdk-python.git
cd hiero-sdk-python
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git

# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run python generate_proto.py
```

**Full setup:** [Setup Guide](docs/sdk_developers/setup.md)

### Making a Contribution
```bash
# Start new work
git checkout main
git pull upstream main
git checkout -b "name-of-your-issue"

# Make changes, then commit (signed!)
git add .
git commit -S -s -m "feat: add new feature"

# Update changelog
# Edit CHANGELOG.md, add entry under [Unreleased]

# Push and create PR
git push origin "name-of-your-issue"
```

**Full workflow:** [Workflow Guide](docs/sdk_developers/workflow.md)

### Keeping Branch Updated
```bash
git checkout main
git pull upstream main
git checkout your-branch
git rebase main -S
```

**Full guide:** [Rebasing Guide](docs/sdk_developers/rebasing.md)

---

## Common Issues

**HELP! I have a an issue...**  
No worries, we're here to help. But please first see the [Common Issues Guide](docs/common_issues.md).


---

Thank you for contributing to the Hiero Python SDK! 🎉

- **Need help or want to connect?** Join our community on Discord! See the **[Discord Joining Guide](docs/discord.md)** for detailed steps on how to join the LFDT server
- **Quick Links:**
    - Join the main [Linux Foundation Decentralized Trust (LFDT) Discord Server](https://discord.gg/hyperledger).
    - Go directly to the [#hiero-python-sdk channel](https://discord.com/channels/905194001349627914/1336494517544681563)

---

## Running tests locally

During development you may want to run a single test file in isolation to avoid importing the project's package-level `__init__` (which imports generated protobuf modules). To run a single test file without loading project-wide fixtures, use the project's virtualenv Python and run pytest on the path:

PowerShell example:
```powershell
# activate virtualenv (if not already active)
C:/Users/Giannis/OneDrive/Programming/hiero-sdk-python/.venv/Scripts/Activate.ps1

# install test deps if needed
python -m pip install -U pip
python -m pip install pytest

# run a single test file
python -m pytest -q tests/test_subscription_handle.py
```

If you want to run a subset of tests, use `-k` with a keyword expression or provide a directory/file path. This helps avoid heavy `conftest.py` imports during quick iteration.
