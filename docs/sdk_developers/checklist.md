# Pull Request Checklist

Before submitting your PR, verify:

## Required ✅

- [ ] All commits are signed (`-S`) and DCO signed-off (`-s`)
- [ ] Changelog entry added under `[Unreleased]`
- [ ] Tests pass locally (`pytest`)
- [ ] Branch is up to date with main
- [ ] Only changes related to the issue are included
- [ ] Code follows project style (run linting tools)

## Recommended 👍

- [ ] Added tests for new functionality
- [ ] Updated documentation if needed
- [ ] Verified GitHub shows commits as "Verified"

## Don't Do This ❌

- [ ] Work on the `main` branch
- [ ] Mix multiple issues in one PR
- [ ] Skip changelog updates
- [ ] Force push without `--force-with-lease`
- [ ] Include sensitive information

## Need Help?

- **Signing issues?** → [Signing Guide](signing.md)
- **Merge conflicts?** → [Merge Conflicts Guide](merge_conflicts.md)
- **Changelog format?** → [Changelog Guide](changelog.md)