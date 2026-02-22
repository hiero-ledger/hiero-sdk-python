# 03: Workflow Best Practices

Building on the concepts from [01-what-are-workflows.md](./01-what-are-workflows.md) and
[02-architecture.md](./02-architecture.md), this guide establishes best practices for
writing and maintaining GitHub Actions workflows and their companion scripts.

## Why Best Practices Matter

Automation is powerful — but power demands discipline. Unlike application code,
workflow bugs can:

- Mass-assign or unassign contributors
- Spam dozens of users with incorrect comments
- Leak permissions or secrets
- Create irreversible state changes
- Break the entire contributor experience

A single mistake can create hours of cleanup. These best practices exist to ensure
our workflows are **safe**, **predictable**, **debuggable**, and **maintainable at
scale**.

---

## 1. Separate the Workflow from the Logic

As explained in [02-architecture.md](./02-architecture.md), we follow the
**Orchestration vs. Logic** pattern:

| Layer | Folder | Responsibility |
| :--- | :--- | :--- |
| **Workflow** (`.yml`) | `.github/workflows/` | Triggers, permissions, env setup, calling scripts |
| **Script** (`.js`/`.sh`) | `.github/scripts/` | Decisions, API calls, error handling, comments |

Avoid adding logic directly to the workflow YAML. Inline logic is brittle —
formatting is harder, some variables can become malformed, and it is difficult to
test.

### ❌ Bad: Logic in YAML

```yaml
- run: |
    ASSIGNEES=$(gh api /repos/$REPO/issues/$NUM/assignees | jq -r '.[].login')
    if [ -z "$ASSIGNEES" ]; then
      gh issue assign $NUM --assignee $USER
    fi
```

### ✅ Good: Logic in a script

```yaml
- uses: actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8.0.0
  with:
    script: |
      const script = require('./.github/scripts/bot-assign.js');
      await script({ github, context, core });
```

---

## 2. Avoid Hardcoding — Use Environment Variables

When adding values to workflows or scripts, extract them as variables rather than
hardcoding. Ideally, environment variables should be **defined in the workflow YAML
and passed to the script**.

### ❌ Bad: Hardcoded in the script

```javascript
if (team === '@hiero-ledger/core-maintainers') {
  // ...
}
```

### ✅ Good: Passed from the workflow

**Workflow YAML:**

```yaml
env:
  MAINTAINER_TEAM: '@hiero-ledger/core-maintainers'
  MAX_ASSIGNEES: '3'
  INACTIVITY_DAYS: '21'
```

**Script:**

```javascript
const TEAM = process.env.MAINTAINER_TEAM;
const MAX = parseInt(process.env.MAX_ASSIGNEES, 10);

if (team === TEAM) {
  // ...
}
```

This improves maintainability (one place to change a value) and security (secrets
stay in the workflow layer).

---

## 3. Secrets Handling

Secrets are the most sensitive part of any workflow. Follow these rules strictly:

| Rule | Why |
| :--- | :--- |
| **Never log secrets** | Even partial logging can expose tokens |
| **Never transform secrets** | String operations on secrets can leak them via error messages |
| **Never pass secrets unless required** | Minimize the blast radius of a compromise |
| **Use `${{ secrets.NAME }}`** | Always reference secrets through GitHub's secrets mechanism |

### ❌ Bad

```yaml
- run: echo "Token is ${{ secrets.GITHUB_TOKEN }}"
- run: |
    TOKEN="${{ secrets.MY_TOKEN }}"
    TRIMMED=${TOKEN:0:10}  # Transformation can leak
```

### ✅ Good

```yaml
steps:
  - run: gh api /repos/...  # gh CLI reads GITHUB_TOKEN from env
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. Permissions — Default to Read, Escalate Only When Required

Every workflow must explicitly declare permissions, scoped to the **minimum**
required.

```yaml
permissions:
  issues: write       # Only if the workflow posts comments or edits issues
  contents: read      # Default — read-only access to repo contents
  pull-requests: read # Only escalate to write if modifying PRs
