# Intermediate Issue Guidelines

This document defines what we **do** and **do not** consider an *Intermediate Issue*.

Intermediate Issues represent the **next step after Beginner Issues** and are intended for contributors who are comfortable navigating the codebase, making design-adjacent decisions, and owning a change from investigation through implementation.

⚠️ **Important:**  
Intermediate contributors will have much more advanced programming and workflow skills, but are still developing **conceptual awareness and responsibility skills**.  
While they are capable of meaningful changes, they also carry a **higher risk of introducing breaking or unintended behavior** if issues are not carefully selected and well-guided.

For this reason, **Intermediate Issues must be curated deliberately** and include enough context and guardrails to keep changes safe.

---

## Table of Contents

- [Purpose](#purpose)
- [What We Consider Intermediate Issues](#what-we-consider-intermediate-issues)
  - [Source Changes in `src`](#source-changes-in-src)
  - [Typing, Refactors, and Code Quality](#typing-refactors-and-code-quality)
  - [Documentation and Developer Guides](#documentation-and-developer-guides)
  - [Examples and Usability Improvements](#examples-and-usability-improvements)
  - [Test Improvements](#test-improvements)
- [What Is NOT an Intermediate Issue](#what-is-not-an-intermediate-issue)
- [Maintainer Guidance](#maintainer-guidance)
- [Additional Resources](#additional-resources)

---

## Purpose

The goal of an Intermediate Issue is to:

- ✅ Build technical ownership
- ✅ Encourage independent investigation and reasoning
- ✅ Develop **safe decision-making habits**
- ✅ Prepare contributors for advanced or core work

Intermediate Issues assume contributors are already comfortable with:

- The SDK development workflow
- Intermediate-level programming
- Reading and navigating multiple files

Contributors should also be able to:

- Reason about existing behavior by reading code and tests
- Identify relevant patterns elsewhere in the codebase
- Ask targeted questions when clarification is needed

---

## What We Consider Intermediate Issues

Intermediate Issues are:

- ✅ Clearly motivated and scoped
- ✅ May span **multiple related files**
- ✅ Require independent investigation, judgment, and trade-offs
- ✅ Appropriate for contributors with growing familiarity with the codebase

They differ from **Beginner Issues** in that they:

- ❗ Require **independent problem-solving**
- ❗ Require **interpreting existing behavior**
- ❗ May involve **light design or API considerations**

They differ from **Advanced Issues** in that they:

- ❗ Do **not** require deep protocol, DLT, or architectural expertise
- ❗ Do **not** involve large-scale refactors or system redesigns
- ❗ Do **not** require long-term planning or multi-phase work
- ❗ Remain localized and reviewable within a single PR

⚠️ **Risk Awareness**  
Intermediate contributors are learning how to:
- Understand API and behavior boundaries
- Avoid breaking changes
- Reason about downstream effects

As a result, Intermediate Issues **must be framed carefully** while still allowing learning.

---

### Source Changes in `src`

#### Allowed

- Small-to-medium behavior changes with clearly stated intent
- Bug fixes requiring investigation of existing logic
- Localized refactors that improve clarity or maintainability
- Improvements to existing APIs **without breaking contracts**
- Changes touching a small set of related modules

#### Not Allowed

- Large architectural refactors
- Cross-cutting changes spanning unrelated subsystems
- Protocol-level or wire-format changes without prior design discussion

---

### Typing, Refactors, and Code Quality

#### Allowed

- Medium-sized typing improvements across related files
- Refining overly broad or imprecise type annotations
- Refactors that reduce duplication or complexity
- Improving internal abstractions with clear justification

#### Not Allowed

- Repository-wide typing rewrites
- Advanced type-system experimentation
- Refactors that significantly alter behavior without clear intent

---

### Documentation and Developer Guides

#### Allowed

- Writing new documentation for existing features
- Expanding or clarifying developer guides based on code behavior
- Documenting non-obvious workflows or design decisions
- Updating documentation to reflect recent changes

#### Not Allowed

- Large documentation restructures without alignment
- Conceptual or architectural documentation
- Documentation requiring deep protocol or domain expertise

---

### Examples and Usability Improvements

#### Allowed

- Creating new examples for existing features
- Improving examples based on user confusion or feedback
- Refactoring examples to demonstrate best practices
- Enhancing output or structure to improve clarity

#### Not Allowed

- Large example suites without a clear instructional goal

---

### Test Improvements

#### Allowed

- Designing and adding new tests for existing functionality
- Extending coverage for edge cases or regressions
- Refactoring tests for clarity, structure, or maintainability
- Improving assertions to better capture intent

#### Not Allowed

- Designing new testing frameworks
- Large-scale test architecture changes
- Performance or stress testing without prior alignment

---

## What Is NOT an Intermediate Issue

### Rule of Thumb

> If a contributor must **investigate behavior, reason about trade-offs,  
> and make localized design decisions**,  
> it’s an **Intermediate Issue**.

> If the work requires **deep protocol expertise, architectural redesign,  
> or long-term planning**,  
> it’s **not**.

---

## Maintainer Guidance

### Label as an Intermediate Issue if the issue:

- ✅ Builds naturally on Beginner Issues
- ✅ Requires investigation and interpretation
- ✅ Has clear intent but multiple valid implementation paths
- ✅ Includes **enough context to avoid breaking changes**
- ✅ Can be reasonably completed in a single PR

### Do NOT label as an Intermediate Issue if the issue:

- ❌ Is purely mechanical (use Good First Issue)
- ❌ Requires minimal investigation (use Beginner Issue)
- ❌ Has a high risk of silent breaking behavior
- ❌ Requires deep protocol, DLT, or architectural expertise
- ❌ Represents long-term or strategic design work

---

## Additional Resources

- [Good First Issue Guidelines](./good_first_issues_guidelines.md)
- [Beginner Issue Guidelines](./beginner_issue_guidelines.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [DCO Signing Guide](../sdk_developers/signing.md)
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)
- [Discord Community](../discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
