# Advanced Issue Guidelines — Hiero Python SDK

## How to Use This Document

This guide is here to support maintainers and issue creators who use the **Advanced** label
in the Hiero Python SDK repository.

It offers shared language and examples to help:

**Issue creators:**
- Describe larger, more complex tasks clearly  
- Set expectations around scope, impact, and collaboration  
- Provide helpful context for experienced contributors  

**Maintainers:**
- Apply the Advanced label consistently  
- Keep issue difficulty labels clear and useful  

This isn’t a rulebook, and it’s not meant to limit what kinds of contributions are welcome.  
All contributions — from small fixes to major improvements — are valuable to the Hiero project.

The **Advanced** label simply highlights work that involves deeper design, broader impact,
and long-term ownership.

---

## Purpose

Advanced Issues represent **high-impact, high-responsibility work**.

They’re a great fit for contributors who:

- Have deep familiarity with the Python SDK  
- Enjoy designing solutions and evaluating trade-offs  
- Are comfortable thinking about long-term impact  

These issues often involve shaping how the SDK evolves over time.

---

## What to Expect

Advanced Issues are designed for contributors who:

- Have strong Python SDK and domain knowledge  
- Understand performance, concurrency, and API stability considerations  
- Feel comfortable proposing and discussing designs  
- Are open to conversations about breaking changes and long-term direction  

These issues usually involve more discussion, iteration, and collaboration than earlier issue levels.

---

## How Advanced Issues Usually Feel

Advanced Issues often:

- Are design-heavy  
- Affect multiple parts of the SDK  
- Have long-term maintenance impact  
- Involve discussion, iteration, and review  

They’re a great fit for contributors who enjoy tackling complex problems and shaping the future of the project.

---

## Common Types of Advanced Work

Here are some examples of tasks that often fit well at this level:

### Core SDK Changes
- Significant behavior changes with clear motivation  
- Refactors spanning multiple related subsystems  
- Improvements to core execution paths or abstractions  
- Bug fixes that require investigation across multiple layers  

### Architecture & Design
- Introducing new abstractions or subsystems  
- Improving extensibility or testability through redesign  
- Decoupling tightly coupled components  
- Addressing systemic architectural issues  

### Interfaces & Contracts
- Evolving public or internal APIs with clear rationale  
- Formalizing or refining existing contracts  
- Improving type consistency across large areas of the codebase  
- Introducing shared types or protocols  

### Documentation & Guidance
- Writing or updating architectural documentation  
- Explaining non-obvious design decisions  
- Adding migration notes or deprecation guidance  
- Aligning docs with new behavior or APIs  

### Examples & Developer Experience
- Designing new examples for advanced features  
- Updating examples to reflect new APIs or workflows  
- Improving clarity around advanced usage patterns  

### Testing & Validation
- Designing new test strategies  
- Adding comprehensive coverage for new abstractions  
- Refactoring test architecture to support new designs  
- Introducing regression tests for complex scenarios  

---

## What Advanced Issues Are *Not*

Advanced Issues are not just “bigger versions” of other issue types.

If a task:

- Can be completed by following existing patterns  
- Is mostly mechanical or scripted  
- Has very limited impact or risk  

…it may be a better fit for **Beginner** or **Intermediate** labels.

Advanced Issues usually involve:

- Design choices  
- Trade-offs  
- Broader context  
- Long-term considerations  

---

## Typical Scope & Time

Advanced Issues are usually:

- ⏱ **Estimated time:** 3+ days  
- 📄 **Scope:** Multiple modules or repository-wide  
- 🧠 **Challenge level:** Design, iteration, and long-term ownership  

They often evolve through discussion and may require multiple review cycles.

---

## Example: A Well-Formed Advanced Issue

### Implement HIP-1261 fee estimate query support in the Python SDK

The Hiero Python SDK doesn’t currently support fee estimate queries as defined in  
HIP-1261. This makes it harder for developers to programmatically estimate
transaction fees before execution.

This issue focuses on **designing and implementing full SDK support** for HIP-1261, including:

- Public APIs  
- Internal request/response handling  
- Tests and examples  

The implementation should align with the HIP specification and stay consistent
with patterns used across other SDKs.

**Reference design document:**  
https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/proposals/hips/hip-1261.md

### Suggested Steps

1. Review HIP-1261 to understand the intended behavior and constraints  
2. Design the Python SDK API surface for fee estimate queries  
3. Implement the feature across the SDK, including:
   - Public-facing query or transaction classes  
   - Internal request/response handling  
   - Validation and error handling  
4. Add unit and integration tests  
5. Provide at least one usage example  

---

## Support & Collaboration

Advanced Issues are supported through:

- Design discussions in issues and PRs  
- Maintainer and community feedback  
- Iterative review cycles  

Support focuses on:

- Exploring design options  
- Evaluating trade-offs  
- Ensuring long-term maintainability  

The goal is to build strong, well-considered solutions together.

---

## Maintainer Guidance

An issue is often a good fit for the **Advanced** label when it:

- Involves system-level thinking  
- Has long-term impact on the SDK  
- Benefits from experienced review and iteration  

---

Advanced Issues are about shaping the future of the project —  
through thoughtful design, collaboration, and long-term vision.