```

**Never** give a workflow excessive permissions or token access. If a workflow only
reads data, it should **not** have write access.

For more on securing workflows, see
[how-to-pin-github-actions.md](../sdk_developers/how-to-pin-github-actions.md).

---

## 5. Log for Debugging and Maintainability

A workflow should not just work — it should be **easy to scale and debug**. If a
maintainer cannot diagnose a failure from logs, the workflow is incomplete.

### What to Log

Logs should show:

- What triggered execution
- What decisions were made
- Why branches were taken
- What API calls occurred
- Why exits happened

### Use Structured, Prefixed Logs

Every log line should identify the source and describe exactly what happened.

#### ❌ Bad

```javascript
console.log('assigned');
console.log('done');
```

#### ✅ Good

```javascript
console.log('[assign-bot] Issue #42 already assigned:', assignees);
console.log('[assign-bot] Exit: user has not completed a Good First Issue');
console.log('[assign-bot] Assigned user @alice to issue #42');
```

### Always Log Exits

Include logs even when exiting early, so you know why the workflow stopped and what
conditions caused it:

```javascript
if (!commentRequestsAssignment(body)) {
  console.log('[assign-bot] Exit: not an /assign request');
  return;
}
```

### What is Acceptable to Log

| ✅ Safe to log | ❌ Never log |
| :--- | :--- |
| Issue numbers | Tokens or secrets |
| Usernames | API keys |
| Label names | Private user data |
| Counts and IDs | Full event payloads |

---

## 6. Error Handling

Automation must fail **predictably** and **helpfully**. Errors fall into three
categories:

### a) Expected Failures

The user did not meet conditions (e.g., eligibility requirements). These often
warrant a helpful comment.

```javascript
if (!hasCompletedGFI) {
  await postComment(
    `Sorry @${user}, we were unable to assign you. ` +
    `You must first complete a Good First Issue.`
  );
  return;
}
```

### b) Operational Failures

The GitHub API malfunctioned or something unexpected happened. Log the error and
optionally notify the user.

```javascript
try {
  await github.rest.issues.addAssignees({ owner, repo, issue_number, assignees });
} catch (error) {
  console.error('[assign-bot] API error:', error.message);
  // Optionally comment to the user
}
```

### c) System Failures

When the workflow cannot safely proceed, tag maintainers for assistance:

```javascript
await postComment(
  `Sorry @${user}, we were unable to assign you due to a technical issue. ` +
  `Requesting @hiero-ledger/maintainers assistance.`
);
core.setFailed('System failure: ' + error.message);
```

**Never exit without logging the exit reason.** Every `return` should have a
corresponding log line so unexpected behavior can be debugged.

---

## 7. Notify Users

### When to Notify

Notify the user when:

- They attempted an action (e.g., `/assign`)
- Eligibility checks failed
- Prerequisites are missing
- They are waiting for a result

Scripts should generate an **informative comment** and post it. Silent failures
leave contributors confused.

### When to Tag Maintainers

Tag maintainers (`@hiero-ledger/maintainers`) when automation cannot safely decide:

- API unavailable or returning unexpected responses
- Ambiguous labels or state
- Permission failures
- Edge cases the script was not designed to handle

---

## 8. Safety Rules

### Pin Action Versions

All third-party actions must be pinned to a **full commit SHA**, not a floating tag.

```yaml
# ❌ Bad — floating tag
uses: actions/checkout@v4

# ✅ Good — pinned SHA with version comment
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

See [how-to-pin-github-actions.md](../sdk_developers/how-to-pin-github-actions.md)
for the full step-by-step guide.

### Treat All User Input as Untrusted

Anything coming from issue titles, comments, labels, PR bodies, or usernames should
be validated before use.

#### ❌ Bad

```javascript
body.includes('/assign');
```

#### ✅ Good

```javascript
/^\s*\/assign\s*$/i.test(body);

function isSafeSearchToken(value) {
  return /^[a-zA-Z0-9._/-]+$/.test(value);
}
```

### Watch Out with Destructive Actions

Before performing destructive actions (deleting labels, unassigning users, closing
issues), confirm:

- Correct issue / PR
- Correct state (labels, assignees)
- Not already done (idempotency)

### Avoid `pull_request_target` with Untrusted Code

