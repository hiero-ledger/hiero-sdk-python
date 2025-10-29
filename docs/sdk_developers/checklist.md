# Developer PR Submission Checklist

## Table of Contents
- [Prior to Submission](#1-prior-to-submission)
- [Post-Submission Verification](#2-post-submission-verification)

---

## 1. Prior to Submission 

- All commits are signed (`-S`) and DCO signed-off (`-s`)
- Changelog entry added under `## [Unreleased]`
- Tests pass 
- Only changes related to the issue are included
- Code follows linting/formatting standards

## 2. Post-Submission Verification

Once you have opened your Pull Request (PR), you must double-check the automated workflow results **BEFORE** requesting a formal review.

### How to Verify All Requirements on GitHub

Navigate to your PR page on GitHub and use the **Checks** and **Commits** tabs to verify the following:

| Requirement | GitHub Location | Status to Look For | Action if Failed |
| :--- | :--- | :--- | :--- |
| **Commit Signature** | **Commits Tab** | Must show **"Verified"** (Green badge) | See **[Signing Guide](signing.md)** for how to set up GPG and fix unverified commits. |
| **DCO Check** | **Checks Tab** | The "DCO" or "License" check must show a **Green Checkmark**. | See **[Signing Guide](signing.md)** to ensure your commits have the DCO sign-off (`-s`). |
| **Tests Pass (CI)** | **Checks Tab** (Workflows like 'Integration Tests') | All required tests must show a **Green Checkmark**. | View the logs for the failing check to debug the error locally. |
| **Changelog Formatting** | **Checks Tab** ('PR Formatting / Changelog Check') | Must show a **Green Checkmark**. | Correct the `CHANGELOG.md` and force push. See **[Changelog Guide](changelog_entry.md)**. |

### The Files Changed Tab

The **Files Changed Tab** shows the exact **difference** between your branch and the `main` branch. This is the key document maintainers use for review.
**Your Goal:** Submitted PRs should have a diff that achieves the issue and meets all items in the pre-submit checklist.

---

## Don't Do This 

- Mix multiple issues in one PR
- Skip changelog updates
- Force push without `--force-with-lease`

## Need Help?

- **Signing issues?** → [Signing Guide](signing.md)
- **Merge conflicts?** → [Merge Conflicts Guide](merge_conflicts.md)
- **Changelog format?** → [Changelog Guide](changelog_entry.md)