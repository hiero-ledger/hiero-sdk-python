# Good First Issue (GFI) Frequency Guidelines

## Purpose

This document defines **how frequently Good First Issues (GFIs)** should be created and maintained for an SDK.

Clear expectations around GFI frequency help:
- Maintain a healthy contributor pipeline
- Prevent contributor overload or abandonment
- Align GFI availability with maintainer capacity and review bandwidth

These guidelines are **SDK-specific** and may differ across SDKs depending on team size, activity, and release cadence.

---

## What Is GFI Frequency?

**GFI frequency** refers to the number of open, actively maintained Good First Issues an SDK aims to support over time.

This is not a hard requirement, but a **maintainer-defined target** that helps ensure:
- Issues labeled as GFI receive timely responses
- Contributors are not left waiting without feedback
- Maintainers do not overcommit beyond their review capacity

---

## Recommended Frequency Models

Maintainers may choose one of the following models, or define a custom approach that fits their SDK.

### 1. Fixed Cadence

A predictable schedule for creating or refreshing GFIs.

**Examples:**
- One GFI per month
- One GFI every two weeks
- Two GFIs per week

This model works well for SDKs with:
- Stable maintainer availability
- Regular contributor interest
- Predictable release cycles

---

### 2. Capacity-Based (Burn Rate)

GFIs are created based on **maintainer capacity**, not time.

**Examples:**
- Maintain 1–3 open GFIs at any given time
- Only open a new GFI when an existing one is closed or inactive
- Limit GFIs to what can be reviewed within a defined SLA (e.g., 5 business days)

This model works well for:
- Small maintainer teams
- Periods of high operational load
- SDKs with fluctuating contributor demand

---

### 3. Hybrid Model

A combination of cadence and capacity.

**Examples:**
- One GFI per month, up to a maximum of 3 open GFIs
- Weekly GFI creation, paused when review backlog exceeds a threshold

---

## SDK-Specific Declaration

Each SDK is encouraged to **explicitly declare its GFI frequency policy**, for example:

```text
This SDK aims to maintain up to two active Good First Issues at any given time,
subject to maintainer availability.
