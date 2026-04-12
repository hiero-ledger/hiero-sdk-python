## Submitting a Pull Request

Once you have completed your work on a dedicated branch and followed all contribution requirements (Getting Assigned, Synced with upstream, Conventional Commits, DCO and GPG signing, Avoiding Breaking changes, Changelog Entry, Testing), you are ready to submit a pull request (PR) to the Python SDK.

This guide walks you through each step of the PR process.

### 1. Push Your Branch to Your Fork
Before opening a pull request, make sure your latest commits are pushed to your fork.

1. Verify you are on your feature branch:
```bash
git branch --show-current
```

2. If this is the first push for the branch, set upstream tracking:
```bash
git push -u origin <your-branch-name>
```

3. If the branch already exists on your fork, push normally:
```bash
git push origin <your-branch-name>
```

If you amended commits or rebased and Git rejects your push, use:
```bash
git push --force-with-lease origin <your-branch-name>
```

### 2. Open a Pull Request to the Python SDK

1. Navigate to the [Python SDK repository](https://github.com/hiero-ledger/hiero-sdk-python/pulls).
2. You will see a banner showing your branch with a "Compare & pull request" button. Click it.
3. Or manually go to: Pull requests -> New pull request.
4. If prompted, set:
   - Base repository: the official Python SDK repo
   - Base branch: main (unless the issue specifies otherwise)
   - Head repository: your fork
   - Head branch: your feature branch

### 3. Write a Clear Pull Request Title and Description

Your pull request title must follow conventional naming: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary).

For example:
`chore: Unit Tests for TokenCreateTransaction`

- Add a brief description and any important notes.
- **IMPORTANT** Under Fixes, link the issue the pull request solves.
- Set it to draft or "ready to review" status and submit.

### 4. Wait for Checks to Run

We have several workflows that check:
- Pull Request has a conventional title
- Changelog entry under the appropriate subheading in [UNRELEASED]
- Commits are DCO and GPG key signed
- Unit Tests Pass
- Integration Tests Pass
- All Examples Pass

If they are failing and you require help, you can:
- Contact us on [Discord](../../../discord.md)
- Attend the Python SDK Office Hours using the [LFDT Calendar](https://zoom-lfx.platform.linuxfoundation.org/meeting/99912667426?password=5b584a0e-1ed7-49d3-b2fc-dc5ddc888338)
- Ask for help on the pull request

All checks should be green before requesting review.

### 5. Request a Review

1. Change the status of your pull request from "Draft" to "Ready to Review".
2. Ensure you have GitHub Copilot set up as a reviewer to help maintainers on the initial review.
3. Assign maintainers using the request review feature on the top right.

That's it. Wait for feedback and resolve.
