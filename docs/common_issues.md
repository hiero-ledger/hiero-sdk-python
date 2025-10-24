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
```

## 2. Changelog Conflict Examples
### Example 1: The SDK Version has upgraded
If the SDK version has upgraded, you'll need to move your changelog entry to the new unreleased section.

For example:
before

`UNRELEASED (version 0.1.6)`
` Changed`

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId
- Refactor examples/token_cancel_airdrop <-- your entry

Version 0.1.6 is now released but your PR is not yet merged so we need to move your changelog entry to the new UNRELEASED SECTION.

after:

`[Unreleased]`

`Changed`
- Refactor examples/token_cancel_airdrop <-- CORRECT

 `[0.1.6] - 2025-10-21`
` Changed`

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId

### Example 2: The SDK has had a minor update
In this case, a new PR is merged in the same release that has a changelog entry written in the same section as you.

For example:

Alice's Pull Request:
` UNRELEASED`
` Changed`

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId <-- ALICE'S Change

Bob's Pull Request:
` UNRELEASED`
` Changed`

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Refactor examples/token_cancel_airdrop <-- BOB's change

They are in conflict.

Alice's change was merged before Bob, so Bob needs update his changelog to be:
Bob's Pull Request:
` UNRELEASED`
` Changed`

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId <-- ALICE'S Change
- Refactor examples/token_cancel_airdrop <-- BOB's change
Which has no conflict as they are no longer clashing.

Congratulations!