`pull_request_target` runs with **write permissions on the base repository**, even
for PRs from forks. Never check out or execute code from the fork branch inside
a `pull_request_target` workflow — this allows a contributor to run arbitrary
code with your repository's write token.

```yaml
# ❌ Dangerous — executes fork code with write token
on: pull_request_target
steps:
  - uses: actions/checkout@...
    with:
      ref: ${{ github.event.pull_request.head.sha }}  # attacker-controlled
  - run: npm install && npm test  # runs attacker code
```

If you must use `pull_request_target` (e.g., to post comments on fork PRs),
keep the workflow free of any checkout or execution of PR code, and scope
permissions to the minimum required.

---

## 9. Concurrency

Workflows might be triggered multiple times simultaneously. Use concurrency controls
to prevent race conditions:

```yaml
concurrency:
  group: assign-${{ github.event.issue.number }}
  cancel-in-progress: false
```

Use `cancel-in-progress: false` for workflows that mutate state (assigning users,
posting comments) to avoid partial execution. Use `cancel-in-progress: true` for
read-only checks (linting, testing) where only the latest run matters.

---

## 10. Testing and Dry Runs

No workflow change is considered safe without testing. Because workflow bugs can
mass-edit issues, spam contributors, or leak permissions, **maintainers expect proof
of testing in PRs**.

### Fork Testing (Strongly Recommended)

Use your personal fork to validate behavior safely. You can trigger events, create
test issues, simulate comments, and inspect logs without risk to the main repository.

See [testing_forks.md](../sdk_developers/training/testing_forks.md) for the full
fork testing guide.

**Checklist:**

- [ ] Does the workflow trigger correctly?
- [ ] Have I tested various edge cases?
- [ ] Are comments formatted correctly?
- [ ] Are logs clear and informative?

### Dry-Run Techniques

Dry runs let you verify logic without performing real mutations. They divert actions
to log instead of execute.

**Workflow YAML:**

```yaml
on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Run in dry-run mode'
        type: boolean
        default: true

env:
  DRY_RUN: ${{ github.event.inputs.dry_run }}
```

**Script:**

```javascript
if (process.env.DRY_RUN === 'true') {
  console.log('[dry-run] Would assign:', username);
  return;
}

await github.rest.issues.addAssignees({ owner, repo, issue_number, assignees: [username] });
```

If dry-run is used, it should be:

- **Clear** — obvious from logs that it is active
- **Well-logged** — every skipped mutation should be logged
- **Default to true** on `workflow_dispatch`
- **Easy to maintain** — simple toggle, not complex branching

### Local Testing

Large parts of behavior can be validated locally without pushing commits:

1. Simulate the GitHub event payload (or extract from a real event)
2. Call your script directly and observe output
3. Verify decision-making, formatting, and branching

**What local testing cannot prove:**

| Cannot validate locally | Requires fork testing |
| :--- | :--- |
| GitHub permissions | ✅ |
| Actual API authorization | ✅ |
| Concurrency behavior | ✅ |
| Runner environment | ✅ |

---

## Quick Reference Checklist

Use this checklist when writing or reviewing a workflow:

| # | Practice | Check |
| :--- | :--- | :--- |
| 1 | Logic is in scripts, not YAML | ☐ |
| 2 | Values use env vars, not hardcoded | ☐ |
| 3 | Secrets are never logged or transformed | ☐ |
| 4 | Permissions are explicit and minimal | ☐ |
| 5 | Logs are structured, prefixed, and informative | ☐ |
| 6 | Errors are handled at all three levels | ☐ |
| 7 | Users are notified on failures | ☐ |
| 8 | Actions are SHA-pinned, inputs are validated | ☐ |
| 9 | Concurrency groups prevent race conditions | ☐ |
| 10 | Tested on a fork with proof in the PR | ☐ |

---

## Related Documentation

- [01: What are Workflows?](./01-what-are-workflows.md)
- [02: How Workflows Are Structured](./02-architecture.md)
- [How to Pin GitHub Actions](../sdk_developers/how-to-pin-github-actions.md)
- [Testing with Forks](../sdk_developers/training/testing_forks.md)
- [Developer PR Checklist](../sdk_developers/checklist.md)
