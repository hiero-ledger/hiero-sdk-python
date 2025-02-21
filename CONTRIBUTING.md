# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK! We appreciate your help and welcome bug reports, feature requests, and code contributions.

## Table of Contents

- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Code Contributions](#code-contributions)
- [Branching](#branching)
- [Committing](#committing)
- [Merging](#merging)
- [Getting in Contact](#getting-in-contact)

---

## Bug Reports

Please submit bug reports on our [Issues](../../issues) page. When filing a bug:

1. **Search Existing Issues**: See if the bug has already been reported.
2. **Upgrade to the Latest Version**: The bug may have been fixed in a newer release.
3. **Include Detailed Info**: Provide a clear description, steps to reproduce, expected vs actual behavior, relevant logs or stack traces, and a minimal working example if possible.

## Feature Requests

Feature requests are also submitted via [Issues](../../issues). As with bugs:

1. **Search Existing Requests**: If a request already exists, give it a thumbs-up or comment instead of duplicating.
2. **Detail Your Proposed Solution**: Provide specifics on how you see the feature working or example code to illustrate your idea.

**Tip**: If you plan to implement this feature yourself, mention it so we can assign the issue to you.

## Code Contributions

Code contributions are handled using [Pull Requests](../../pulls). Please ensure:

1. You fork this repository
2. You have an [Issue](../../issues) for any bug or feature you’re working on (to avoid duplicating effort).
3. **All new code has tests** to prove it works as intended or fixes the issue.
4. Follow our [Branching](#branching) and [Committing](#committing) guidelines.

---

## Branching

We follow a trunk-based development approach. Typical branches:
- `feature/...` for new features
- `fix/...` for bug fixes

The `main` branch should always be stable and production-ready.

## Committing

We use commit types like:
- `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `style`

Individual commit messages within PRs can be more descriptive and do not necessarily need the prefix, as long as they are clear and meaningful.


## Merging

- We recommend **squash and merge** to keep the commit history tidy.
- Commits should be signed and verified if possible (e.g. `git commit -s -S -m "message"`).
- Pull request titles should begin with types as appropriate (e.g. `feat: add some feature`).  

All Pull Requests must be approved by at least one member of the SDK team before merging.

---

## Getting in Contact

- Join us on [Discord](discord.gg/hyperledger) to chat with the Hiero community and maintainers. Feel free to ask questions, propose ideas, or discuss your PR.
- Check the [Issues](../../issues) page for ongoing discussions.

Thank you for helping improve the Hiero Python SDK!
