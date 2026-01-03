# Beginner Issue Guidelines

This document defines what we **do** and **do not** consider a *Beginner Issue* in the Hiero Python SDK.

Beginner Issues represent the **next step after Good First Issues** and are intended for contributors who are ready to take on slightly more responsibility and decision-making.

---

## Table of Contents

- [Purpose](#purpose)
- [What We Consider Beginner Issues](#what-we-consider-beginner-issues)
  - [Source Changes in `src`](#source-changes-in-src)
  - [Typing and Code Quality Improvements](#typing-and-code-quality-improvements)
  - [Documentation Improvements](#documentation-improvements)
  - [Improvements to Examples](#improvements-to-examples)
  - [Test Improvements](#test-improvements)
- [What Is NOT a Beginner Issue](#what-is-not-a-beginner-issue)
- [Maintainer Guidance](#maintainer-guidance)
- [Additional Resources](#additional-resources)

---

## Purpose

The goal of a Beginner Issue is to:

- ✅ Build confidence and independence
- ✅ Encourage light investigation
- ✅ Prepare for intermediate work

Beginner Issues assume contributors are already familiar with:

- Basic SDK workflow
- Basic Git
- At least beginner level programming
- Reading and navigating some of the codebase

---

## What We Consider Beginner Issues

Beginner Issues are:

- ✅ Well-scoped
- ✅ Encourage light investigation
- ✅ Lightly challenging
- ✅ Welcome questions and discussion

They differ from Good First Issues in that they:

- ❗ Require **some initiative and coding experience**
- ❗ Require **working to understand existing behavior**
- ❗ Are not purely mechanical

Here are some examples:

### Source Changes in `src`

#### Allowed

- Implementing or improving `__str__` or `__repr__` methods
- Small, localized improvements to utility functions
- Minor behavior changes with clearly stated intent
- Changes that require limited understanding of how existing code behaves

#### Not Allowed

- Large refactors or architectural changes
- Cross-cutting changes spanning many unrelated modules

---

### Typing and Code Quality Improvements

#### Allowed

- Adding missing type hints in simple functions
- Fixing incorrect type annotations in simple functions
- Improving type consistency in a file

#### Not Allowed

- Large-scale typing refactors
- Type hinting in advanced areas, like protobufs or complicated functions to interpret
- Type changes that significantly alter runtime behavior

---

### Documentation Improvements

#### Allowed

- Writing new documentation in simple areas or narrow areas that can be researched
- Improving or expanding existing documentation or examples

#### Not Allowed

- Creating large documentation workflows
- Documentation changes requiring deep domain knowledge
- Documentation changes requiring high-level insights

---

### Improvements to Examples

#### Allowed

- Creating simple examples that are similar to others
- Adding missing steps to better demonstrate functionality
- Improving ordering, clarity, or readability of examples
- Enhancing example output to be more instructive

#### Not Allowed

- Turning examples into production-ready implementations without significant prompting or examples

---

### Test Improvements

#### Allowed

- Extending existing tests to cover specific additional scenarios
- Adding assertions based on observed behavior
- Improving test clarity, naming, or intent

#### Not Allowed

- Creating new unit or integration test suites
- Designing complex or high-level test strategies

---
## What is Not a Beginner Issue
### Rule of Thumb

> If a contributor must **read code and make small decisions**,  
> it’s a **Beginner Issue**.

> If they must **interpret complex code or design systems**,  
> it’s **not**.

---

## Maintainer Guidance

#### Label as a Beginner Issue if the issue:

- ✅ Builds naturally on Good First Issues
- ✅ Requires light investigation or interpretation
- ✅ Has clear intent but not a fully scripted solution

#### Do NOT label as a Beginner Issue if the issue:

- ❌ Is purely mechanical (use Good First Issue instead)
- ❌ Requires protocol or DLT expertise
- ❌ Spans many unrelated parts of the codebase
- ❌ Represents architectural or design-level work

### Additional Resources

- [Good First Issue Guidelines](./good_first_issues_guidelines.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [DCO Signing Guide](../sdk_developers/signing.md)
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)
- [Discord Community](../discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
