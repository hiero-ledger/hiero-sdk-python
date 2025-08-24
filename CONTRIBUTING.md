# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK! 

Please read this guide carefully.

## Table of Contents

- [Code Contributions](#code-contributions)
- [Breaking Changes](#breaking-changes)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [Blog Posts](#blog-posts)
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
- [ ] Add type hints and check using mypy [Typing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_types.md)
- [ ] Style and lint using pylint [Linting Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_linting.md)
- [ ] Test your code. Create unit tests (local) at hedera_sdk_python/tests/unit and integration tests (network) at hedera_sdk_python/tests/integration [Testing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/docs/testing.md). Run tests and fix code.
- [ ] Write functionality example(s) if applicable at hedera_sdk_python/examples [View Examples](https://github.com/hiero-ledger/hiero-sdk-python/tree/main/examples).
- [ ] Update README at hedera_sdk_python/examples/README.md if you added an example script(s)

8. **Ensure Quality of Commits**. Each individual commit should be:
- [ ] Pre-fixed by [conventional commit formatting](https://www.conventionalcommits.org/en/v1.0.0/) such as (`feat`, `fix`, `chore`). Example: "feat: TokenCreate unit test with missing token id".
- [ ] Signed with `git commit -S -s -m "message"` [Signing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/Commit_Signing.md)

9. **Ensure Branch is Updated**. Check if main has been updated since you started work. If it has, rebase following these steps [Updating Your Branch]((https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_upstream.md)). Resolve any conflicts.

10. **Review Network Test Outcomes**. Once your issue is solved on your branch, publish your branch and visit your python sdk repository https://github.com/your_name/hiero_sdk_python. Your push will trigger Hiero Solo Integration Tests which is our network test suite. Review outcome and fix any code.

11. **Change Pull Request From Draft to 'Ready to Review'**. Visit your draft pull request at [Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls). Convert it to 'Ready to Review' by clicking the button at the bottom of the page.

Ensure:
- [ ] You've explained the changes in your pull-request.
- [ ] CHANGELOG.md is updated
- [ ] Your pull request has a title with a pre-fix such as [conventional title formatting](https://www.conventionalcommits.org/en/v1.0.0/)
- [ ] Local unit tests pass.
- [ ] Hiero Solo Integration Tests pass.
- [ ] All commits are marked as verified. If not, you'll need to back-sign [Signing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/Commit_Signing.md).
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
- [] Reasons for breaking changes
- [] Backwards compatability additions
- [] Relevant unit and integration tests
- [] Changelog documentation

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

We welcome bug reports and appreciate your efforts. When filing a bug report, please follow these steps:

1. **Search Existing Issues**: Check if the bug has already been reported. If there is no bug report, proceed.
2. **Upgrade to the Latest Version**: Install the latest Python SDK release. The bug may have been fixed.
```python
pip install -U hiero-sdk-python
```
3. **Assess the Security Threat**: does the bug impact minor functionality or does it represent a security threat? Most bug reports should be filed directly to our [Issues Page for Bug Reports](https://github.com/hiero-ledger/hiero-sdk-python/issues) but security issues should be treated differently.
3. **File The Bug Report**: depending on the type of bug, report the bug.
- Bugs impacting functionality without a security threat. Workflow:
  - [ ] Click on the top right: "new issue". Select the bug report option. 
  - [ ] Provide an informative title, clear description, steps for us to reproduce and logs or screenshots. 
  - [ ] Additional information such as: expected vs actual behavior and a minimal working example are not required but will be helpful. 
  - [ ] Click 'create'.
- Bugs impacting security. Workflow:
  - [ ] Ensure you have joined the [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563). 
  - [ ] Contact [maintainers](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/MAINTAINERS.md) directly on discord stating there is an issue requiring immediate follow-up. 
  - [ ] Prepare sufficient documentation, such as logs, screenshots and information on how to replicate to share with the maintainer once asked.

We will review your bug report shortly and comment as appropriate.

## Blog Posts

We welcome Hiero blog posts about our Python SDK. Blog posts have to be submitted to the hiero-website repository as a pull request [Hiero Website Repository](https://github.com/hiero-ledger/hiero-website/pulls). 

When submitting a blog about the Python SDK, you'll need to fork the hiero-website repository, submit an issue, solve it and create a pull request.

Detailed steps:

1. **Search Existing Blog Posts**: If a very similar blog posts already exists, consider how to distinguish it slightly or build on the solution. For example, whether you'd like to add to that existing blog as a pull request, if you'd like to create a follow-up blog post or if you'd like to change topic slightly.
2. **Create a Blog Post New Feature Suggestion**: visit [Hiero Website Issues](https://github.com/hiero-ledger/hiero-website/issues). Click on the green button "New Issue" at the top right, select Feature and create a brief proposal for your blog post.
3. **Fork the Hiero Website Repo**: clone or fork fork of the hiero website code. Click the fork button on the top right. Congratulations, you now have a copy of the codebase!
4. **Create a New Branch**: do not create your blog post on the main brach, rather, create a new branch titled with your blog post.
5. **Write Your Blog Post**: Locate /hiero-website/content/posts. Here, create a {blog_post_title}.md and inside it, write your blog post. The hiero blog requires blogs to be written in markdown, which is why it is .md. Ensure there is an easy-to-read structure such as headings and subheadings. Focus on the text content; will ensure correct formatting in the next step.
6. **Transform to Markdown Format**: We will take your text blogpost.md and add correct markdown annotations to aspects such as headings, subheadings, bullet points, bold text so the blog post publishes with correct formatting on the hiero webpage. Markdown is simple, you can learn more about Markdown.md here [Introductory Markdown Guide](https://www.markdownguide.org/basic-syntax/). AI tooling ctan also assist.
7. **Preview Markdown**: Preview your blogpost.md and check and resolve any errors. If you have been writing on Visual Studio, this is command+shift+V or control+shift+V. You can also click "Open Preview to the Side" which is a small split screen icon with a magnifying glass on the top right. You must fix errors on the raw file, not the preview file.
9. **Add Images**: at /hiero-website/public/images/python add a high-quality jpg featured image for your blog post in the Hiero style in /blog_titles and (if desired) a profile image in /members. You can also skip this step and comment that you need help from a maintainer to add a hiero featured image.
8. **Add Hugo Requirements**: The hiero blog is built using Hugo [Introduction to Hugo](https://gohugo.io/documentation/). We need to add instructions at the top of the markdown file for it to render correctly.

Add:
```markdown

+++
title = "The Blog Post Title I Want The Community To See At Hiero Blog"
featured_image = "/images/python/blog_titles/the_icon_image_for_my_blog.jpg"
date = 2025-08-01T11:00:00-07:00
categories = ["Blog"]
abstract = "A brief abstract"
[[authors]]
name = "your name or github alias"
title = ""
organization = "Python Team"
link = ""
image = "/images/python/members/your_personal__or_github_image.png"
+++
```

8. **Commit Locally**: commit your blog post solution on your branch. Well done!
9. **Create a Pull Request to the Hiero Website**: visit [Hiero Website Pull requests](https://github.com/hiero-ledger/hiero-website/pulls). Your recent commit to your local branch should show up as an item to pull request. Click create pull request. In that pull request form, add the link to your issue in step 2.
10. **Check Hugo Preview**: preview your pull request is as expected using the Hugo preview link that shows up as a check in your pull reuqest. Ensure all tests pass.
11. **Wait for Reviews**: the Hiero website community will review your new blog post and publish it once approved.

## Find Support and Get In Touch
We strive to be a welcoming community with lots of activity, opportunities and support for all.

### Socials
- Join us on [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563), add it to your favourites andchat with the Hiero Python SDK community and maintainers. Feel free to ask questions, propose ideas, or discuss your PR.
- Discuss programming or issues with the Hedera community [Hedera Python Discord](https://discord.com/channels/373889138199494658/535491161289261096).
- Check the [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues) page for ongoing discussions. Comment on an issue and see the conversation grow.

- Learn about our recent activities at [Hiero Blog](https://hiero.org/blog/)
- Watch our Python SDK Community Calls at [LFDT Youtube Channel](https://www.youtube.com/@lfdecentralizedtrust/videos)
- Attend our Python SDK Community Call fortnightly on Wednesdays at 2pm UTC [Hiero LFTD Calendar](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)

### Documentation
- Learn about Hedera Protobufs [Hedera Protobufs](https://github.com/hashgraph/hedera-protobufs/tree/8c27786cec93abab974309074feaef9b48a695b7) and [Service Probufs](https://github.com/hashgraph/hedera-protobufs/tree/8c27786cec93abab974309074feaef9b48a695b7/services)
- Learn about the Hedera Token Service [Hedera Token Service](https://docs.hedera.com/hedera/sdks-and-apis/sdks/token-service)
- Learn about the Hedera File Service [Hedera File Service](https://docs.hedera.com/hedera/sdks-and-apis/sdks/file-service)
- Learn about the Hedera Smart Contract Service [Hedera Smart Contracts](https://docs.hedera.com/hedera/sdks-and-apis/sdks/smart-contracts)

- Review our collection of first starter documentation: README.md, Contributing.md, Commit_Signing.md, README_linting.md, README_types.md.
- View examples of our code at hiero/hedera_sdk_python/examples
- View our codebase at hedera_sdk_python/src/hiero_sdk_python

- View examples from the Javascript SDK [Hiero JS SDK](https://github.com/hiero-ledger/hiero-sdk-js/tree/main/src)
- View examples from the Java SDK [Hiero Java SDK](https://github.com/hiero-ledger/hiero-sdk-java)
- View examples from the Go SDK [Hiero Go SDK](https://github.com/hiero-ledger/hiero-sdk-go
)

Thank you for contributing to the the Hiero Python SDK and its community!
