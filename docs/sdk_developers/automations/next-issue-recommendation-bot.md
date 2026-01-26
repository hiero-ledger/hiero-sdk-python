# Next Issue Recommendation Bot

## Overview

The Next Issue Recommendation Bot is an automated GitHub Actions workflow designed to improve contributor retention by recommending relevant issues to contributors after their first successful pull request merge. This bot specifically targets contributors who complete "Good First Issue" or "beginner" level issues, helping them find their next contribution opportunity.

## Trigger Conditions

The bot triggers under the following conditions:

1. **Automatic Trigger**: When a pull request is merged (`pull_request_target` event with `closed` type)

The workflow only runs when:
- The pull request has been merged (`github.event.pull_request.merged == true`)
- The merged PR is linked to an issue with "Good First Issue" or "beginner" labels
- The linked issue is not labeled as "intermediate" or "advanced"

## Recommendation Logic

### Issue Detection

The bot parses the pull request body to find linked issues using regex patterns that match:
- `Fixes #ISSUE_NUMBER`
- `Closes #ISSUE_NUMBER` 
- `Resolves #ISSUE_NUMBER`
- `Fix #ISSUE_NUMBER`
- `Close #ISSUE_NUMBER`
- `Resolve #ISSUE_NUMBER`

### Recommendation Strategy

1. **For Good First Issue completers**:
   - First searches for unassigned issues with "beginner" label
   - Falls back to unassigned "Good First Issue" issues if no beginner issues found

2. **For beginner issue completers**:
   - Searches for unassigned issues with "beginner" label
   - Falls back to unassigned "Good First Issue" issues if no beginner issues found

3. **Fallback behavior**:
   - If no repository issues are available, provides link to organization-wide good first issues
   - Limits recommendations to up to 5 issues to avoid overwhelming contributors

## Comment Content

The bot posts a congratulatory comment that includes:

- **Congratulations message**: Thank you and encouragement for the contribution
- **Recommended issues**: List of up to 5 relevant issues with:
  - Issue title and direct link
  - Brief description (truncated to 150 characters)
- **Repository engagement**: 
  - Direct link to star the repository
  - Direct link to watch the repository for notifications
- **Community resources**: Link to Discord community for questions
- **Fallback message**: Organization-wide good first issues link if no repo issues available

### Example Comment Structure

```markdown
<!-- next-issue-bot-marker -->

🎉 **Congratulations on your first merged contribution!**

Thank you for your contribution to the Hiero Python SDK! We're excited to have you as part of our community.

Here are some beginner-level issues you might be interested in working on next:

1. [Issue Title](https://github.com/owner/repo/issues/123)
   Brief description of the issue...

2. [Another Issue](https://github.com/owner/repo/issues/456)
   Another brief description...

🌟 **Stay connected with the project:**
- ⭐ [Star this repository](https://github.com/owner/repo)
- 👀 [Watch this repository](https://github.com/owner/repo/watchers)

We look forward to seeing more contributions from you! If you have any questions, feel free to ask in our [Discord community](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md).

From the Hiero Python SDK Team 🚀
```

## Idempotent Behavior

The bot includes duplicate prevention by:

- Wrapping comments with HTML marker `<!-- next-issue-bot-marker -->`
- Checking existing PR comments for the marker before posting
- Skipping if a comment already exists
- This ensures only one recommendation comment per PR

## Technical Implementation

### Workflow File

**Location**: `.github/workflows/bot-next-issue-recommendation.yml`

**Key features**:
- Uses pinned action versions per project conventions
- Minimal permissions (`pull-requests: write`, `issues: read`, `contents: read`)
- Concurrency control to prevent duplicate runs

### Script File

**Location**: `.github/scripts/bot-next-issue-recommendation.js`

**Key components**:
- GitHub REST API integration for issue and comment operations
- Regex parsing for linked issue detection
- Search queries with label filtering
- Error handling and logging

## Testing

The bot can be tested through:

1. **Fork testing**: Test workflow behavior in forks before production deployment
2. **GitHub CLI testing**: Local testing with appropriate environment variables

**Note**: The workflow only triggers automatically when PRs are merged. Manual testing requires creating test PRs and merging them in a test environment.

## Permissions

The workflow requires minimal permissions:
- `pull-requests: write` - To post comments on pull requests
- `issues: read` - To fetch issue details and search for recommendations
- `contents: read` - To access the script file

## Troubleshooting

### Common Issues

1. **No linked issues found**: Ensure PR body contains "Fixes #123" or similar pattern
2. **Permission errors**: Verify workflow has required permissions
3. **Rate limiting**: GitHub API limits are handled by the GitHub Actions runner
4. **Duplicate comments**: Bot checks for existing markers to prevent duplicates

### Debug Information

The bot provides detailed logging:
- PR number and dry-run status
- Linked issue detection results
- Issue labels found
- Search queries used
- Number of recommended issues found
- Comment posting status

## Future Enhancements

Potential improvements to consider:
- Support for custom recommendation criteria
- Integration with contributor statistics
- Personalized recommendations based on contribution history
- Support for multiple issue linking patterns
- Analytics on bot effectiveness and contributor retention
