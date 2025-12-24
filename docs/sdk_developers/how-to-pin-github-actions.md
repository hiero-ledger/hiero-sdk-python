# How to Pin GitHub Actions to a Specific Commit Hash

## Overview

When creating or updating GitHub workflows in the Hiero Python SDK, **all GitHub Actions must be pinned to a specific commit hash** rather than using floating tags.

This document explains **why pinning is required**, **how to find the correct commit hash**, and **best practices** for maintaining pinned GitHub Actions.

---

## Why Pin GitHub Actions?

GitHub Actions can be referenced in multiple ways:

```yaml
uses: step-security/harden-runner@v2.12.0        
uses: owner/action@v4
uses: step-security/harden-runner@20cf305ff2072d973412fa9b1e3a4f227bda3c76 # v2.14.0