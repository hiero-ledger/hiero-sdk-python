# Developer Pre-Submission Checklist

Before submitting your PR, verify:

## Table of Contents
1. [Prior to Submission](#1-prior-to-submission)
2. [Post-Submission Verification](#2-post-submission-verification)

---

## 1. Prior to Submission ✅

- [x] All commits are signed (`-S`) and DCO signed-off (`-s`)
- [x] Changelog entry added under `## [Unreleased]`
- [x] Tests pass 
- [x] Only changes related to the issue are included
- [x] Code follows linting/formatting standards

## 2. Post-Submission Verification (Self-Check) 🔍

Once you have opened your Pull Request (PR), you must double-check the automated workflow results **BEFORE** requesting a formal review. This ensures your contribution is technically ready and saves the maintainers valuable time.

### How to Verify All Requirements on GitHub

Navigate to your PR page and use the **Commits** and **Checks** tabs to verify the following:

| Requirement | GitHub Location | Status to Look For | Action if Failed |
| :--- | :--- | :--- | :--- |
| **Commit Signature** | **Commits Tab** (Look next to the commit ID) | Must show **"Verified"** (Green badge) | Run `git reset --soft HEAD~1`, then re-commit with `git commit -S -s -m "..."` and **Force Push**. |
| **DCO Check** | **Checks Tab** | The "DCO" or "License" check must show a **Green Checkmark**. | Run `git commit --amend -s` (to add the DCO sign-off) and force push. |
| **Tests Pass (CI)** | **Checks Tab** (Look for workflows like 'Solo Integration Tests' or 'Build') | All required tests must show a **Green Checkmark**. | View the logs for the failing check to debug the test failure locally. |
| **Changelog Formatting** | **Checks Tab** (Look for 'PR Formatting / Changelog Check') | Must show a **Green Checkmark**. | Correct the `CHANGELOG.md` entry and force push. |
| **Final Code Review** | **Files Changed Tab** | Review the files yourself one last time to ensure the content and relative URLs are correct. | Fix locally, amend, and force push. |

**Goal:** You should not ask for a review until **all essential checks** (Signature, DCO, and Tests) show a green checkmark.

---

## Don't Do This ❌

- [ ] Work on the `main` branch
- [ ] Mix multiple issues in one PR
- [ ] Skip changelog updates
- [ ] Force push without `--force-with-lease` (or just `--force` if you know what you are doing)
- [ ] Include sensitive information

## Need Help?

- **Signing issues?** → [Signing Guide](signing.md)
- **Merge conflicts?** → [Merge Conflicts Guide](merge_conflicts.md)
- **Changelog format?** → [Changelog Guide](changelog_entry.md)