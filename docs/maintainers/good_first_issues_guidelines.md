# Good First Issue Guidelines

This document defines what we **do** and **do not** consider a *Good First Issue (GFI)* in the Hiero Python SDK.

## Table of Contents

- [Purpose](#purpose)
- [Allowed Categories](#allowed-categories)
  - [Small, Focused Source Changes](#-small-focused-source-changes)
  - [Typing Improvements](#-typing-improvements)
  - [Refactors of Existing Examples](#-refactors-of-existing-examples)
  - [Documentation Improvements](#-documentation-improvements)
  - [Print and Output Clarity](#-print-and-output-clarity-examples-only)
  - [Functional Improvements to Examples](#-functional-improvements-to-examples)
  - [Test Improvements](#-test-improvements-additive-only)
- [What We Do NOT Consider Good First Issues](#-what-we-do-not-consider-good-first-issues)
- [Maintainer Guidance](#-maintainer-guidance)

---

## Purpose

The goal of a Good First Issue is to:

- **Help new contributors get onboarded successfully** — providing a clear, achievable starting point
- **Build confidence with a meaningful but low-risk contribution** — ensuring success without overwhelming complexity
- **Reduce maintainer overhead during first-time contributions** — making review and guidance straightforward

These issues are intentionally:

- ✅ Small
- ✅ Low risk
- ✅ Easy to review
- ✅ Safe for first-time contributors

---

## Allowed Categories

### 🧵 Small, Focused Source Changes

Limited, localized changes to existing source files that do not alter public behavior or SDK contracts.

#### Allowed

- Adding or improving simple string helper functions
- Implementing or improving `__str__` or `__repr__` methods
- Fixing or clarifying edge cases in existing utility functions

#### Examples

- Improve formatting of a `__repr__` output
- Make a string helper more robust or readable
- Clarify handling of empty or `None` inputs in a utility function

---

### 🧩 Typing Improvements

Improvements to type annotations that increase correctness or clarity without changing runtime behavior.

#### Allowed

- Adding missing return type hints
- Fixing incorrect or overly broad type annotations
- Resolving basic type conflicts flagged by type checkers

#### Examples

- Change `-> Any` to a more specific return type
- Fix mismatched return types in conditional branches
- Tighten a `Dict[str, Any]` to a more precise type

---

### 🔄 Refactors of Existing Examples

Refactors that improve clarity, structure, or readability of **existing examples only**.

#### Allowed

- Refactoring an example for clarity or readability
- Extracting repeated logic into helper functions
- Renaming variables to be more descriptive

#### Allowed Directions

- Split a large example into smaller, named functions
- Combine a split example back into a single monolithic function for simplicity

> ⚠️ **Note:** This category applies **only** to existing examples.  
> Creating new examples is **out of scope** for GFIs.

---

### 📚 Documentation Improvements

Improvements to documentation that clarify intent or behavior without changing functionality.

#### Includes

- Module-level docstrings
- Function and method docstrings
- Inline comments that explain *why* (not what) code does something

#### Examples

- Clarify a confusing or outdated docstring
- Add explanation for non-obvious behavior
- Improve wording or structure for readability

---

### 🖨️ Print and Output Clarity (Examples Only)

Improvements to output clarity in example code.

#### Allowed

- Improving clarity of `print()` statements
- Making output more descriptive or user-friendly
- Standardizing message formatting (prefixes, spacing, context)

#### Examples

- Replace ambiguous prints like `"Done"` with meaningful context
- Add explanatory text before printing values
- Make output ordering easier to follow

---

### ⚙️ Functional Improvements to Examples

Small functional improvements that better illustrate **existing behavior** in examples.

#### Allowed

- Adding missing steps that improve understanding
- Improving ordering or structure of example code
- Clarifying error-handling paths

#### Examples

- Add an explicit setup step that was previously implied
- Improve error-handling clarity in an example
- Make control flow easier to follow

---

### 🧪 Test Improvements (Additive Only)

Small, additive improvements to **existing** tests.

#### Allowed

- Adding specific assertions to existing tests
- Extending tests to cover an obvious edge case
- Improving test names or failure messages

#### Examples

- Add an assertion for a previously untested branch
- Improve test failure messages for clarity

> ⚠️ Tests must extend **existing test files**.  
> Creating new test suites or frameworks is **out of scope**.

---

## 🚫 What We Do NOT Consider Good First Issues

The following types of changes are **explicitly out of scope** for GFIs.

---

### ❌ New Examples

- Creating entirely new examples
- Adding new example files or workflows

These require deeper understanding of intended usage patterns.

---

### ❌ New Unit or Integration Tests

- Creating new test files
- Designing new test strategies or frameworks

Test creation often requires broader architectural context.

---

### ❌ Core DLT or Protocol Logic

- Changes to `to_proto` / `from_proto`
- Modifying serialization or deserialization logic
- Any change affecting network or wire-level behavior

These areas are sensitive and require domain expertise.

---

### ❌ Cross-Cutting or Architectural Changes

- Refactors spanning multiple modules or packages
- Changes requiring understanding of multiple subsystems
- Performance optimizations or concurrency changes

These are better suited for experienced contributors.

---

## 📌 Maintainer Guidance

When evaluating whether to label an issue as a Good First Issue, consider:

### Label as GFI if the issue:

- ✅ Touches a **single file or module**
- ✅ Has **clear, well-defined scope**
- ✅ Requires **no domain or protocol knowledge**
- ✅ Can be **reviewed quickly**
- ✅ Has **low risk of breaking changes**

### Do NOT label as GFI if the issue:

- ❌ Touches **multiple subsystems**
- ❌ Changes **SDK behavior or contracts**
- ❌ Requires **domain or protocol knowledge**
- ❌ Could have **unintended side effects**
- ❌ Needs **extensive review or testing**

### Important Reminders

1. **Good First Issues are promoted automatically** by GitHub and Hiero, making them highly visible to new contributors
2. **Quality over quantity** — we prefer fewer, clearly safe GFIs over many ambiguous ones
3. **Clear acceptance criteria** — every GFI should have well-defined success conditions
4. **Link to documentation** — include relevant guides to help contributors succeed

---

## Additional Resources

- [Contributing Guide](../../CONTRIBUTING.md)
- [DCO Signing Guide](../sdk_developers/signing.md)
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)
- [Discord Community](../discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
