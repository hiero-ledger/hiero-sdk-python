# Good First Issue (GFI) Guidelines

## Purpose

This document defines what qualifies as a **Good First Issue (GFI)** for SDKs in this repository.

Good First Issues are intended to:
- Help new contributors get started successfully
- Reduce ambiguity for maintainers when labeling issues
- Provide **SDK-level clarity**, beyond organization- or project-level guidance

While higher-level guidance exists (e.g., at the Hiero level), this document focuses specifically on **SDK expectations**.

---

## What Is a Good First Issue?

A Good First Issue should be:
- Narrow in scope
- Low risk
- Easy to test or validate
- Achievable without deep domain knowledge of the SDK

Below are examples of changes that are generally considered good first issues.

---

## Examples of Good First Issues

### 1. Small, Focused Code Changes

- Narrow changes or additions to existing `src` functionality
- Uses common Python skills
- Can be tested by adding to an existing test

**Examples:**
- Adding or improving `__str__` functions
- Adding or improving `__repr__` functions
- Simple typing fixes (e.g., return type hints, resolving basic type conflicts)

---

### 2. Refactoring Existing Examples

- Separating existing examples into smaller helper functions
- Consolidating overly split examples into a single, clearer function
- Improving readability without changing behavior

---

### 3. Documentation Improvements

Documentation-only changes are excellent GFIs.

**Examples:**
- Adding or improving module docstrings
- Adding or improving function docstrings
- Adding inline comments to clarify logic
- Improving or adding `print` statements for clarity in examples

---

### 4. Improvements to Existing Examples

- Adding small, incremental steps to examples to better demonstrate functionality
- Clarifying edge cases or expected outputs
- Improving naming or structure for educational purposes

---

### 5. Test Enhancements (Limited Scope)

- Small additions to **existing** unit or integration tests
- Improving clarity or coverage of an existing test

---

## What Is *Not* a Good First Issue

The following are **generally not considered Good First Issues**:

- Creation of entirely new examples
- Creation of entirely new unit tests
- Creation of entirely new integration tests
- Large refactors
- Changes requiring deep architectural or domain knowledge
- Features that introduce new public APIs

These may still be valuable contributions, but they are better suited for more experienced contributors.

---

## SDK-Specific Guidelines

Each SDK **may extend or refine** these guidelines based on its own needs.

SDK maintainers are encouraged to:
- Add a short SDK-specific section
- Call out any exceptions or special cases
- Document SDK-specific tooling or constraints

This approach allows:
- Consistent contributor experience across SDKs
- Easy updates without changing organization-wide guidance

---

## Maintainer Responsibility

Maintainers should:
- Label issues as `good first issue` only when they meet these guidelines
- Provide clear issue descriptions and acceptance criteria
- Include pointers to relevant files, examples, or tests when possible

Clear labeling and descriptions significantly improve the contributor experience.

---

## Updating These Guidelines

These guidelines are expected to evolve.

If you believe changes are needed:
- Open a discussion or pull request
- Propose SDK-specific additions rather than broad changes when possible

---

## Summary

## How to Contribute
We welcome contributions from everyone! To get started, please follow these steps:
1. **Fork the repository:** Click the "Fork" button at the top right of this page to create your own copy of the project.
2. 2. **Create a new branch:** Before making any changes, create a new branch to work on. This keeps your changes separate from the main project.
   3. 3. **Make your changes:** Now you can make your changes to the code or documentation.
      4. 4. **Commit your changes:** Once you're happy with your changes, commit them with a clear and descriptive message.
         5. 5. **Open a pull request:    ** Finally, open a pull request to submit your changes for review.
Good First Issues should be:
- Small
- Clear
- Low-risk
- Educational

When in doubt, favor issues that help contributors learn the SDK without overwhelming them.
