# Workflow Documentation Guide

This guide establishes best practices for documenting GitHub workflows and automation scripts in the Hiero Python SDK. Well-documented workflows ensure that contributors, maintainers, and collaborators can quickly understand system behavior without unnecessary deep dives into implementation details.

## Table of Contents

- [Overview](#overview)
- [Write Great Headers](#write-great-headers)
- [Write Good Docstrings](#write-good-docstrings)
- [Make Exit Reasons Obvious](#make-exit-reasons-obvious)
- [Name Things Clearly](#name-things-clearly)
- [Documentation Checklist](#documentation-checklist)
- [Related Documentation](#related-documentation)

## Overview

When documenting workflows and automation scripts, organize documentation in this order:

1. **Header Block** - High-level explanation (purpose, trigger, rules, links)
2. **Function/Script Documentation** - Detailed behavior, assumptions, side effects
3. **Code Comments** - Exit reasons and important decisions
4. **Naming Conventions** - Clear, self-documenting names

This hierarchy ensures readers understand the system immediately without scrolling through implementation details.

---

## Write Great Headers

### What a Great Header Contains

A header should provide everything needed for initial understanding:

- **Purpose** - What problem does this solve?
- **Trigger** - When/how is this executed?
- **Major Rules** - What are the critical constraints?
- **Related Docs** - Links to associated documentation

### Example: Contributor Self-Assignment Workflow

```yaml
# PURPOSE
# -------
# Handles contributor self-assignment when a user comments "/assign".
#
# TRIGGER
# -------
# GitHub issue comment containing exactly "/assign" (case-insensitive).
#
# MAJOR RULES
# -----------
# 1. Only contributors with verified skill levels can self-assign
# 2. Never override an existing assignment
# 3. Automatically transition labels based on assignment
# 4. Notify assignee and maintainers of state changes
# 5. Validate issue is in "ready" state before allowing assignment
#
# RELATED DOCS
# -----------
# - Contributor Workflow: <your-workflow-docs>
# - Issue Guidelines: <your-issue-guidelines>
# - Issue Creating: <your-issue-creation-guide>
#
```

### Example: Labeling Bug Workflow

```yaml
# PURPOSE
# -------
# Automatically categorizes incoming issues by type (bug, feature, question)
# when first submitted, routing them to appropriate maintainers.
#
# TRIGGER
# -------
# New issue creation or direct invocation via /label command.
#
# MAJOR RULES
# -----------
# - Assign exactly one issue type label per issue
# - Use confidence threshold of 95%+ for automated categorization
# - If confidence is too low, notify maintainers for manual review
# - Preserve user-provided labels; never remove existing labels
#
# RELATED DOCS
# -----------
# - Issue Guidelines: <your-issue-guidelines>
# - Maintainer Workflow: <your-maintainer-workflow>
#
```

---

## Write Good Docstrings

Docstrings should explain intent, assumptions, side effects, and edge cases. This ensures maintainers understand not just what the code does, but why and when it applies.

### Worse Example: Unclear Intent

```python
def get_skill_level(issue_labels):
    """Gets skill level"""
    # implementation...
```

### Better Example: Clear Intent and Assumptions

```python
def determine_contributor_skill_level_from_labels(issue_labels: list[str]) -> str | None:
    """
    Determines the contributor difficulty tier for the issue.
    
    Assumes exactly one skill label should be present on the issue.
    If multiple skill labels exist, the first match in priority order is returned.
    Returns None if no skill label is found, which triggers maintainer escalation
    notifications.
    
    Args:
        issue_labels: List of GitHub label strings on the issue
        
    Returns:
        Skill level identifier (Good First Issue, Beginner, Intermediate, Advanced)
        or None if no skill label found
        
    Side Effects:
        - None. This is a pure function that only reads labels.
        
    Edge Cases:
        - Multiple skill labels: Priority order is Good First Issue > Beginner > Intermediate > Advanced
        - No labels: Returns None (expected to trigger escalation)
    """
    # implementation...
```

### Python Example

```python
def extract_issue_prerequisites(issue_body: str) -> List[str]:
    """
    Extracts listed skill prerequisites from the issue body.
    
    Looks for a "## Prerequisites" section and parses the checklist items.
    
    Assumptions:
    - Prerequisites section format is consistent with issue templates
    - Each prerequisite is a checklist item (- [ ] or - [x])
    - Unknown prerequisites are skipped with a warning log
    
    Args:
        issue_body: The markdown text of the GitHub issue
        
    Returns:
        List of prerequisite identifiers found in the issue
        
    Side Effects:
        - Logs warnings for unrecognized prerequisites
        - Does NOT validate if prerequisites are met
        
    Edge Cases:
        - Missing "## Prerequisites" section returns empty list
        - Malformed lines in prerequisites are skipped silently
        - Duplicate prerequisites are preserved as-is
    """
    # implementation...
```

---

## Make Exit Reasons Obvious

When code exits early or returns a specific state, the reason should be immediately clear. Use clear comments to explain why the function returns or terminates.

### Worse Example: Unclear Exit Condition

```python
if issue.assignees:
    return
```

### Better Example: Clear Exit Reason

```python
# Safety gate: never override an existing assignment.
# If someone is already assigned, this workflow must not change it.
if issue.assignees:
    return create_comment(
        issue,
        f"Cannot self-assign: issue is already assigned to @{issue.assignees[0].login}"
    )
```

### Python Example: Clear Exit Conditions

```python
def validate_assignment_prerequisites(contributor_id: str, issue: Issue) -> bool:
    """Validate that a contributor can be assigned to this issue."""
    
    # Exit condition 1: Check contributor exists and is active
    contributor = get_contributor(contributor_id)
    if not contributor or not contributor.is_active:
        log_warning(f"Contributor {contributor_id} not found or inactive")
        return False
    
    # Exit condition 2: Verify issue has required skill labels
    skill_labels = extract_skill_labels(issue)
    if not skill_labels:
        log_error(f"Issue {issue.number} missing skill level label")
        return False
    
    # Exit condition 3: Check contributor skill matches issue requirement
    required_skill = skill_labels[0]
    if not contributor_has_skill(contributor_id, required_skill):
        log_info(f"Contributor {contributor_id} lacks skill: {required_skill}")
        return False
    
    return True
```

---

## Name Things Clearly

Use descriptive names that reveal intent. Function names should be action-oriented and specific.

### Worse Examples: Vague/Generic Names

```python
make_msg2()         # What kind of message? Why "2"?
handle()            # Too generic
process()           # Too generic
check()             # Check what?
do_test()           # Do what test?
```

### Better Examples: Clear, Specific Names

```python
build_prerequisite_not_met_comment()       # Creates a specific comment type
validate_skill_level_label()               # What it validates
notify_maintainers_of_escalation()         # What it notifies and why
extract_skill_level_from_labels()          # What it extracts and from where
verify_contributor_has_required_skill()    # Specific check being performed
transition_issue_to_ready_state()          # Specific state transition
```

### Python Examples

```python
# Better: Clear, Action-Oriented Names
def fetch_contributor_skill_level_from_database(contributor_id: str):
    """Retrieve a contributor's verified skill tier."""
    pass

def validate_issue_meets_readiness_criteria(issue: Issue) -> tuple[bool, str]:
    """Returns (is_valid, reason_if_invalid)."""
    pass

def transition_issue_labels_on_assignment(
    issue: Issue, 
    old_skill_level: str, 
    new_skill_level: str
) -> None:
    """Remove old skill label and apply new one."""
    pass
```

---

## Documentation Checklist

When documenting a workflow or automation script, ensure:

- Header block includes PURPOSE, TRIGGER, MAJOR RULES, and RELATED DOCS
- Each function has a docstring explaining intent, assumptions, side effects, and edge cases
- Exit conditions are clearly documented with comments explaining why the function returns early
- Function names are descriptive and action-oriented (avoid generic names like `make`, `do`, `process`, `handle`)
- Variable names reveal their purpose and content type
- Complex logic is explained with inline comments for maintainability
- Related documentation is linked so readers can navigate the ecosystem
- Examples of expected behavior are provided for non-obvious workflows

---

## Related Documentation

- [Contributor Workflow](../sdk_developers/workflow.md)
- [Issue Guidelines](../maintainers/difficulty_overview_guidelines.md)
- [Code Signing and Commits](../sdk_developers/signing.md)

---

Great workflow documentation follows a simple principle: place the most important, high-level information at the top. This allows readers to understand the system without scrolling through implementation details.

By following these guidelines, you ensure that your workflows are accessible, maintainable, and self-documenting.
