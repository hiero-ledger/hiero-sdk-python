## Submitting a Pull Request

Once you have completed your work on a dedicated branch and followed all contribution requirements (Getting Assigned, Synced with upstream, Conventional Commits, DCO and GPG signing, Avoiding Breaking changes, Changelog Entry, Testing), you are ready to submit a pull request (PR) to the Python SDK.

This guide walks you through each step of the PR process.

1. Push Your Branch to Your Fork
If you haven’t already pushed your changes:

```bash
git push origin <your-branch-name>
```

2. Open a Pull Request to the Python SDK

Navigate to the [Python SDK repository](https://github.com/hiero-ledger/hiero-sdk-python/pulls)

You will see a banner showing your branch with a “Compare & pull request” button—click it.

Or manually:
Pull requests → New pull request

If prompted, set:
- Base repository: the official Python SDK repo
- Base branch: main (unless the issue specifies otherwise)
- Head repository: your fork
- Head branch: your feature branch

3. Write a Clear Pull Request Title and Description
Your pull request title must follow conventional naming [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)

For example:
`chore: Unit Tests for TokenCreateTransaction`

Add a brief description and any important notes.

**IMPORTANT** Under Fixes, link the issue the pull request solves.

Set it to draft or 'ready to review' status and submit!

4. Wait for Checks to Run
We have several workflows that check:
- Pull Request has a conventional title
- Changelog entry under the appropriate subheading in [UNRELEASED]
- Commits are DCO and GPG key signed
- Unit Tests Pass
- Integration Tests Pass
- All Examples Pass

If they are failing and you require help, you can:
- Contact us on discord (docs/discord.md)
- Attend the Python SDK Office Hours using the [LFDT Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
- Ask for help on the pull request

All checks should be green before requesting review.

5. Request a Review
Change the status of your pull request from 'Draft' to 'Ready to Review'

Ensure you have GitHub Copilot set up as a reviewer to help maintainers on the initial review.

Assign maintainers using the request review feature on the top right.

That's it! Wait for feedback and resolve.