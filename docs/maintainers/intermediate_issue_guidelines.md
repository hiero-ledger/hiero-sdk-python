# Intermediate Issue Guidelines — Hiero Python SDK

## How to Use This Document

This guide supports maintainers and issue creators who use the **Intermediate** label
in the Hiero Python SDK repository.

It helps:

**Issue creators:**
- Describe moderately complex tasks clearly  
- Set expectations around scope and independence  
- Provide enough context without over-prescribing solutions  

**Maintainers:**
- Apply the Intermediate label consistently  
- Keep issue difficulty levels clear and helpful  

This isn’t a rulebook, and it’s not meant to limit what kinds of contributions are welcome.  
All contributions — from small fixes to major improvements — are valuable to the Hiero project.

The **Intermediate** label highlights work that involves investigation, reasoning,
and ownership — while staying well-scoped and safe to review.

---

## Purpose

Intermediate Issues represent the **next step after Beginner Issues**.

They’re a great fit for contributors who:

- Are comfortable navigating the codebase  
- Enjoy investigating how things work  
- Are ready to take more ownership of their changes  

These issues help contributors grow their confidence in:

- Understanding existing behavior  
- Making thoughtful, localized changes  
- Working more independently  

---

## What to Expect

Intermediate Issues are designed for contributors who:

- Are familiar with the Python SDK structure  
- Can read and reason about existing implementations  
- Are comfortable working across multiple files  
- Can ask focused questions when needed  

These issues usually involve more exploration than Beginner Issues,
but still have clear goals and boundaries.

---

## How Intermediate Issues Usually Feel

Intermediate Issues often:

- Involve multiple related files  
- Require understanding existing behavior  
- Leave room for thoughtful implementation choices  
- Stay focused on a specific, well-defined goal  

They’re a great fit for contributors who enjoy learning by digging into the code.

---

## Common Types of Intermediate Work

Here are examples of tasks that often fit well at this level:

### Core SDK Changes
- Small-to-medium behavior changes with clear intent  
- Bug fixes that require investigating existing logic  
- Localized refactors for clarity or maintainability  
- Improvements to existing APIs without breaking contracts  

### Refactors & Code Quality
- Refining overly broad or imprecise type hints  
- Reducing duplication or complexity  
- Improving internal abstractions with clear justification  

### Documentation & Guides
- Writing new documentation for existing features  
- Clarifying developer guides based on real usage  
- Documenting non-obvious workflows  
- Updating docs to reflect recent changes  

### Examples & Usability
- Creating new examples for existing features  
- Improving examples based on user feedback  
- Refactoring examples to demonstrate best practices  

### Tests
- Adding new tests for existing functionality  
- Extending coverage for edge cases  
- Refactoring tests for clarity and structure  

---

## Usually Not Good Fits

- Purely mechanical tasks  
- Fully scripted changes  
- Large architectural redesigns  
- Long-term, multi-phase projects  
- Work requiring deep protocol or DLT expertise  

These tasks may be a better fit for **Good First Issue** or **Beginner** labels.

If a task:

- Involves major design decisions  
- Affects core architecture or APIs  

…it may be a better fit for the **Advanced** label.

---

## Typical Scope & Time

Intermediate Issues are usually:

- ⏱ **Estimated time:** 1–3 days  
- 📄 **Scope:** Multiple related files  
- 🧠 **Challenge level:** Investigation, reasoning, and ownership  

They’re designed to be achievable in a single pull request.

---

## Example: A Well-Formed Intermediate Issue

### Add optional child receipt support to TransactionReceiptQuery

The Python SDK’s `TransactionReceiptQuery` currently returns only the parent
transaction receipt, even when child receipts are available.

The mirror node API supports returning child receipts, and similar query types
in the SDK already support optional configuration flags.

This makes it harder to inspect scheduled or child transactions without
additional manual queries.

Relevant files:
- `hiero_sdk/query/transaction_receipt_query.py`
- `examples/query/transaction_receipt_query.py`

### Expected Outcome

Add an optional configuration flag that allows callers to request child receipts.

The change should:

- Be opt-in (default behavior stays the same)  
- Reuse existing receipt parsing logic  
- Follow existing query configuration patterns  
- Avoid breaking public APIs  

Example usage:

```python
receipt = (
    TransactionReceiptQuery()
    .set_transaction_id(tx_id)
    .set_include_children(True)
    .execute(client)
)
```
### Implementation Notes

Likely steps:
- Add an optional boolean flag (e.g. include_children)
- Propagate the flag to the mirror node request
- Update response parsing to include child receipts
- Update the example file
- Add or adjust unit tests
- Similar patterns exist in other query classes with optional flags.

## Support & Collaboration
- Intermediate Issues are supported through:
- Issue and PR discussions
- Maintainer and community feedback

Support focuses on:
- Helping contributors reason about existing behavior
- Clarifying boundaries and constraints
- Ensuring changes stay safe and well-scoped
- The goal is to build confidence while protecting the stability of the SDK.

Maintainer Guidance
- An issue is often a good fit for the Intermediate label when it:
- Builds naturally on Beginner Issues
- Requires investigation and interpretation
- Has clear intent but multiple valid approaches
- Includes enough context to avoid breaking changes
- Can be completed in a single PR

Intermediate Issues are about growing skills —
through exploration, reasoning, and thoughtful ownership.