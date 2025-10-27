# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK!

## Table of Contents

- [Quick Start for New Contributors](#-quick-start-for-new-contributors)
- [Ways to Contribute](#ways-to-contribute)
  - [Code Contributions](#-code-contributions)
  - [Bug Reports](#-bug-reports)
  - [Feature Requests](#-feature-requests)
  - [Blog Posts](#-blog-posts)
  - [Breaking Changes](#️-breaking-changes)
- [Developer Resources](#developer-resources)
- [Community & Support](#community--support)
- [Quick Reference](#quick-reference)
- [Common Questions](#common-questions)

---

## 🚀 Quick Start for New Contributors

**First time contributing?** Follow this path:

1. **[Setup Guide](docs/sdk_developers/setup.md)** ← START HERE
   - Fork, clone, and install dependencies
2. **[Signing Guide](docs/sdk_developers/signing.md)** ← REQUIRED
   - Set up GPG commit signing (mandatory)
3. **[Workflow Guide](docs/sdk_developers/workflow.md)** ← LEARN THIS
   - Day-to-day development workflow
4. **[Quality Checklist](docs/sdk_developers/checklist.md)** ← BEFORE SUBMITTING
   - Final checks before PR submission

**Already contributed before?** Quick links:
- [Rebasing Guide](docs/sdk_developers/rebasing.md)
- [Merge Conflicts](docs/sdk_developers/merge_conflicts.md)
- [Changelog Guide](docs/sdk_developers/changelog.md)

---

## Ways to Contribute

### 💻 Code Contributions

**Quick workflow:**
1. Find/create an issue → [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)
2. Get assigned (comment "I'd like to work on this")
3. Follow the [Workflow Guide](docs/sdk_developers/workflow.md)
4. Submit a PR

**Requirements:**
- ✅ Signed commits (GPG + DCO) - [Signing Guide](docs/sdk_developers/signing.md)
- ✅ Updated changelog - [Changelog Guide](docs/sdk_developers/changelog.md)
- ✅ Tests pass
- ✅ Code quality checks - [Checklist](docs/sdk_developers/checklist.md)

**Detailed step-by-step:** See [Workflow Guide](docs/sdk_developers/workflow.md)

---

### 🐛 Bug Reports

Found a bug? Help us fix it!

1. **Search existing issues** - Check if it's already reported
2. **Upgrade first** - Test with the latest version:
   ```bash
   pip install -U hiero-sdk-python
   ```
3. **Report it:**
   - **Regular bugs** → [Create Issue](https://github.com/hiero-ledger/hiero-sdk-python/issues/new)
   - **Security bugs** → Contact [maintainers](MAINTAINERS.md) on [Discord](https://discord.com/channels/905194001349627914/1336494517544681563) privately

**Include:**
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Logs/screenshots if applicable

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

### ⚠️ Breaking Changes

**Avoid breaking changes** when possible. If necessary:
1. Create a new issue explaining the benefits
2. Wait for approval
3. Submit as a separate PR with:
   - Reasons for the change
   - Backwards compatibility plan
   - Tests
   - Changelog documentation

---

## Developer Resources

### Essential Guides

| Guide | What It Covers |
|-------|----------------|
| [Setup](docs/sdk_developers/setup.md) | Fork, clone, install, configure |
| [Workflow](docs/sdk_developers/workflow.md) | Branching, committing, PRs |
| [Signing](docs/sdk_developers/signing.md) | GPG + DCO commit signing |
| [Changelog](docs/sdk_developers/changelog.md) | Writing changelog entries |
| [Checklist](docs/sdk_developers/checklist.md) | Pre-submission checklist |
| [Rebasing](docs/sdk_developers/rebasing.md) | Keeping branch updated |
| [Merge Conflicts](docs/sdk_developers/merge_conflicts.md) | Resolving conflicts |
| [Types](docs/sdk_developers/types.md) | Python type hints |
| [Linting](docs/sdk_developers/linting.md) | Code quality tools |

### Code Examples

- **SDK Examples:** [examples/](examples/) directory
- **Usage Guide:** [Running Examples](docs/sdk_users/running_examples.md)

### Hedera Network Resources

- [Hedera Documentation](https://docs.hedera.com/)
- [Get Testnet Account](https://portal.hedera.com/) (free)
- [Hedera Protobufs](https://github.com/hashgraph/hedera-protobufs)

### Other Language SDKs

- [JavaScript SDK](https://github.com/hiero-ledger/hiero-sdk-js)
- [Java SDK](https://github.com/hiero-ledger/hiero-sdk-java)
- [Go SDK](https://github.com/hiero-ledger/hiero-sdk-go)

---

## Community & Support

### Get Help

- **Discord:** [Hiero Python SDK Channel](https://discord.com/channels/905194001349627914/1336494517544681563)
- **General Support:** [Hedera Developer Discord](https://discord.com/channels/373889138199494658/1106578684573388900)
- **Issues:** [GitHub Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)

### Stay Connected

- **Blog:** [Hiero Blog](https://hiero.org/blog/)
- **Videos:** [LFDT YouTube](https://www.youtube.com/@lfdecentralizedtrust/videos)
- **Community Calls:** Wednesdays 2pm UTC - [Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)

---

## Quick Reference

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
git checkout -b issue-123-fix-thing

# Make changes, then commit (signed!)
git add .
git commit -S -s -m "feat: add new feature"

# Update changelog
# Edit CHANGELOG.md, add entry under [Unreleased]

# Push and create PR
git push origin issue-123-fix-thing
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

**Need help?** Ask on [Discord](https://discord.com/channels/905194001349627914/1336494517544681563) - we're friendly!