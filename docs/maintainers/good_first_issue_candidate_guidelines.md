Good first issue candidate guidelines
===================================

Purpose
-------

This document helps maintainers and contributors identify and prepare issues suitable
for the "good first issue" label. The goal is to make first contributions pleasant
and achievable for newcomers.

Criteria for a good-first-issue candidate
----------------------------------------

- Small, well-scoped: fixable in a few hours with minimal repository knowledge.
- Clear reproduction steps (if applicable) and expected behavior.
- Includes a short guide on where to start in the codebase and suggested files to edit.
- Contains tests or instructions for manual verification when possible.
- Does not require privileged access or large infra changes.

Maintainer checklist before labeling
------------------------------------

1. Confirm the issue is independent and does not block on other work.
2. Add reproduction steps or a minimal failing example if relevant.
3. Suggest a clear first-step implementation for newcomers.
4. Provide links to related docs or code paths (files/functions) to edit.
5. Optionally add a test or a minimal script to reproduce the issue.

Suggested PR template note for contributors
-------------------------------------------

When opening a PR for a `good first issue`, please include:

- A short description of the change and how it fixes the issue.
- Steps you took to verify the fix (tests run or manual steps).
- Any follow-ups or improvements that remain out of scope.

Maintainers: use this file to standardize and streamline onboarding for new contributors.
