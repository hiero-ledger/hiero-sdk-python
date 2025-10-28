# Common Issues for SDK Developers

This guide is designed to help developers overcome some common issues when developing for the Hiero Python SDK. If you're new to contributing, this document will walk you through frequently encountered challenges and their solutions.

## Table of Contents

- [Verified Commits and Signing Issues](#verified-commits-and-signing-issues)
- [Changelog Issues](#changelog-issues)
- [One Issue Per Pull Request](#one-issue-per-pull-request)
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

## One Issue Per Pull Request

### The Problem

We only accept **one issue per pull request**. 

Sometimes, a contributor will submit a pull request that contains changes for multiple issues. This makes the pull request difficult to review and merge.

For example, if your issue is "Expand Token Creation to allow Infinite tokens", your pull request should ONLY contain changes for that feature and its changelog entry (e.g., `feat: added infinite tokens to token create`). 

You should **NOT** also add a separate change, like `chore: type hint token_associate`, in the same pull request. That should be its own issue and its own pull request.

### The Solution

To solve this, you must follow these best practices for every pull request you submit:

1.  **Create One Branch Per Issue**
    You must create a new, separate branch for every issue you work on. 

2.  **Always Branch from `main`**
    This new branch should *always* be created from the `main` branch. Do not create a new branch from one of your other branches.

3.  **Keep Your `main` Branch Up-to-Date**
    Before you create a new branch, make sure your local `main` branch is in sync with the upstream (the project's) `main` branch. You can find instructions for this in `rebasing.md`, but the quick commands are:
    ```sh
    git fetch upstream
    git checkout main
    git pull upstream main
    ```

4.  **Check Your Files Before Submitting**
    After you submit your pull request, click the **"Files changed"** tab.



    Look at the list of files. Do they *only* relate to the *one* issue you are solving? If you see extra files or changes you didn't mean to include, your PR will not be merged.

    You can see an example of this tab here: [https://github.com/hiero-ledger/hiero-sdk-python/pull/515/files](https://github.com/hiero-ledger/hiero-sdk-python/pull/515/files)

---


## Getting in Touch

### Problem
You're stuck, have questions, or need help with your contribution.

### Solution
The Hiero Python SDK community is here to help! Here are the best ways to get support:

**1. Discord Community**
- Join the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger)
- Join the [Hedera Discord](https://discord.com/invite/hederahashgraph)
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
2. Ask in the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger)
3. Create a new issue with the `documentation` label if something should be added to this guide

Happy contributing! 🎉
