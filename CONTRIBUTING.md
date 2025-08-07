# Contributing to the Hiero Python SDK

Thank you for your interest in contributing to the Hiero Python SDK! We appreciate your help and welcome code contributions, feature requests, bug reports and blog posts. The community also offers various sources of support.

This guide will explain how to contribute.

## Table of Contents

- [Code Contributions](#code-contributions)
    - [Branching](#branching)
    - [Committing](#committing)
    - [Merging](#merging)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [Blog Posts](#blog-posts)
- [Find Support](#find-support)
- [Getting in Contact](#getting-in-contact)

---

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

We welcome Hiero blog posts about our Python SDK. Blog posts have to be submitted to the hiero-website repository as a pull request [Hiero Website Repository] (https://github.com/hiero-ledger/hiero-website/pulls). 

When submitting a blog about the Python SDK, you'll need to fork the hiero-website repository, submit an issue, solve it and create a pull request.

Detailed steps:

1. **Search Existing Blog Posts**: If a very similar blog posts already exists, consider how to distinguish it slightly or build on the solution. For example, whether you'd like to add to that existing blog as a pull request, if you'd like to create a follow-up blog post or if you'd like to change topic slightly.
2. **Create a Blog Post New Feature Suggestion**: visit [Hiero Website Issues] (https://github.com/hiero-ledger/hiero-website/issues). Click on the green button "New Issue" at the top right, select Feature and create a brief proposal for your blog post.
3. **Fork the Hiero Website Repo**: clone or fork fork of the hiero website code. Click the fork button on the top right. Congratulations, you now have a copy of the codebase!
4. **Create a New Branch**: do not create your blog post on the main brach, rather, create a new branch titled with your blog post.
5. **Write Your Blog Post**: Locate /hiero-website/content/posts. Here, create a {blog_post_title}.md and inside it, write your blog post. The hiero blog requires blogs to be written in markdown, which is why it is .md. Ensure there is an easy-to-read structure such as headings and subheadings. Focus on the text content; will ensure correct formatting in the next step.
6. **Transform to Markdown Format**: We will take your text blogpost.md and add correct markdown annotations to aspects such as headings, subheadings, bullet points, bold text so the blog post publishes with correct formatting on the hiero webpage. Markdown is simple, you can learn more about Markdown.md here [Introductory Markdown Guide] (https://www.markdownguide.org/basic-syntax/). AI tooling can also assist.
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

8. **Commit Locally**: commit your blog post solution on your branch. Well done!
9. **Create a Pull Request to the Hiero Website**: visit [Hiero Website Pull requests] (https://github.com/hiero-ledger/hiero-website/pulls). Your recent commit to your local branch should show up as an item to pull request. Click create pull request. In that pull request form, add the link to your issue in step 2.
10. **Check Hugo Preview**: preview your pull request is as expected using the Hugo preview link that shows up as a check in your pull reuqest. Ensure all tests pass.
11. **Wait for Reviews**: the Hiero website community will review your new blog post and publish it once approved.

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
