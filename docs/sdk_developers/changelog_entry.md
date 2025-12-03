# Changelog Entry Guide

This document explains how to create proper changelog entries for the Hiero Python SDK.

## Table of Contents

- [Why Changelog Entries Matter](#why-changelog-entries-matter)
- [Required Format](#required-format)
- [Changelog Sections](#changelog-sections)
- [Step-by-Step Guide](#step-by-step-guide)
- [Examples](#examples)

## Why Changelog Entries Matter

**Every pull request MUST include a changelog entry.**

The changelog is the first place users look to understand what's new, what's fixed, and what's changed in each release. A well-written changelog entry helps users quickly understand the impact of your contribution.

## Required Format

Your changelog entry must:

1. **Link to the issue** - Include a reference to the issue your PR solves
2. **Use clear, descriptive language** - Be concise but informative
3. **Be 1-2 sentences** - Keep it brief and focused
4. **Go under [Unreleased]** - Add your entry at the top of the file, in the appropriate section under `[Unreleased]`
5. **Use proper markdown** - Follow the bullet point format

## Changelog Sections

The `[Unreleased]` section is divided into three categories. Choose the one that best fits your change:

### Added
For new features, functionality, or capabilities added to the SDK.

**Examples:**
- New API methods
- New query types
- New transaction types
- New utility functions

### Changed
For modifications to existing functionality that change behavior but aren't bug fixes.

**Examples:**
- Refactored code structure
- Updated dependencies
- Modified function signatures
- Performance improvements
- Updated documentation

### Fixed
For bug fixes that resolve incorrect behavior.

**Examples:**
- Resolved errors or exceptions
- Corrected incorrect return values
- Fixed edge cases
- Patched security vulnerabilities

## Step-by-Step Guide

1. **Open `CHANGELOG.md`** in the repository root

2. **Find the `[Unreleased]` section** at the top of the file

3. **Choose the appropriate subsection** (Added, Changed, or Fixed)

4. **Add your entry as a new bullet point** at the top of that subsection

5. **Format your entry** as:
   ```markdown
   - Brief description of your change (#IssueNumber)
   ```

6. **Ensure it's descriptive** - Readers should understand what changed and why it matters

## Examples

### ✅ Good Examples

#### Good: Clear and Descriptive
```markdown
## [Unreleased]

### Changed
- Refactor `query_balance.py` into modular, reusable functions with `setup_client()`, `create_account()`, `get_balance()`, `transfer_hbars()`, and `main()` for improved readability, maintainability, and error handling (#123)
```

**Why this is good:**
- Links to the issue (#123)
- Describes what was refactored
- Lists the specific functions created
- Explains the benefits (readability, maintainability, error handling)
- Placed correctly under [Unreleased] → Changed

#### Good: Bug Fix
```markdown
## [Unreleased]

### Fixed
- Resolve `TypeError` in `transfer_transaction.py` when passing `None` as memo parameter (#456)
```

**Why this is good:**
- Links to the issue
- Specifies the error type
- Identifies the affected file
- Describes the problematic scenario

#### Good: New Feature
```markdown
## [Unreleased]

### Added
- Add support for HIP-### token association transactions with automatic fee calculation (#789)
```

**Why this is good:**
- Links to the issue
- Clearly states what was added
- Mentions a key feature (automatic fee calculation)

### ❌ Bad Examples

#### Bad: Not Informative
```markdown
## [Unreleased]

### Changed
- Refactor `query_balance.py`
```

**Why this is bad:**
- No issue link
- Doesn't explain what was refactored or why
- Too vague - users can't understand the impact

#### Bad: Wrong Placement (Version Number Instead of Unreleased)
```markdown
## [0.1.6] - 2025-10-21

### Changed
- Refactor `query_balance.py` into modular, reusable functions (#123)
```

**Why this is bad:**
- Added under a released version instead of [Unreleased]
- Version numbers and dates are added by maintainers during release
- Your entry should always go under [Unreleased]

#### Bad: No Issue Reference
```markdown
## [Unreleased]

### Fixed
- Fix bug in transaction signing
```

**Why this is bad:**
- No issue link
- Too vague about what bug was fixed
- Doesn't help users understand if it affects them

## Common Mistakes to Avoid

1. **Don't add entries to released versions** - Always use `[Unreleased]`
2. **Don't forget the issue number** - Every entry needs a link like `(#123)`
3. **Don't write paragraphs** - Keep it to 1-2 sentences
4. **Don't be too technical** - Write for SDK users, not just developers
5. **Don't skip the changelog** - It's required for all PRs

## Need Help?

If you're unsure about your changelog entry:

1. Look at recent entries in `CHANGELOG.md` for inspiration
2. Ask in your pull request for feedback
3. Review this guide again
4. Check other documentation files in `docs/sdk_developers/`

Remember: A good changelog entry helps thousands of developers understand your contribution!
