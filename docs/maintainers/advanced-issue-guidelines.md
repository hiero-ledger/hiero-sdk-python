# Advanced Issue Guidelines

This document defines what we **do** and **do not** consider an *Advanced Issue*.

Advanced Issues represent the **highest tier of contributor work** and are intended for contributors with deep familiarity with the codebase, strong architectural judgment, and the ability to own complex changes end-to-end.

Advanced contributors are trusted to make **high-impact decisions** that may affect core behavior, public APIs, or long-term maintainability of the SDK.

---

## Table of Contents

- [Purpose](#purpose)
- [What We Consider Advanced Issues](#what-we-consider-advanced-issues)
  - [Source Changes in `src`](#source-changes-in-src)
  - [Architecture, Design, and Refactors](#architecture-design-and-refactors)
  - [Typing, Interfaces, and Contracts](#typing-interfaces-and-contracts)
  - [Documentation and Developer Guidance](#documentation-and-developer-guidance)
  - [Examples and Public UX](#examples-and-public-ux)
  - [Testing and Validation](#testing-and-validation)
- [What Is NOT an Advanced Issue](#what-is-not-an-advanced-issue)
- [Maintainer Guidance](#maintainer-guidance)
- [Additional Resources](#additional-resources)

---

## Purpose

The goal of an Advanced Issue is to:

- ✅ Enable **high-impact, high-responsibility contributions**
- ✅ Improve core correctness, extensibility, or maintainability
- ✅ Introduce or evolve architectural patterns
- ✅ Prepare contributors for long-term ownership and stewardship

Advanced Issues assume contributors are already comfortable with:

- The full SDK development workflow
- Navigating and reasoning across many modules
- Understanding implicit invariants and contracts
- Evaluating backwards compatibility and migration risk

Contributors are expected to:

- Proactively identify risks and edge cases
- Propose and justify design decisions
- Communicate trade-offs clearly
- Take responsibility for downstream impact

---

## What We Consider Advanced Issues

Advanced Issues are:

- ✅ Clearly motivated but **not fully specified**
- ✅ Often span **multiple subsystems or layers**
- ✅ Require architectural reasoning and design judgment
- ✅ May involve **behavior changes or API evolution**
- ✅ High impact, with **medium to high risk if done incorrectly**

They differ from **Intermediate Issues** in that they:

- ❗ Require **deep conceptual understanding**
- ❗ Require **design ownership**, not just implementation
- ❗ May require proposing new abstractions or patterns
- ❗ May affect long-term API or architectural direction

---

### Source Changes in `src`

#### Allowed

- Significant behavior changes with explicit rationale
- Refactors spanning multiple related subsystems
- Changes to core execution paths or abstractions
- Bug fixes that require deep investigation across layers
- Improvements that trade short-term complexity for long-term clarity

#### Not Allowed

- Trivial or mechanical changes (use lower-tier labels)
- Changes without a clear problem statement or motivation

---

### Architecture, Design, and Refactors

#### Allowed

- Introducing new abstractions or subsystems
- Reworking existing designs to address systemic issues
- Decoupling tightly coupled components
- Improving extensibility or testability through redesign

#### Not Allowed

- Architectural churn without demonstrated benefit
- Refactors without migration or compatibility consideration

---

### Typing, Interfaces, and Contracts

#### Allowed

- Changes to public or internal interfaces with justification
- Refining or formalizing implicit contracts
- Improving type precision across large areas of the codebase
- Introducing new shared types or protocols

#### Not Allowed

- Interface changes without documented impact
- Type-system experimentation without clear benefit

---

### Documentation and Developer Guidance

#### Allowed

- Writing or revising architectural documentation
- Explaining non-obvious design decisions
- Updating guides to reflect behavioral or API changes
- Adding migration notes or deprecation guidance

#### Not Allowed

- Documentation changes disconnected from code changes
- High-level conceptual docs without implementation context

---

### Examples and Public UX

#### Allowed

- Designing new examples for advanced or complex features
- Updating examples to reflect new APIs or workflows
- Improving clarity around advanced usage patterns

#### Not Allowed

- Example changes without corresponding documentation
- Large example suites without instructional purpose

---

### Testing and Validation

#### Allowed

- Designing new test strategies or patterns
- Adding comprehensive coverage for new abstractions
- Refactoring test architecture to support new designs
- Introducing regression tests for complex scenarios

#### Not Allowed

- Skipping tests for high-impact changes
- Relying solely on existing coverage for new behavior

---

## What Is NOT an Advanced Issue

### Rule of Thumb

> If a contributor must **design systems, evaluate trade-offs,  
> and take responsibility for long-term impact**,  
> it’s an **Advanced Issue**.

> If the work can be safely completed by following existing patterns  
> without design ownership,  
> it’s **not**.

---

## Maintainer Guidance

### Label as an Advanced Issue if the issue:

- ✅ Requires architectural or design decisions
- ✅ Has multiple valid solution paths
- ✅ May affect public APIs or core behavior
- ✅ Requires careful backwards-compatibility reasoning
- ✅ Is suitable for experienced, trusted contributors

### Do NOT label as an Advanced Issue if the issue:

- ❌ Is purely mechanical or scripted
- ❌ Is well-bounded with minimal risk (use Intermediate)
- ❌ Is exploratory without clear goals
- ❌ Requires organizational or product-level decisions

---

## Additional Resources

- [Intermediate Issue Guidelines](./intermediate_issue_guidelines.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [SDK Developer Docs](../sdk_developers)
- [DCO Signing Guide](../sdk_developers/signing.md)
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)
- [Discord Community](../discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
