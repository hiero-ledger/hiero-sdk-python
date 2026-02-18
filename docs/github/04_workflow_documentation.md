# Workflow Documentation Guide

This guide establishes best practices for documenting GitHub workflows and automation scripts in the Hiero Python SDK. Well-documented workflows ensure that contributors, maintainers, and collaborators can quickly understand system behavior without unnecessary deep dives into implementation details.

## Table of Contents

- [Overview](#overview)
- [Workflow YAML Documentation](#workflow-yaml-documentation)
- [Script File Documentation](#script-file-documentation)
- [Write Good Docstrings](#write-good-docstrings)
- [Make Exit Reasons Obvious](#make-exit-reasons-obvious)
- [Name Things Clearly](#name-things-clearly)
- [Documentation Checklist](#documentation-checklist)
- [Related Documentation](#related-documentation)

## Overview

GitHub workflows consist of two parts:

1. **Workflow YAML files** (`.github/workflows/*.yml`) - Define triggers and orchestrate execution
2. **Script files** (`.github/scripts/*`) - Contain the actual logic and rules

Documentation must reflect this separation:

- **YAML workflows** have minimal comments (1-2 lines) pointing to the script file
- **Script files** contain all detailed documentation: purpose, major rules, logic, assumptions, and edge cases

This separation ensures readers understand the system architecture without scrolling through implementation details.

---

## Workflow YAML Documentation

Workflow YAML files orchestrate execution but don't contain business logic. Keep documentation minimal - just a brief comment pointing to the script file.

### What to Document in YAML Files

A brief comment (1-2 lines) explaining:
- What the workflow does (briefly)
- Which script file contains the logic

**Note:** Detailed documentation belongs in the script files, not in YAML. The YAML is just the trigger/orchestration layer.

### Example: Contributor Self-Assignment Workflow

This example shows a well-documented GitHub Actions workflow (`.github/workflows/bot-gfi-assign-on-comment.yml`):

```yaml
# Handles contributor self-assignment via "/assign" comment.
# See .github/scripts/bot-gfi-assign-on-comment.js for validation logic and rules.

name: GFI Assign on /assign

on:
  issue_comment:
    types:
      - created

permissions:
  issues: write
  contents: read

jobs:
  gfi-assign:
    if: github.event.issue.pull_request == null
    runs-on: ubuntu-latest
    
    concurrency:
      group: gfi-assign-${{ github.event.issue.number }}
      cancel-in-progress: false
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6.0.1
      
      - name: Run GFI /assign handler
        uses: actions/github-script@v8.0.0
        with:
          script: |
            const script = require('./.github/scripts/bot-gfi-assign-on-comment.js');
            await script({ github, context });
```

### Example: PR Changelog Validation Workflow

This example shows a well-documented GitHub Actions workflow (`.github/workflows/pr-check-changelog.yml`):

```yaml
# Validates that PRs include changelog entries under [Unreleased].
# See .github/scripts/pr-check-changelog.sh for validation rules.

name: 'PR Changelog Check'

on:
  pull_request:
    types: [opened, reopened, edited, synchronize]

permissions:
  contents: read

jobs:
  changelog-check:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6.0.1
        with:
          fetch-depth: 0
      
      - name: Run changelog validation
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x .github/scripts/pr-check-changelog.sh
          bash .github/scripts/pr-check-changelog.sh
```

---

## Script File Documentation

Script files (`.github/scripts/*`) contain the actual logic and business rules. Most scripts in the Hiero SDK are written in JavaScript. Documentation here should be comprehensive.

### What to Document in Script Files

- **Purpose** - What problem does this script solve?
- **Called By** - Which workflow(s) execute this script?
- **Major Rules** - What are the critical constraints and validation logic?
- **Dependencies** - External packages or APIs used
- **Related Docs** - Links to associated documentation

### Example: GFI Self-Assignment Script

This example shows a well-documented script file (`.github/scripts/bot-gfi-assign-on-comment.js`):

```javascript
// PURPOSE
// -------
// Handles contributor self-assignment logic when "/assign" is commented.
// Validates prerequisites and enforces assignment rules for Good First Issues.
//
// CALLED BY
// ---------
// Workflow: .github/workflows/bot-gfi-assign-on-comment.yml
//
// MAJOR RULES
// -----------
// 1. Only allow assignment to Good First Issues
// 2. Never override an existing assignment
// 3. Check user is not on spam list
// 4. Enforce max 3 open assigned issues per user
// 5. Post helpful comment with unassigned GFI link on success
//
// DEPENDENCIES
// ------------
// - @actions/github for GitHub API access
// - @actions/core for logging
//
// RELATED DOCS
// ------------
// - Issue Guidelines: docs/maintainers/good_first_issues_guidelines.md
// - Contributor Workflow: docs/sdk_developers/workflow.md

module.exports = async ({ github, context }) => {
  // Implementation...
};
```

### Example: Changelog Validation Script

This example shows a well-documented bash script (`.github/scripts/pr-check-changelog.sh`):

```bash
#!/bin/bash
# PURPOSE
# -------
# Validates that PRs contain proper changelog entries under [Unreleased]
# before allowing merge.
#
# CALLED BY
# ---------
# Workflow: .github/workflows/pr-check-changelog.yml
#
# MAJOR RULES
# -----------
# 1. New changelog entries must exist in CHANGELOG.md
# 2. Entries must be placed under [Unreleased] section only
# 3. Entries must be under a valid category (Added, Changed, Fixed, etc.)
# 4. Entries placed under released versions will fail the check
# 5. Block merge if entries are missing or improperly placed
#
# DEPENDENCIES
# ------------
# - git for diff operations
# - grep/awk for text processing
#
# RELATED DOCS
# ------------
# - Changelog Guide: docs/sdk_developers/changelog_entry.md
# - PR Workflow: docs/sdk_developers/workflow.md

# Implementation...
```

---

## Write Good Docstrings

Docstrings should explain intent, assumptions, side effects, and edge cases. This ensures maintainers understand not just what the code does, but why and when it applies.

Automation scripts in `.github/scripts/` are written in JavaScript. Here are examples of good documentation:

### Worse Example: Unclear Intent

```javascript
/**
 * Gets skill level
 */
function getSkillLevel(issueLabels) {
  // implementation...
}
```

### Better Example: Clear Intent and Assumptions

```javascript
/**
 * Determines the contributor difficulty tier from issue labels.
 * 
 * Assumes exactly one skill label should be present on the issue.
 * If multiple skill labels exist, the first match in priority order is returned.
 * Returns null if no skill label is found, which triggers maintainer escalation
 * notifications.
 * 
 * @param {string[]} issueLabels - List of GitHub label strings on the issue
 * @returns {string|null} Skill level identifier (Good First Issue, Beginner, 
 *                        Intermediate, Advanced) or null if no skill label found
 * 
 * @sideEffects None. This is a pure function that only reads labels.
 * 
 * @edgeCases
 * - Multiple skill labels: Priority order is Good First Issue > Beginner > Intermediate > Advanced
 * - No labels: Returns null (expected to trigger escalation)
 */
function determineContributorSkillLevelFromLabels(issueLabels) {
  const skillLabels = ['Good First Issue', 'Beginner', 'Intermediate', 'Advanced'];
  
  for (const skillLabel of skillLabels) {
    if (issueLabels.includes(skillLabel)) {
      return skillLabel;
    }
  }
  
  return null;
}
```

### Another Example: Script Function Documentation

```javascript
/**
 * Extracts listed skill prerequisites from the issue body.
 * 
 * Looks for a "## Prerequisites" section and parses the checklist items.
 * 
 * @assumptions
 * - Prerequisites section format is consistent with issue templates
 * - Each prerequisite is a checklist item (- [ ] or - [x])
 * - Unknown prerequisites are skipped with a warning log
 * 
 * @param {string} issueBody - The markdown text of the GitHub issue
 * @returns {string[]} List of prerequisite identifiers found in the issue
 * 
 * @sideEffects
 * - Logs warnings for unrecognized prerequisites via console.warn
 * - Does NOT validate if prerequisites are met
 * 
 * @edgeCases
 * - Missing "## Prerequisites" section returns empty array
 * - Malformed lines in prerequisites are skipped silently
 * - Duplicate prerequisites are preserved as-is
 */
function extractIssuePrerequisites(issueBody) {
  // implementation...
}
```

---

## Make Exit Reasons Obvious

When code exits early or returns a specific state, the reason should be immediately clear. Use clear comments to explain why the function returns or terminates.

### Worse Example: Unclear Exit Condition

```javascript
if (issue.assignees.length > 0) {
  return;
}
```

### Better Example: Clear Exit Reason

```javascript
/*
 * Safety gate: never override an existing assignment.
 * If someone is already assigned, this workflow must not change it.
 */
if (issue.assignees.length > 0) {
  await github.rest.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: issue.number,
    body: `Cannot self-assign: issue is already assigned to @${issue.assignees[0].login}`
  });
  return;
}
```

### Another Example: Clear Exit Conditions

```javascript
/**
 * Validate that a contributor can be assigned to this issue.
 */
async function validateAssignmentPrerequisites(contributorId, issue, github) {
  /* Exit condition 1: Check contributor exists and is active */
  const contributor = await getContributor(contributorId, github);
  if (!contributor || !contributor.is_active) {
    console.warn(`Contributor ${contributorId} not found or inactive`);
    return false;
  }
  
  /* Exit condition 2: Verify issue has required skill labels */
  const skillLabels = extractSkillLabels(issue);
  if (skillLabels.length === 0) {
    console.error(`Issue ${issue.number} missing skill level label`);
    return false;
  }
  
  /* Exit condition 3: Check contributor skill matches issue requirement */
  const requiredSkill = skillLabels[0];
  if (!contributorHasSkill(contributorId, requiredSkill)) {
    console.info(`Contributor ${contributorId} lacks skill: ${requiredSkill}`);
    return false;
  }
  
  return true;
}
```

---

## Name Things Clearly

Use descriptive names that reveal intent. Function names should be action-oriented and specific.

### Worse Examples: Vague/Generic Names

```javascript
makeMsg2()         // What kind of message? Why "2"?
handle()           // Too generic
process()          // Too generic
check()            // Check what?
doTest()           // Do what test?
```

### Better Examples: Clear, Specific Names

```javascript
buildPrerequisiteNotMetComment()       // Creates a specific comment type
validateSkillLevelLabel()              // What it validates
notifyMaintainersOfEscalation()        // What it notifies and why
extractSkillLevelFromLabels()          // What it extracts and from where
verifyContributorHasRequiredSkill()    // Specific check being performed
transitionIssueToReadyState()          // Specific state transition
```

### Examples

```javascript
// Better: Clear, Action-Oriented Names
async function fetchContributorSkillLevelFromDatabase(contributorId) {
  // Retrieve a contributor's verified skill tier
}

function validateIssueMeetsReadinessCriteria(issue) {
  // Returns { isValid: boolean, reason: string }
}

async function transitionIssueLabelsOnAssignment(issue, oldSkillLevel, newSkillLevel, github) {
  // Remove old skill label and apply new one
}
```

---

## Documentation Checklist

### For Workflow YAML Files (`.github/workflows/*.yml`)

- Brief comment (1-2 lines) explaining what the workflow does
- Comment points to the script file that contains the logic
- Does NOT include detailed documentation like PURPOSE, TRIGGER, MAJOR RULES, or RELATED DOCS
- All detailed documentation belongs in the script file

### For Script Files (`.github/scripts/*`)

- Header block includes PURPOSE, CALLED BY, MAJOR RULES, DEPENDENCIES, and RELATED DOCS
- Each function has a docstring explaining intent, assumptions, side effects, and edge cases
- Exit conditions are clearly documented with comments explaining why the function returns early
- Function names are descriptive and action-oriented (avoid generic names like `make`, `do`, `process`, `handle`)
- Variable names reveal their purpose and content type
- Complex logic is explained with inline comments for maintainability
- Examples of expected behavior are provided for non-obvious logic

---

## Related Documentation

- [Contributor Workflow](../sdk_developers/workflow.md)
- [Issue Guidelines](../maintainers/difficulty_overview_guidelines.md)
- [Code Signing and Commits](../sdk_developers/signing.md)

---

Great workflow documentation follows a simple principle: separate orchestration from logic. 

- **Workflow YAML files** document triggers and script references
- **Script files** document major rules and implementation details

This separation ensures readers understand the system architecture without scrolling through implementation details.

By following these guidelines, you ensure that your workflows and scripts are accessible, maintainable, and self-documenting.
