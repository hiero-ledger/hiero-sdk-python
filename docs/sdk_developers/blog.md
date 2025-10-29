# Writing Blog Posts About the Hiero Python SDK

We welcome Hiero blog posts about our Python SDK. Blog posts have to be submitted to the hiero-website repository as a pull request [Hiero Website Repository](https://github.com/hiero-ledger/hiero-website/pulls).

When submitting a blog about the Python SDK, you'll need to fork the hiero-website repository, submit an issue, solve it and create a pull request.

## Detailed Steps

### 1. Search Existing Blog Posts

If a very similar blog post already exists, consider how to distinguish it slightly or build on the solution. For example, whether you'd like to add to that existing blog as a pull request, if you'd like to create a follow-up blog post or if you'd like to change topic slightly.

### 2. Create a Blog Post New Feature Suggestion

Visit [Hiero Website Issues](https://github.com/hiero-ledger/hiero-website/issues). Click on the green button "New Issue" at the top right, select Feature and create a brief proposal for your blog post.

### 3. Fork the Hiero Website Repo

Clone or fork the hiero website code. Click the fork button on the top right. Congratulations, you now have a copy of the codebase!

### 4. Create a New Branch

Do not create your blog post on the main branch, rather, create a new branch titled with your blog post.

### 5. Write Your Blog Post

Locate `/hiero-website/content/posts`. Here, create a `{blog_post_title}.md` and inside it, write your blog post. The hiero blog requires blogs to be written in markdown, which is why it is `.md`. Ensure there is an easy-to-read structure such as headings and subheadings. Focus on the text content; we will ensure correct formatting in the next step.

### 6. Transform to Markdown Format

We will take your text `blogpost.md` and add correct markdown annotations to aspects such as headings, subheadings, bullet points, bold text so the blog post publishes with correct formatting on the hiero webpage. Markdown is simple, you can learn more about Markdown here [Introductory Markdown Guide](https://www.markdownguide.org/basic-syntax/). AI tooling can also assist.

### 7. Preview Markdown

Preview your `blogpost.md` and check and resolve any errors. If you have been writing on Visual Studio, this is `command+shift+V` or `control+shift+V`. You can also click "Open Preview to the Side" which is a small split screen icon with a magnifying glass on the top right. You must fix errors on the raw file, not the preview file.

### 8. Add Images

At `/hiero-website/public/images/python` add a high-quality jpg featured image for your blog post in the Hiero style in `/blog_titles` and (if desired) a profile image in `/members`. You can also skip this step and comment that you need help from a maintainer to add a hiero featured image.

### 9. Add Hugo Requirements

The hiero blog is built using Hugo [Introduction to Hugo](https://gohugo.io/documentation/). We need to add instructions at the top of the markdown file for it to render correctly.

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

### 10. Commit Locally

Commit your blog post solution on your branch. Well done!

### 11. Create a Pull Request to the Hiero Website

Visit [Hiero Website Pull Requests](https://github.com/hiero-ledger/hiero-website/pulls). Your recent commit to your local branch should show up as an item to pull request. Click create pull request. In that pull request form, add the link to your issue in step 2.

### 12. Check Hugo Preview

Preview your pull request is as expected using the Hugo preview link that shows up as a check in your pull request. Ensure all tests pass.

### 13. Wait for Reviews

The Hiero website community will review your new blog post and publish it once approved.