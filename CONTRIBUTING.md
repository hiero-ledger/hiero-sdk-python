# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK!

Please read this guide carefully.

## Table of Contents

- [Code Contributions](#code-contributions)
- [Breaking Changes](#breaking-changes)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [Blog Posts](#blog-posts)
- [Documentation Guide](#documentation-guide)
- [Find Support and Get In Touch](#find-support-contact)
    - [Socials](#socials)
    - [Documentation](#documentation)

---

## Code Contributions
Code contributions require creating a [Pull Request](https://github.com/hiero-ledger/hiero-sdk-python/pulls).

Workflow:
1. **Fork the Python SDK**. Fork the [Python SDK](https://github.com/hiero-ledger/hiero-sdk-python), clicking the fork button on the top right.

2. **Find or Create an Issue**. Select an issue to work on at [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues). Alternatively, create an issue, information found at [Feature Requests](#feature-requests) [Bug Reports](#bug-reports) or #bug-reports.

3. **Get Assigned**. Comment “I’d like to work on this” inside the issue and wait to be assigned to avoid possibly duplicating work.

4. **Create a branch** view your forked repository and create a branch from an up-to-date main. Give it a title pre-fixed by:
- feature/<short‑slug> for new features
- fix/<short‑slug> for bug fixes

5. **Create a Draft Pull Request**. Announce you have begun work on the issue and show progress by creating a draft pull request. Click the green 'New Pull Request' at [Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls), select your branch and click create a draft pull request. Inside the form:
- [ ] Add a URL to the issue you are working on
- [ ] Add a brief description on your intended solution

  **Note**: each push to your branch will add to the draft pull request.

6. **Ensure Branch is Updated With Upstream Main**. Follow these steps to make sure your branch is up-to-date with main to avoid conflicts [Updating Your Branch](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_upstream.md).

7. **Solve your issue on this branch**: code the solution and push commits progressively to your branch.
To ensure high-quality-reviewable code, please ensure:
- [ ] Update the changelog at hedera_sdk_python/CHANGELOG.md with your feature or bug fix.
- [ ] Only resolve tasks set. For example, if the issue is to code a Token create unit test, do not change the style in TokenCreateTransaction or update the integration tests. To resolve additional tasks, create a [New Feature](#feature-requests) and create an additional Pull Request.
- [ ] Add type hints and check using mypy [Typing Guide](./README_types.md)
- [ ] Style and lint using pylint [Linting Guide](./README_linting.md)
- [ ] Test your code. Create unit tests (local) at hedera_sdk_python/tests/unit and integration tests (network) at hedera_sdk_python/tests/integration [Testing Guide](./README.md). Run tests and fix code.
- [ ] Write functionality example(s) if applicable at hedera_sdk_python/examples [View Examples](https://github.com/hiero-ledger/hiero-sdk-python/tree/main/examples).
- [ ] Update README at hedera_sdk_python/examples/README.md if you added an example script(s)

8. **Ensure Quality of Commits**. Each individual commit should be:
- [ ] Pre-fixed by [conventional commit formatting](https://www.conventionalcommits.org/en/v1.0.0/) such as (`feat`, `fix`, `chore`). Example: "feat: TokenCreate unit test with missing token id".
- [ ] Signed with `git commit -S -s -m "message"` [Signing Guide](./Commit_Signing.md)

9. **Ensure Branch is Updated**. Check if main has been updated since you started work. If it has, rebase following these steps [Updating Your Branch](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_upstream.md). Resolve any conflicts.

10. **Review Network Test Outcomes**. Once your issue is solved on your branch, publish your branch and visit your python sdk repository https://github.com/your_name/hiero_sdk_python. Your push will trigger Hiero Solo Integration Tests which is our network test suite. Review outcome and fix any code.

11. **Change Pull Request From Draft to 'Ready to Review'**. Visit your draft pull request at [Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls). Convert it to 'Ready to Review' by clicking the button at the bottom of the page.

Ensure:
- [ ] You've explained the changes in your pull-request.
- [ ] CHANGELOG.md is updated
- [ ] Your pull request has a title with a pre-fix such as [conventional title formatting](https://www.conventionalcommits.org/en/v1.0.0/)
- [ ] Local unit tests pass.
- [ ] Hiero Solo Integration Tests pass.
- [ ] All commits are marked as verified. If not, you'll need to back-sign [Signing Guide](./Commit_Signing.md).
- [ ] No sensitive information is revealed.

12. **Wait for Workflow Outcomes and Reviews**. Our maintainers will be notified automatically of your pull request and provide feedback.

13. **Update Code Given Feedback**. Create additional commits to resolve applicable feedback and ask for a review once completed.

14. **Wait for Merging to Main**. When your pull request is approved, it will shortly be merged into main. Congratulations and thank you!


## Breaking Changes

Occasionally when working on an issue, you'll come across breaking changes.

As a general guide:
1. Avoid breaking changes when solving an issue. These are defined as changes that when merged and the user updates to the lastest version, will cause existing SDK users' code to error because they use legacy methods. Changes vulnerable to creating breaking changes are aspects such as: changing file structures, return statements, function names and deletions.
2. Breaking changes might be beneficial or/and necessary. If so, create a new issue and detail the benefits to the breaking change. Wait for approval to work on the issue.
3. Proposed breaking changes are sensitive and best handled as its own pull request, complete with:
- [ ] Reasons for breaking changes
- [ ] Backwards compatability additions
- [ ] Relevant unit and integration tests
- [ ] Changelog documentation

## Feature Requests

We welcome new functionality or feature suggestions for the Python SDK. You can submit a feature request on the issue page [Issue Page for Feature Requests](https://github.com/hiero-ledger/hiero-sdk-python/issues). When submitting a feature, please make sure to:

1. **Search Existing Requests**: If a request already exists, give it a thumbs-up or comment, adding more contextual information, instead of duplicating. Else proceed.
2. **Create Your Feature** following these steps:
- [ ] Define the feature so the pull-request would be small. If necessary, create multiple feature proposals. It is better to keep pull-requests specific and streamlined to keep development fast, requiring fewer rebases, and facilitate the review process.
- [ ] Click the green new issue button on the top right of the issues page.
- [ ] A pop-up menu appears, click the second option: Feature.
- [ ] Add an informative title to describe your desired feature and a clear explanation of the problem this would solve (if applicable, else just detail how you envisage the feature to work).
- [ ] Scroll down and detail a proposed solution, such as how you roughly see the feature working or example code.
- [ ] Click 'create'.
3. **Decide If You Want To Work On It**. Features can be left open for others to contribute or you can complete it yourself. If you want to complete it yourself, add "I would like to work on this issue" and we will assign you.

## Bug Reports

We welcome bug reports to help us improve the Python SDK. You can submit a bug report on the [Issue Page for Bug Reports](https://github.com/hiero-ledger/hiero-sdk-python/issues). When submitting a bug, please make sure to:

1. **Search Existing Reports**: If a report for the same bug already exists, give it a thumbs-up or comment with additional information, instead of creating a duplicate.
2. **Create Your Bug Report**: Click the green "New issue" button, select the "Bug report" template, and fill it out with as much detail as possible, including steps to reproduce, expected behavior, and SDK version.
3. **Decide If You Want To Work On It**. You can report the bug for maintainers to address, or you can offer to fix it yourself. If you want to work on the fix, add a comment like "I would like to work on this issue" and we will assign it to you.

## Blog Posts

We love it when the community writes about the Hiero Python SDK! If you've written a blog post, tutorial, or created a video, please let us know. You can share it with us on Discord or by creating an issue, and we'd be happy to help promote it.

## Documentation Guide

Understanding the project's documentation is key to making meaningful contributions. Our documentation is organized to cater to different needs, from high-level service information to detailed SDK implementation guides.

### Hedera Services
For comprehensive information about Hedera's services, protocols, and concepts (like HCS, HTS, HFS), please refer to the official [Hedera Documentation](https://docs.hedera.com/). This is the primary source of truth for the underlying network services that this SDK interacts with.

### SDK Documentation
All documentation specific to this Python SDK is located within the repository, primarily in the `/docs` directory.

#### The `/docs` Directory
This directory is the central hub for our detailed documentation. It is structured to serve different audiences:

- **/docs/community-calls**: Contains notes, agendas, and recordings from our community and developer calls.
- **/docs/sdk_developers**: Aimed at contributors to the SDK itself. Here you will find deep-dives into the SDK's architecture, design principles, contribution workflows, testing setup, and guides for adding new features.
- **/docs/sdk_users**: Aimed at developers using the SDK in their applications. This section includes installation guides, quick-start tutorials, common use-case examples, and detailed API usage guides.

#### Quick Reference & Code Resources
For quick access to essential information and code, refer to these resources within the repository:

- **[README.md](./README.md)**: The main project README with installation, basic usage, and project overview.
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** (This file): Guidelines for all types of contributions.
- **[Commit Signing Guide](./Commit_Signing.md)**: Instructions for signing your commits, a mandatory step.
- **[Typing Guide](./README_types.md)**: Information on our use of type hints and `mypy`.
- **[Linting Guide](./README_linting.md)**: Guidelines for code style and linting with `pylint`.
- **[Examples](./examples/)**: A directory of runnable code examples demonstrating various SDK features.
- **The Codebase**: The ultimate source of truth is the code itself. Don't hesitate to read the source to understand implementation details.

### Other SDKs
Hedera is a polyglot ecosystem. If you are working with other languages, you can find the corresponding official and community SDKs on the [Hedera developer portal](https://docs.hedera.com/hedera/sdks-and-apis/sdks).

<a name="find-support-contact"></a>
## Find Support and Get In Touch

### Socials
- **Discord**: Join our community on Discord for real-time discussions and support (link coming soon).
- **Twitter**: Follow us on Twitter for the latest news and updates (link coming soon).

<a name="documentation"></a>
### Documentation
For a comprehensive overview of all documentation resources, please see the [Documentation Guide](#documentation-guide).