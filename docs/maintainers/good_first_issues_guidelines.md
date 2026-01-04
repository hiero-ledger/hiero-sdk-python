# Good First Issue Guidelines

This document defines what we **do** and **do not** consider a *Good First Issue (GFI)* in the Hiero Python SDK.

## Table of Contents

- [Purpose](#purpose)
- [What We Consider Good First Issues](#what-we-consider-good-first-issues)
  - [Small, Focused Source Changes](#small-focused-source-changes)
  - [Typing Improvements](#typing-improvements)
  - [Documentation Improvements](#documentation-improvements)
  - [Test Improvements](#test-improvements)
- [Summary: What Is NOT a Good First Issue](#summary-what-is-not-a-good-first-issue)
- [Maintainer Guidance](#maintainer-guidance)
- [Additional Resources](#additional-resources)


---

## Purpose

The goal of a Good First Issue is to:

- ✅ **Help new contributors get onboarded successfully** by providing a clear, achievable starting point.

Good First Issues are often a contributor’s **first interaction with open source** and are intended to help them learn our workflow with confidence.


## What We Consider Good First Issues

Good First Issues are intentionally:

- ✅ Small
- ✅ Low risk
- ✅ Easy to review
- ✅ Safe for first-time contributors

Importantly, they have:

- ✅ A **very clear, explicitly described, or provided solution**
- ✅ **No requirement to interpret code behavior or make design decisions**

Below are examples that we consider good first issues:

---
### Small, Focused Source Changes

> ⚠️ **Note:** In most cases, changes to `src` functionality are **not** Good First Issues.  
> This category applies only when the change is **purely mechanical and fully specified**.

#### Allowed (rare, explicit cases only)

- Very small, explicitly described edits to existing code
- Changes that do **not** require understanding how the code is used elsewhere

#### Not Allowed

- Any change that requires deciding *how* something should behave
- Any change that affects public behavior or SDK contracts

---

### Typing Improvements

Typing changes must be **fully specified** and **mechanical**.

#### Allowed

- Adding missing return type hints **when the expected type is explicitly stated**
- Fixing incorrect or overly broad type annotations **when the correct type is provided**

#### Not Allowed

- Inferring correct types by interpreting code
- Large or cross-file typing refactors
- Resolving complex type-system issues

---

### Documentation Improvements

Documentation tasks must be **explicitly scoped** and **instruction-driven**.

#### Allowed

- Renaming variable names when new names are provided
- Fixing identified typos or grammar issues
- Making explicitly provided changes to docstrings, comments or print statements
- Splitting a large example into smaller functions
- Combining a split example into a single function

#### Not Allowed

- Writing new documentation
- Adding docstrings or comments that require interpreting code behavior
- Deciding *what* should be documented or printed
- Deciding which steps should exist

---

### Test Improvements

> ⚠️ Most test-related work belongs in **Beginner or Intermediate Issues**.

#### Allowed (rare, explicit cases only)

- Adding a clearly specified assertion to an existing test
- Small mechanical edits with no test-design decisions

#### Not Allowed

- Creating new test files
- Designing new test cases
- Extending coverage based on interpretation

---

## Summary: What Is NOT a Good First Issue

- ❌ Issues without a clearly defined or provided solution
- ❌ Tasks requiring interpretation, investigation, or initiative
- ❌ Changes to `src` functionality that affect behavior
- ❌ Creating new examples, tests, or documentation
- ❌ Work spanning multiple files or subsystems

---

### Rule of Thumb

> If a contributor must **decide what to do**,  
> it is **not** a Good First Issue.

---

## Maintainer Guidance

### Label as GFI if the issue:

- ✅ Touches a **single file or module**
- ✅ Has **clear, well-defined scope**
- ✅ Requires **no domain or protocol knowledge**
- ✅ Can be **reviewed quickly**
- ✅ Has **low risk of breaking changes**
- ✅ Has a **clear step-by-step solution**

### Do NOT label as GFI if the issue:

- ❌ Touches **multiple subsystems**
- ❌ Changes **SDK behavior or contracts**
- ❌ Requires **domain or protocol knowledge**
- ❌ Could have **unintended side effects**
- ❌ Needs **extensive review or testing**
- ❌ Requires initiative or interpretation to solve

Instead, these are better suited as **Beginner Issues**.

---

### Important Reminders

1. **Good First Issues are promoted automatically** by GitHub and Hiero, making them highly visible
2. **Good First Issues are self-assigned** (via `/assign`), so they must be achievable by anyone
3. **Quality over quantity** — prefer fewer, clearly safe GFIs
4. **Clear acceptance criteria** — every GFI should define what “done” means
5. **Link to documentation** — include relevant guides to help contributors succeed

---

## Additional Resources

- [Contributing Guide](../../CONTRIBUTING.md)
- [DCO Signing Guide](../sdk_developers/signing.md)
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)
- [Discord Community](../discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
