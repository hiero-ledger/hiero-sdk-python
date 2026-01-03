# Good First Issue — Candidate Guidelines

This document defines the purpose and usage of the **`good first issue: candidate`** label, and explains when and how an issue may be promoted to a full **Good First Issue (GFI)**.

The candidate label exists to protect the quality and trustworthiness of **Good First Issues** by ensuring issues are **fully specified, low-risk, and mechanically solvable** before being promoted.

---

## Table of Contents

- [Why We Use a Candidate Label](#why-we-use-a-candidate-label)
- [When to Use `good first issue: candidate`](#when-to-use-good-first-issue-candidate)
- [What a Candidate Is NOT](#what-a-candidate-is-not)
- [Promoting a Candidate to GFI](#promoting-a-candidate-to-gfi)

---

## Why We Use a Candidate Label

Labeling an issue as a **Good First Issue (GFI)** signals to new contributors that the issue is:

- ✅ Small and well-scoped
- ✅ Low risk
- ✅ Fully specified
- ✅ Safe for first-time contributors
- ✅ Ready to be picked up without interpretation or initiative

However, **many issues are not ready for that label immediately**.

They might have:
- ❗ Incomplete documentation
- ❗ Uncertainty if they are in fact a good first issue


The **`good first issue: candidate`** label exists to:

| Purpose | Description |
|--------|-------------|
| 🚫 Avoid premature labeling | Prevent partially defined or misclassified issues from being advertised as GFIs |
| 🧭 Enforce quality standards | Ensure GFIs meet strict “no interpretation required” criteria |
| 🛠 Allow refinement time | Give maintainers space to fully specify scope and solution |
| 📋 Create a clear pipeline | Establish a safe promotion path to GFI |

The candidate label is **not a softer GFI** — it is a **holding state**.

---

## When to Use `good first issue: candidate`

Apply the **candidate** label when you believe the issue is a good first issue, not documented enough, or have some doubt with its difficulty:

### ✅ Appears Potentially Suitable as a GFI

- The change is *likely* small, localized, and low risk
- The issue fits within the **allowed GFI categories** (docs, examples, typing, small mechanical edits)
- The issue is *not* exploratory and does *not* require design decisions

Suitability can be assessed [here](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/maintainers/good_first_issues_guidelines.md)

### ✅ Requires Some Refinement

One or more of the following is still missing:

- ❗ Explicit step-by-step instructions
- ❗ Clearly defined acceptance criteria

### ✅ Difficulty is Uncertain

Use the `good first issue: candidate` label when you believe it is a Good First Issue but are not sure

- ✅ Requires maintainer approval

Check by reading good first issue guidelines [here](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/maintainers/good_first_issues_guidelines.md)

If easy issues are not 'Good First Issues' are in fact 'beginner' issues.

## What a Candidate Is NOT

The **candidate** label must **NOT** be used for issues that clearly do not qualify as GFIs.

### ❌ Not for Issues Requiring Decisions

If a contributor must decide:
- *what* to change
- *how* something should behave
- *what* is correct or expected

→ the issue is **not** a candidate.

### ❌ Not for Core or Behavioral Changes

Do **not** use the candidate label for changes involving:

- SDK or protocol behavior
- Public APIs or contracts
- `to_proto` / `from_proto` logic
- Serialization, deserialization, or networking

### ❌ Not for Exploratory or Blocked Work

- Investigations or debugging tasks
- Issues dependent on other PRs or decisions
- Work requiring domain or protocol knowledge

> ⚠️ If an issue clearly does *not* meet GFI criteria, **do not label it as a candidate**.  
> The candidate label is for issues that *might* qualify after refinement — not for issues that never will.

---

## Promoting a Candidate to GFI

A candidate may be promoted to a full **Good First Issue** only when **all** of the following are true.

### ✅ Readiness Checklist

- [ ] The problem is clearly described
- [ ] The solution is **explicitly specified**
- [ ] The change is small, localized, and low risk
- [ ] The issue touches a single file or clearly defined location
- [ ] Acceptance criteria are defined and objective
- [ ] No interpretation or initiative is required

### 🔁 Promotion Process

1. Review the issue against the **Good First Issue Guidelines** [here](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/maintainers/good_first_issues_guidelines.md)
2. Add missing details, steps, and acceptance criteria
3. Remove the `good first issue: candidate` label
4. Add the **Good First Issue** label


