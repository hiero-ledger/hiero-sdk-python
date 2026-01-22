# Testing GitHub Actions using Forks

When developing GitHub Actions or automation bots for the SDK, it is risky to test directly on the main repository. A mistake could accidentally close valid Pull Requests, spam developers with comments, or break build pipelines.

To test safely, developers should use their personal **fork** of the repository. This guide explains how to set up a fork to mimic the main repository and test workflows effectively.

## Prerequisites

By default, GitHub Actions are often disabled on forks to save resources. You must enable them manually:

1.  Go to your fork on GitHub (e.g., `github.com/<your-username>/hiero-sdk-python`).
2.  Click on the **Settings** tab.
3.  On the left sidebar, click **Actions** > **General**.
4.  Select **Allow all actions and reusable workflows**.
5.  Click **Save**.

## The Testing Workflow

Testing a bot or action usually involves two distinct parts:
1.  **The Logic:** The code that runs the bot (e.g., the `.sh` script or `.yml` workflow).
2.  **The Trigger:** An event that causes the bot to run (e.g., a new PR, a comment, or a specific time of day).

### Step 1: Update your Fork's Main Branch
GitHub Actions usually define the "active" workflows based on the files present in the default branch (usually `main`). To test your new bot logic:

1.  Create a branch with your changes (e.g., `feat/new-bot-logic`).
2.  Push this branch to your fork.
3.  Open a Pull Request **targeting your fork's main branch** (Base: `<your-username>:main` ← Compare: `<your-username>:feat/new-bot-logic`).
4.  **Merge** this PR into your fork's `main`.

> **Note:** Your fork's `main` branch now acts as the "production" environment for your test. It contains the code that *runs* the tests.

### Step 2: Create a Test Scenario
Now that your fork has the updated logic, you need to create an event to trigger it.

1.  Create a new dummy branch (e.g., `test/trigger-bot`).
2.  Make the necessary changes to trigger the specific action (see examples below).
3.  Open a Pull Request **within your fork** (Base: `<your-username>:main` ← Compare: `<your-username>:test/trigger-bot`).

---

## Modifying Test Timescales

Real-world conditions (like "21 days of inactivity") are impractical for testing. You should temporarily modify the code in your feature branch (Step 1) to simulate these conditions immediately.

### 1. Shortening Time Thresholds
If a bot waits for **21 days**, change the variable to **0 days** or **minutes** in your script.

**Before (Production Code):**
```bash
# Wait for 21 days before marking as stale
DAYS="${DAYS:-21}"
```

**After (Testing Code):**
```bash
# Set to 0 to treat everything as immediately stale for testing
DAYS="${DAYS:-0}" 
```

### 2. accelerating Cron Schedules
If a workflow runs once a day, you don't want to wait 24 hours. Modify the `.yml` file to run frequently or allow manual triggers.

**Before:**
```yaml
on:
  schedule:
    - cron: "0 12 * * *"  # Runs at 12:00 PM daily
```

**After:**
```yaml
on:
  workflow_dispatch:      # Allows manual button click in Actions tab
  schedule:
    - cron: "*/5 * * * *" # Runs every 5 minutes
```

---

## Real World Examples

### Example 1: Testing an Unverified Commit Bot
**Goal:** Ensure the bot posts a warning comment if a PR contains unsigned commits.

1.  **Deploy Logic:** Merge the workflow file that checks for GPG signatures into your fork's `main`.
2.  **Trigger Scenario:**
    *   Create a new branch: `git checkout -b test/unsigned-commit`
    *   Make a dummy change.
    *   Commit **without** your GPG signature using the `--no-gpg-sign` flag:
        ```bash
        git commit -m "test: unsigned commit" --no-gpg-sign
        ```
    *   Push and open a PR to your fork's `main`.
3.  **Verify:** Wait a moment and check the PR timeline. The bot should post a comment or fail the check indicating the commit is unverified.

### Example 2: Testing the Inactivity Bot
**Goal:** Verify the bot unassigns users after a period of inactivity.

1.  **Modify Logic:** In your script (Step 1), set `DAYS=0` so the bot considers any issue created "now" as stale.
2.  **Deploy:** Merge this change to your fork's `main`.
3.  **Trigger Scenario:**
    *   Create a dummy Issue in your fork.
    *   Assign yourself to the Issue.
    *   Wait for the scheduled workflow to run (e.g., the 5-minute cron you set up) or manually trigger it via the Actions tab.
4.  **Verify:** Check if the bot posted a comment on the issue and removed you from the assignee list.

## Cleanup

Once you have verified the functionality works as expected:

1.  Delete your test branches (`test/trigger-bot`, etc.).
2.  Close any dummy Pull Requests and Issues in your fork.
3.  **Revert the timescale changes** in your feature branch (e.g., change `DAYS=0` back to `DAYS=21`, remove the `*/5` cron).
4.  Create a final Pull Request from your clean feature branch to the official upstream repository.