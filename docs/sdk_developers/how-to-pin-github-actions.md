# How to Pin GitHub Actions to a Specific Commit Hash

## Overview

When creating or updating GitHub workflows in the Hiero Python SDK, **all GitHub Actions must be pinned to a specific commit hash** rather than using floating tags.

This document explains **why pinning is required**, **how to find the correct commit hash**, and **best practices** for maintaining pinned GitHub Actions.

---

## Why Pin GitHub Actions?

GitHub Actions can be referenced in multiple ways:

```yaml
uses: owner/action@v1          # ❌ floating tag
uses: owner/action@v4          # ⚠️ major version tag
uses: owner/action@<commit> # ✅ pinned commit SHA (v2.14.0)
```

### Security and supply-chain risk

GitHub Actions referenced using tags such as `latest`, `v1`, or `v4` are **mutable** and can be updated to point to a different commit at any time. This means the code executed by a workflow can change without any modification to the workflow file itself.

If an action repository is compromised or a malicious change is introduced upstream, workflows that rely on floating tags may unknowingly execute untrusted code. This represents a significant **software supply-chain risk**.

By pinning a GitHub Action to a specific commit SHA, the exact code being executed is known and cannot change unexpectedly. This makes workflows more secure, auditable, and resistant to supply-chain attacks.

For this reason, many security tools (for example, StepSecurity) require GitHub Actions to be pinned to commit SHAs.

### Reproducibility and stability

Pinning GitHub Actions to a specific commit SHA ensures workflows are fully reproducible. The same workflow will always execute the same version of an action, regardless of new releases or tag updates made upstream.

This prevents unexpected behavior changes caused by automatic updates to floating tags and makes CI runs more predictable.

Reproducible workflows are easier to debug, audit, and maintain, since any failures can be traced back to a known and immutable version of the action.

## Step-by-step: How to find the correct commit SHA

### Step 1: Open the action’s GitHub repository

Start with the official GitHub repository for the action. Prefer repositories linked from the GitHub Marketplace and ensure the project is actively maintained.

Examples:
- actions/checkout
- step-security/harden-runner

### Step 2: Go to the Releases page

In the repository, navigate to **Releases** and open the **Latest** release.

### Step 3: Open the release tag

Click the release version (for example `v2.14.0`) to open the release details page.

### Step 4: Copy the commit SHA

From the release page, open the commit associated with the release and copy the full 40-character commit SHA.

Example SHA: 20cf305ff2072d973412fa9b1e3a4f227bda3c76

### Step 5: Update the workflow

Replace any floating or version-based reference:

```yaml
uses: step-security/harden-runner@v2
uses: step-security/harden-runner@20cf305ff2072d973412fa9b1e3a4f227bda3c76 # v2.14.0
```

## Best practices

- Always pin GitHub Actions to a full commit SHA
- Avoid floating tags such as `latest`, `v1`, or `v4`
- Keep a version comment (for example `# v2.14.0`)
- Review release notes before updating pinned SHAs
- Periodically update pinned actions to include security fixes
- Avoid deprecated or archived action repositories
