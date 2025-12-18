# Good First Issue — Candidate Guidelines

This document explains the purpose of the **`good first issue: candidate`** label, when to use it, and when an issue should be promoted to a full **Good First Issue**.

## Table of Contents

- [Why We Use a "Candidate" Label](#-why-we-use-a-candidate-label)
- [When to Use the Candidate Label](#️-when-to-use-good-first-issue-candidate)
- [What a Candidate Is NOT](#-what-a-candidate-is-not)
- [Promoting a Candidate to GFI](#-promoting-a-candidate-to-gfi)
- [Workflow Summary](#-workflow-summary)
- [Important Considerations](#important-considerations)

---

## 🎯 Why We Use a "Candidate" Label

Labeling an issue as a **Good First Issue (GFI)** signals to new contributors that the issue is:

- ✅ **Well-scoped** — clear boundaries and deliverables
- ✅ **Low risk** — minimal chance of breaking changes
- ✅ **Clearly defined** — unambiguous requirements
- ✅ **Ready to be picked up** — with minimal guidance needed

However, **not all issues start in that state**.

The **`good first issue: candidate`** label exists to:

| Purpose | Description |
|---------|-------------|
| 🚫 **Avoid premature labeling** | Prevent issues from being labeled as GFIs before they're ready |
| 🔍 **Allow refinement time** | Give maintainers space to clarify scope and requirements |
| 📊 **Set accurate expectations** | Ensure new contributors know exactly what to do |
| 📋 **Create a clear pipeline** | Establish a workflow for curating high-quality GFIs |

This approach helps us prioritize **quality over quantity** when advertising beginner-friendly work.

---

## 🏷️ When to Use `good first issue: candidate`

Apply the **candidate** label when an issue:

### ✅ Fits the General Criteria

- *Might* be suitable as a GFI based on initial assessment
- Fits within the [allowed categories](./good_first_issues_guidelines.md#allowed-categories) of GFI work
- Appears to be small in scope and low risk

### ⏳ Still Needs Work

- **Needs clarification** — requirements are ambiguous or incomplete
- **Needs refinement** — scope could be narrowed or better defined
- **Needs confirmation** — maintainer review required to verify suitability
- **Needs acceptance criteria** — clear success conditions not yet defined

### 📝 Example Scenarios

| Scenario | Why Use Candidate? |
|----------|-------------------|
| User reports a documentation gap | Needs scoping to determine exact changes required |
| Bug in example code identified | Need to confirm it's isolated and straightforward to fix |
| Type annotation improvement suggested | Need to verify it doesn't affect runtime behavior |
| Test assertion missing | Need to confirm it extends existing tests only |

---

## 🚦 What a Candidate Is NOT

The **candidate** label should **NOT** be used for:

### ❌ Large or Cross-Cutting Changes

Issues that span multiple modules, packages, or require architectural understanding.

### ❌ Core Protocol or SDK Logic

Changes to:
- `to_proto` / `from_proto` methods
- Serialization/deserialization logic
- Network or wire-level behavior

### ❌ Exploratory or Investigative Work

Issues where the solution path is unclear or requires research.

### ❌ Blocked Issues

Issues that depend on external decisions, other PRs, or upstream changes.

---

> ⚠️ **Important:** If an issue clearly does *not* meet GFI criteria, it should **not** be labeled as a candidate either. The candidate label is for issues that *might* qualify, not for issues that definitely won't.

---

## ✨ Promoting a Candidate to GFI

A candidate should be promoted to a full **Good First Issue** when:

### Readiness Checklist

- [ ] **Clear description** — the problem and solution are well-defined
- [ ] **Scoped appropriately** — changes are localized and low-risk
- [ ] **Acceptance criteria defined** — clear conditions for success
- [ ] **Documentation linked** — relevant guides are referenced
- [ ] **No blockers** — no dependencies on other work
- [ ] **Maintainer approved** — a maintainer has reviewed and confirmed suitability

### Promotion Process

1. **Review the candidate issue** against [GFI guidelines](./good_first_issues_guidelines.md)
2. **Add missing details** — clarify requirements, add acceptance criteria
3. **Remove `good first issue: candidate`** label
4. **Add `Good First Issue`** label
5. **Optionally notify** in comments that the issue is ready for contributors

---

## 📊 Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Issue Created                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Initial Assessment by Maintainer               │
│                                                             │
│  Is this potentially a Good First Issue?                    │
│                                                             │
│  • Small scope?                                             │
│  • Low risk?                                                │
│  • Fits allowed categories?                                 │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         ┌────────┐     ┌──────────┐    ┌──────────┐
         │   No   │     │  Maybe   │    │   Yes    │
         └────────┘     └──────────┘    └──────────┘
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Label normally  │ │ Label as      │ │ Label as      │
    │ (not GFI)       │ │ `candidate`   │ │ Good First    │
    │                 │ │               │ │ Issue         │
    └─────────────────┘ └───────────────┘ └───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Refine & Review │
                    │                 │
                    │ • Add details   │
                    │ • Define scope  │
                    │ • Set criteria  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Promote to GFI  │
                    │ when ready      │
                    └─────────────────┘
```

---

## Important Considerations

### Why This Matters

1. **Good First Issues are automatically promoted** by GitHub and Hiero, making them highly visible to potential contributors worldwide

2. **New contributors trust the GFI label** — they expect issues to be ready and achievable

3. **Poorly scoped GFIs waste contributor time** — and can discourage future contributions

4. **Quality GFIs build community** — successful first contributions lead to long-term contributors

### Best Practices

| Do | Don't |
|----|-------|
| ✅ Use candidate for uncertain issues | ❌ Rush issues to GFI status |
| ✅ Take time to refine candidates | ❌ Label obviously unsuitable issues as candidates |
| ✅ Add clear acceptance criteria before promotion | ❌ Promote candidates without review |
| ✅ Link to relevant documentation | ❌ Assume contributors know the codebase |

---

## Additional Resources

- [Good First Issue Guidelines](./good_first_issues_guidelines.md) — what qualifies as a GFI
- [Contributing Guide](../../CONTRIBUTING.md) — how to contribute
- [DCO Signing Guide](../sdk_developers/signing.md) — commit signing requirements
- [Discord Community](../discord.md) — get help from the community
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week) — weekly office hours
