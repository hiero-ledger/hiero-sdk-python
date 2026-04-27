# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK!

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
  - [Code Contributions](#-code-contributions)
  - [Bug Reports](#-bug-reports)
  - [Feature Requests](#-feature-requests)
  - [Blog Posts](#-blog-posts)
- [Developer Resources](#developer-resources)
- [Cheatsheet](#cheatsheet)

---

## Ways to Contribute

### 💻 Code Contributions

**Get Started By Reading:**

- [Project Structure](docs/sdk_developers/training/setup/project_structure.md)
- [Setup](docs/sdk_developers/training/setup)
- [Setup (Windows)](docs/sdk_developers/setup_windows.md)
- [Workflow](docs/sdk_developers/training/workflow)

**Quick Start:**

1. Find/create an issue → [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)
2. Get assigned (comment "I'd like to work on this")
3. Follow [Setup Guide](docs/sdk_developers/training/setup)
4. Follow [Workflow Guide](docs/sdk_developers/workflow.md)
5. GPG and DCO sign commits [Quickstart Signing](docs/sdk_developers/training/workflow/07_signing_requirements.md)
6. Submit a PR [Quickstart Submit PR](docs/sdk_developers/training/workflow/10_submit_pull_request.md)

**Detailed Docs:**

- [Setup Guide](docs/sdk_developers/setup.md)
- [Signing Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/signing.md)
- [Rebasing Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/rebasing.md)
- [Merge Conflicts Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/merge_conflicts.md)
- [Testing Guide](docs/sdk_developers/testing.md)


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
- Blog posts are submitted to the [Hiero Website Repository](https://github.com/hiero-ledger/hiero-website) in a Pull Request
- Written in Markdown

**Full guide with step-by-step instructions:** [Blog Post Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/blogs.md)

---

## Developer Resources

### Essential Guides

| Guide | What It Covers |
|-------|----------------|
| [Setup](docs/sdk_developers/setup.md) | Fork, clone, install, configure |
| [Workflow](docs/sdk_developers/workflow.md) | Branching, committing, PRs |
| [Signing](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/signing.md) | GPG + DCO commit signing |
| [Checklist](docs/sdk_developers/checklist.md) | Pre-submission checklist |
| [Rebasing](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/rebasing.md) | Keeping branch updated |
| [Merge Conflicts](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/merge_conflicts.md) | Resolving conflicts |
| [Types](docs/sdk_developers/types.md) | Python type hints |
| [Linting](docs/sdk_developers/ruff.md) | Code quality tools |

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

**Full guide:** [Rebasing Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/rebasing.md)


---

Thank you for contributing to the Hiero Python SDK! 🎉

- **Need help or want to connect?** Join our community on Discord! See the **[Discord Joining Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/discord.md)** for detailed steps on how to join the LFDT server
- **Quick Links:**
    - Join the main [Linux Foundation Decentralized Trust (LFDT) Discord Server](https://discord.gg/hyperledger).
    - Go directly to the [#hiero-python-sdk channel](https://discord.com/channels/905194001349627914/1336494517544681563)
