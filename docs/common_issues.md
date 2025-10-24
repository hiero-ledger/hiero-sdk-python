## Resolving Changelog Conflicts

A common issue you may face when submitting a pull request (PR) is a "changelog conflict." This happens when your PR modifies the `CHANGELOG.md` file, but another PR that also modified it was merged before yours.

### Common Causes

There are two main reasons this happens:

1.  **SDK Version Bump (Scenario A):** The SDK launched a new version (e.g., `0.1.5` became `0.1.6`) while your PR was open. Your changelog entry was under the `[Unreleased]` section, but that section is now part of the `[0.1.6]` release. Your entry needs to be moved to the *new* `[Unreleased]` section.
2.  **Same Section Conflict (Scenario B):** Another PR was merged that added its own changelog entry to the *exact same* `[Unreleased]` section as yours (e.g., you both added a line under `Changed`). The file now has a conflict because Git doesn't know which line should come first.

### How to Resolve the Conflict

To fix this, you need to sync your branch with the main project (known as `upstream`) and then fix the conflict. This is done using a `rebase`.

**1. Sync Your Local `main` Branch**

First, ensure your local `main` branch has the latest changes from the `hiero-ledger` project.

```bash
# Switch to your main branch
git checkout main

# Fetch all the latest changes from the upstream (original) repository
git fetch upstream

# Pull those changes into your local main branch
git pull upstream main