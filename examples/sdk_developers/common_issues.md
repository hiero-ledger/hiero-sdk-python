# Common Issues for SDK Developers

This guide is designed to help developers overcome some common issues when developing for the Hiero Python SDK. If you're new to contributing, this document will walk you through frequently encountered challenges and their solutions.

## Table of Contents

- [Verified Commits and Signing Issues](#verified-commits-and-signing-issues)
- [Changelog Issues](#changelog-issues)
- [Getting in Touch](#getting-in-touch)

---

## Verified Commits and Signing Issues

### Problem
Your pull request shows unverified commits, or GitHub rejects your commits because they aren't properly signed.

### Solution
Every commit in this repository **must be both GPG-signed and DCO-signed**. This is a strict requirement for all contributions.

**Required commit command:**
```bash
git commit -S -s -m "your commit message"
```

- `-S` flag: GPG signature (cryptographically proves you authored the commit)
- `-s` flag: DCO sign-off (Developer Certificate of Origin)

**How to set up GPG signing:**

1. Check our comprehensive guide: [Signing Guide](../docs/sdk_developers/signing.md)
2. Generate a GPG key if you don't have one
3. Add your GPG key to your GitHub account
4. Configure Git to use your GPG key

**If you forgot to sign a commit:**
```bash
git commit --amend -S -s
git push --force-with-lease
```

**Common issues:**
- "gpg: signing failed: No secret key" → Your GPG key isn't configured in Git
- Commit shows "Unverified" badge → GPG key not added to GitHub account
- "error: gpg failed to sign the data" → GPG agent may not be running

---

## Changelog Issues

### Problem
Your PR is blocked because you haven't updated the CHANGELOG.md file, or you're unsure where/how to add your changes.

### Solution
Every contribution **must include an entry in CHANGELOG.md** under the `[Unreleased]` section.

**Location:** `CHANGELOG.md` in the repository root

**Format:**
```markdown
## [Unreleased]

### Added
- Your new feature description

### Fixed
- Your bug fix description

### Changed
- Your improvement description
```

**Requirements:**
- Add one concise sentence describing your change
- Place it in the correct category (Added/Fixed/Changed/Removed)
- Keep it user-focused and descriptive
- Add your entry at the top of the appropriate section

**Example:**
```markdown
## [Unreleased]

### Added
- Common issues guide for SDK developers at `examples/sdk_developers/common_issues.md`
```

**Why this matters:**
The changelog helps users understand what's new in each release. Your entry will be included in the next version's release notes.

---

## Getting in Touch

### Problem
You're stuck, have questions, or need help with your contribution.

### Solution
The Hiero Python SDK community is here to help! Here are the best ways to get support:

**1. Discord Community**
- Join the [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563)
- Ask questions, discuss your PR, or get real-time help from maintainers and community members
- This is the fastest way to get unstuck

**2. Community Calls**
- Attend our fortnightly community calls: Wednesdays at 2pm UTC
- Calendar: [Hiero LFTD Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
- Great for discussing larger contributions or getting feedback

**3. GitHub Issues**
- Comment on the issue you're working on
- Tag maintainers if you need specific guidance
- Check [existing issues](https://github.com/hiero-ledger/hiero-sdk-python/issues) for similar problems

**4. Documentation Resources**
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Complete contribution guidelines
- [Signing Guide](../docs/sdk_developers/signing.md) - GPG and DCO setup
- [Rebasing Guide](../docs/sdk_developers/rebasing.md) - Keep your branch up to date
- [Linting Guide](../docs/sdk_developers/linting.md) - Code quality tools
- [Types Guide](../docs/sdk_developers/types.md) - Python type hints

**Tips for getting help:**
- Provide context: share error messages, screenshots, or logs
- Mention what you've already tried
- Link to your work-in-progress PR if applicable
- Be patient and respectful

---

## Still Need Help?

If you encounter an issue not covered in this guide, please:

1. Search existing [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues) and [Discussions](https://github.com/hiero-ledger/hiero-sdk-python/discussions)
2. Ask in the [Discord](https://discord.com/channels/905194001349627914/1336494517544681563)
3. Create a new issue with the `documentation` label if something should be added to this guide

Happy contributing! 🎉
