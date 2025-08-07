# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK! We appreciate your help and welcome code contributions, feature requests, bug reports and blog posts. The community also offers various sources of support.

This guide will explain how to contribute.

## Table of Contents

- [Code Contributions](#code-contributions)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [Blog Posts](#blog-posts)
- [Find Support and Get In Touch](#find-support-contact)
    - [Socials](#socials)
    - [Documentation](#documentation)

---

## Code Contributions
Code contributions are handled using [Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls). Please ensure:

1. **Fork the Python SDK**. Fork this repository at [Python SDK](https://github.com/hiero-ledger/hiero-sdk-python), clicking the fork button on the top right.

2. **Find or Create an Issue**. Identify or create an issue you'll be working on [Issue](https://github.com/hiero-ledger/hiero-sdk-python/issues). You can create a new feature issue by clicking 'New issue' then feature or bug to resolve by clicking 'New issue' then bug.

3. **Get Assigned**. Add a comment inside an issue and state you'd like to work on the issue. Wait until a maintainer assigns you to the issue (to avoid duplicating effort).

4. **Create a branch** with your issue as a title. We follow a trunk-based development approach. The `main` branch should always be stable and production-ready.
Typical branches:
- `feature/...` for new features
- `fix/...` for bug fixes

5. **Solve your issue on this branch**. Commit all your code to your branch, ensure all your commits are:
- Prefixed by informative messaging (`feat`, `fix`, `chore`, `docs`, `test`) in alignment with [conventional commit formatting](https://www.conventionalcommits.org/en/v1.0.0/). Individual commit messages within PRs can be more descriptive and do not necessarily need the prefix, as long as they are clear and meaningful.
  - Example: "feat: TokenCreate unit test". Individual commit messages within PRs can be more descriptive and do not necessarily need the prefix, as long as they are clear and meaningful.
- Signed appropriately `git commit -S -s -m "message"` [Signing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/Commit_Signing.md). This is easiest using terminal but there are ways to apply global signing to commits.

6. **Type hint and lint your code**. 
Add type hints and check with mypy for extra robustness (ensure any new commits are signed):
```python
mypy hedera_sdk_python/src/hiero_sdk_python/your_file_location.py
```
Optionally your code conforms to standard practices with pylint:
```python
pylint hedera_sdk_python/src/hiero_sdk_python/your_file_location.py
```
Read more at [README_types](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_types.md)
Read more at [README_linting](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README_linting.md)

7. **Create unit and integration tests**. The functionality for your new feature must be tested locally (unit tests) and through the solo network (integration tests). See unit test examples at hedera_sdk_python/tests/unit. See integration test examples at hedera_sdk_python/tests/integration. You can run the unit tests having installed pytest:

```python
python3 pytest/hedera_sdk_python/tests/unit/your_test_name.py
```
To run the integration tests, you can either attach the solo action to your fork on github online which will run when you publish your changes, or you can wait until you submit a pull request and it will run automatically.

Review test feedback and refine code until they all pass. Ask for help if required.

8. **Push All Changes** you've now completed your issue, ensure all commits are pushed to your repo.

9. **Create a Pull Request** visit [Python SDK Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls). Your recent push should show at the top and click to create a pull request from that. For more advanced users, we recommend creating a draft pull request as soon as you are assigned to the issue and building on that to help us avoid conflicts. Our maintainers will be notified to review your pull request. All Pull Requests must be approved by at least one member of the SDK team before merging. It will be merged as a squashed pull request to keep the commit history tidy.

## Feature Requests

We welcome new functionality or feature suggestions for the Python SDK. You can submit a feature request on the issue page [Issue Page for Feature Requests](https://github.com/hiero-ledger/hiero-sdk-python/issues). When submitting a feature, please make sure to:

1. **Search Existing Requests**: If a request already exists, give it a thumbs-up or comment, adding more contextual information, instead of duplicating. Else proceed.
2. **Create Your Feature**: Click the green new issue button on the top right of the issues page. A pop-up menu appears, click the second option: Feature. Add an informative title to describe your desired feature and a clear explanation of the problem this would solve (if applicable, else just detail how you envisage the feature to work). Next, scroll down and provide a proposed solution, such as how you roughly see the feature working or example code. Click 'create'.
3. **Decide If You Want To Work On It**. If you are passionate about your new feature and would like to create it, add a comment after you have created the feature saying "I would like to work on this issue" and we will assign you.

## Bug Reports

We welcome bug reports. Please submit bug reports on our [Issues Page for Bug Reports](https://github.com/hiero-ledger/hiero-sdk-python/issues) page. When filing a bug report follow these steps:

1. **Search Existing Issues**: Check if the bug has already been reported. If there is no bug report, proceed.
2. **Upgrade to the Latest Version**: Install the latest Python SDK release. The bug may have been fixed.
3. **File The Bug Report**: Click on the top right: "new issue". Select the bug report option. Provide an informative title, clear description, steps for us to reproduce and logs or screenshots. Additional information such as: expected vs actual behavior and a minimal working example are not required but will be helpful. Click 'create'.

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