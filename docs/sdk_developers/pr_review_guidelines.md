# PR Review Guidelines

This guide provides best practices for reviewing pull requests in the Hiero Python SDK.
Whether you are a first-time reviewer or a seasoned contributor, these guidelines will help you deliver constructive, high-quality reviews that strengthen the codebase and support fellow contributors.

## Table of Contents

- [Introduction & Community Reviews](#1-introduction--community-reviews)
- [Quality Checks](#2-quality-checks)
  - [Commit Signing](#commit-signing)
  - [Issue Linkage](#issue-linkage)
  - [Issue Resolution](#issue-resolution)
  - [CI Workflow Checks](#ci-workflow-checks)
- [Review Best Practices](#3-review-best-practices)
  - [Circle of Competence](#circle-of-competence)
  - [Communication Style](#communication-style)
  - [Research Process](#research-process)
  - [Language and Documentation](#language-and-documentation)
  - [AI Review Caution](#ai-review-caution)
- [Quick Reference Checklist](#4-quick-reference-checklist)
- [Related Documentation & Help](#5-related-documentation--help)

---

## 1. Introduction & Community Reviews

Anyone from the community is welcome to review pull requests that carry the **`reviewer: community`** label. These are pull requests that maintainers have marked as ready for community feedback.

👉 **[View open PRs available for community review](https://github.com/hiero-ledger/hiero-sdk-python/pulls?q=is%3Aopen+is%3Apr+label%3A%22reviewer%3A+community%22)**

Community reviews are valuable because they:
- Bring diverse perspectives and catch issues maintainers might miss
- Help contributors receive faster feedback
- Give reviewers the opportunity to learn from real-world code changes
- Strengthen the overall quality of the SDK

You do not need special permissions to leave a review. Simply open the pull request, examine the changes, and share your feedback using GitHub's review tools.

---

## 2. Quality Checks

Before diving into the code, verify that the pull request meets the following quality criteria.

### Commit Signing

Every commit in a pull request must be signed in two ways:

1. **GPG Signed** — Look for the green **"Verified"** badge next to each commit on the PR's "Commits" tab. If any commit shows "Unverified," the author needs to re-sign.

2. **DCO Signed** — Each commit message must include a `Signed-off-by` line with the author's name and email. This is added automatically with the `-s` flag:
   ```bash
   git commit -S -s -m "feat: add new feature"
   ```

If commits are missing signatures, point the contributor to the [Signing Requirements](training/workflow/07_signing_requirements.md) guide or the detailed [Signing Guide](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/signing.md).

### Issue Linkage

Check that the pull request description links to the issue it resolves. Look for one of these keywords followed by an issue number:

- `Closes #1234`
- `Fixes #1234`
- `Resolves #1234`

If the link is missing, ask the contributor to add it. Proper linkage ensures the issue is automatically closed when the PR is merged.

### Issue Resolution

Read the linked issue carefully and verify that the pull request:

- Addresses what the issue actually asks for — nothing more, nothing less
- Meets any acceptance criteria listed in the issue description
- Does not introduce unrelated changes or scope creep

If you are unsure whether the PR fully resolves the issue, leave a comment explaining what you think is missing or needs clarification.

### CI Workflow Checks

The repository runs automated checks on every pull request. Review the status of these checks at the bottom of the PR page.

**Primary checks:**

| Check | What It Verifies |
|-------|-----------------|
| Code Coverage | Test coverage meets minimum thresholds |
| CodeQL | No security vulnerabilities detected |
| Broken Markdown Links | All documentation links are valid |
| Test File Naming | Test files follow the naming convention |

**Secondary checks:**

| Check | What It Verifies |
|-------|-----------------|
| Unit / Integration Tests | All tests pass across Python 3.10–3.14 |
| Dependency Compatibility | No dependency conflicts |
| Examples | Example scripts run without errors |
| TCK Tests | Technology Compatibility Kit passes |

If a check fails:
- Review the workflow logs to understand the failure
- If the failure is in the contributor's code, point them toward the relevant guide (e.g., [Testing Guide](testing.md) or [Linting Guide](ruff.md))
- If the failure appears unrelated to the PR (e.g., a flaky upstream test), note it in your review

---

## 3. Review Best Practices

### Circle of Competence

Focus your review on areas you understand well, but also stretch yourself:

- If you are comfortable with Python but unfamiliar with gRPC or protobuf, you can still review code style, logic flow, and test coverage
- If a change touches something you do not understand, say so honestly rather than guessing
- Reviewing outside your comfort zone is a great way to learn — just be transparent about your level of confidence

### Communication Style

How you communicate matters as much as what you say:

- **Frame uncertain feedback as questions.** Instead of "This is wrong," try "Could this cause an issue if the input is None?" Contributors may take directives literally without evaluating them critically, so questions encourage them to think.
- **Be specific and constructive.** Instead of "This needs improvement," explain what exactly should change and why.
- **Acknowledge good work.** If something is well-written or cleverly solved, say so. Positive feedback motivates contributors.
- **Stay respectful.** Disagreement is fine; personal criticism is not. Review our [Code of Conduct](code_of_conduct.md) for community standards.

### Research Process

A thorough review requires preparation:

1. **Read the full issue description first.** Understand what problem the PR is solving before looking at any code.
2. **Study the submitted code carefully.** Do not skim — read each changed file and understand the logic.
3. **Check the surrounding context.** Click "Expand" on unchanged lines in the diff to see how new code fits into the existing file.
4. **For complex changes, clone and test locally.** Open the branch in GitHub Codespaces or check it out locally to step through the code:
   ```bash
   git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
   git checkout pr-<PR_NUMBER>
   uv run pytest tests/unit/ -v
   ```

### Language and Documentation

Code quality is not just about logic:

- Check for typos and grammar issues in comments, docstrings, and documentation files
- Verify that new or changed functionality has appropriate documentation
- Ensure variable names, function names, and class names are clear and follow existing conventions
- Check that error messages are helpful and user-friendly

### AI Review Caution

AI-assisted review tools can be helpful but require critical thinking:

- ⚠️ **Do not accept AI-generated suggestions without verifying them.** AI tools may not understand repo-specific patterns, protobuf schemas, or SDK conventions.
- ⚠️ **Verify AI suggestions against the actual codebase.** Check whether a suggested pattern actually matches how things are done in this repository.
- ⚠️ **Think before suggesting AI-generated code to a contributor.** If you pass along an incorrect AI suggestion, the contributor may implement it without questioning it.

---

## 4. Quick Reference Checklist

### DO ✅

- **Read the linked issue** before reviewing any code
- **Verify commit signing** — both GPG ("Verified" badge) and DCO (`Signed-off-by`)
- **Check that all CI workflow checks pass** before approving
- **Frame uncertain feedback as questions** to encourage critical thinking
- **Be specific** — reference exact lines, suggest concrete alternatives
- **Acknowledge good work** — positive feedback matters
- **Test complex changes locally** or in GitHub Codespaces when possible
- **Check for typos, grammar, and naming conventions** in code and docs
- **Stay within your circle of competence** and be transparent about your confidence level
- **Cross-reference the codebase** before suggesting patterns or approaches

### DON'T ❌

- **Don't approve without reviewing** — every approval carries weight
- **Don't accept AI suggestions blindly** — verify against actual repo patterns first
- **Don't make demands when unsure** — ask questions instead
- **Don't review only the diff** — check surrounding context for integration issues
- **Don't ignore failing CI checks** — investigate and comment on failures
- **Don't leave vague feedback** like "this needs work" without specifics
- **Don't make personal criticisms** — review the code, not the person
- **Don't skip the issue description** — it defines what "done" looks like

---

## 5. Related Documentation & Help

### Related Documentation

| Guide | Description |
|-------|-------------|
| [Contribution Workflow](workflow.md) | Branching, committing, and PR process |
| [Testing Guide](testing.md) | Writing and running unit and integration tests |
| [Code of Conduct](code_of_conduct.md) | Community behavior standards |
| [Contributing Guide](../../CONTRIBUTING.md) | Main entry point for contributors |
| [Submitting a Pull Request](training/workflow/10_submit_pull_request.md) | Step-by-step PR submission details |
| [Signing Requirements](training/workflow/07_signing_requirements.md) | GPG and DCO commit signing |
| [Linting Guide](ruff.md) | Code quality with Ruff |
| [Security Analysis](docs/sdk_developers/bandit.md) | Security analysis & vulnerability scanning |

### Need Help?

- **Questions about a review?** Comment directly on the pull request — maintainers and other contributors will respond.
- **General questions?** Ask on the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger) (or go directly to the [#hiero-python-sdk channel](https://discord.com/channels/905194001349627914/1336494517544681563)).
- **Live support?** Join the [Python SDK Office Hours](https://zoom-lfx.platform.linuxfoundation.org/meeting/99912667426?password=5b584a0e-1ed7-49d3-b2fc-dc5ddc888338) or [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meeting/92041330205?password=2f345bee-0c14-4dd5-9883-06fbc9c60581).
