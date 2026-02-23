# Good First Issue Guidelines — Hiero Python SDK

## How to Use This Document

This guide is intended to help **maintainers and issue creators** use the **Good First Issue (GFI)** label consistently and effectively in the Hiero Python SDK.

It provides shared language, examples, and guidance to help:

**Issue creators:**
- Feel confident proposing a Good First Issue  
- Understand what makes an issue approachable for new contributors  
- Decide when a task might be better suited for another issue label  

**Maintainers:**
- Apply the Good First Issue label consistently  
- Keep issue difficulty labels clear, predictable, and helpful  

This document is not meant to limit contributions or discourage initiative.  
All contributions — large or small — are valuable to the Hiero project.

The Good First Issue label simply highlights tasks that are especially friendly for **first-time contributors**.

---

## Purpose

Good First Issues (GFIs) are designed to provide a **welcoming, confidence-building first contribution experience** for new community members.

They help contributors:

- Get set up successfully  
- Navigate the repository  
- Open their first pull request  

For many contributors, this is their **first interaction with open source** or with the Hiero SDK codebase.  
Good First Issues are designed to make that experience smoother by offering:

- Clear, well-scoped tasks  
- **Explicit or step-by-step implementation instructions**  
- Predictable and easy-to-verify outcomes  

The emphasis is on learning the workflow — **not** on researching behavior, making design decisions, or filling in missing context.

---

## What to Expect

Good First Issues are intended for contributors who:

- Have basic Python knowledge  
- Are familiar with Git and GitHub  
- Are new to the Hiero SDK  
- Do not yet understand the SDK’s architecture or internal design  

Ideally, everything needed to complete the task is included directly in the issue description.

If a task requires investigation, interpretation, or design judgment, it is likely a better fit for another issue label — and that is perfectly okay.

---

## What Makes a Good First Issue

A Good First Issue works best when it is:

- Clearly defined  
- **Fully specified or scripted with explicit instructions**  
- Small in scope (often a single file or location)  
- Easy to review and verify  

The solution path should feel clear and direct, allowing contributors to focus on learning the contribution process rather than figuring out what needs to be done.

### Helpful Rule of Thumb

> If a contributor must **decide what to do or how something should work**,  
> it is **not** a Good First Issue.

---

## Typical Scope & Time

Good First Issues are intentionally small and focused:

- ⏱ **Estimated time:** ~1–4 hours (including setup)  
- 📄 **Scope:** One file or a clearly defined section  
- 🧠 **Type:** Straightforward, mechanical, low-risk changes  

Most of the effort should go into getting comfortable with the workflow — not solving complex technical problems.

---

## Common Good First Issue Examples

The following are good fits for Good First Issues **when the solution is explicitly described**.

### Small, Focused Source Changes

> ⚠️ In most cases, changes to `src` functionality are **not** Good First Issues.  
> This category applies only when the change is **purely mechanical and fully specified**.

### Suitable for Good First Issues (rare, explicit cases only):
- Very small, explicitly described edits to existing code  
- Changes that do not require understanding how the code is used elsewhere  

### Not Suitable for Good First Issues
- Any change that requires deciding *how* something should behave  
- Any change that affects public behavior or SDK contracts  

---

### Typing Improvements

Typing-related Good First Issues must be **fully specified and mechanical**.

### Suitable for Good First Issues
- Adding missing return type hints when the expected type is explicitly stated  
- Fixing incorrect or overly broad annotations when the correct type is provided  

### Not Suitable for Good First Issues
- Inferring types by interpreting code behavior  
- Cross-file or large-scale typing refactors  
- Resolving complex type-system issues  

---

### Documentation Improvements

Documentation tasks must be **explicitly scoped and instruction-driven**.

### Suitable for Good First Issues
- Fixing identified typos or grammar issues  
- Replacing text with a provided version  
- Making explicitly described changes to docstrings, comments, or print statements  
- Renaming variables or examples when new names are provided  
- Splitting or combining examples when explicitly instructed  

### Not Suitable for Good First Issues
- Writing new documentation  
- Adding explanations that require interpreting code behavior  
- Deciding what should be documented  
- Choosing which steps or details should exist  

---

### Test Improvements

> ⚠️ Most test-related work is better suited for **Beginner or Intermediate Issues**.

### Suitable for Good First Issues (rare, explicit cases only):
- Adding a clearly specified assertion to an existing test  
- Small mechanical edits with no test-design decisions  

### Not Suitable for Good First Issues
- Creating new test files  
- Designing new test cases  
- Extending coverage based on interpretation  

---

## Summary: What Is NOT a Good First Issue

- ❌ Issues without a clearly defined or provided solution  
- ❌ Tasks requiring interpretation, investigation, or initiative  
- ❌ Changes to `src` functionality that affect behavior  
- ❌ Creating new documentation, examples, or tests  
- ❌ Work spanning multiple files or subsystems  

---

## Maintainer Guidance

### Label an issue as GFI if it:

- ✅ Touches a single file or clearly defined location  
- ✅ Has a clear, well-defined scope  
- ✅ Requires no domain or protocol knowledge  
- ✅ Can be reviewed quickly  
- ✅ Has low risk of unintended side effects  
- ✅ Includes explicit or step-by-step instructions  

### Do NOT label an issue as GFI if it:

- ❌ Touches multiple subsystems  
- ❌ Changes SDK behavior or contracts  
- ❌ Requires domain or protocol knowledge  
- ❌ Could introduce subtle side effects  
- ❌ Requires extensive review or testing  
- ❌ Requires interpretation or design decisions  

Such issues are better labeled as **Beginner Issues**.

---

## Important Reminders

1. Good First Issues are often promoted automatically, making them highly visible  
2. Good First Issues are typically self-assigned, so they must be achievable by anyone  
3. Quality matters more than quantity — fewer, safer GFIs are better  
4. Every GFI should clearly define what “done” means  
5. Link to relevant documentation whenever possible to help contributors succeed  

---

## Additional Resources

- [Contributing Guide](../../CONTRIBUTING.md)  
- [DCO Signing Guide](../sdk_developers/signing.md)  
- [Changelog Entry Guide](../sdk_developers/changelog_entry.md)  
- [Discord Community](../discord.md)  
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meeting/92041330205?password=2f345bee-0c14-4dd5-9883-06fbc9c60581)
