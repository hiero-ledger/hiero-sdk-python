// A script to  closes pull requests without a linked issue after 3 days automatically.

// dryRun env var: any case-insensitive 'true' value will enable dry-run
const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';
const daysBeforeClose = parseInt(process.env.DAYS_BEFORE_CLOSE || '3', 10);
const requireAuthorAssigned = (process.env.REQUIRE_AUTHOR_ASSIGNED || 'true').toLowerCase() === 'true';

const getDaysOpen = (pr) =>
  Math.floor((Date.now() - new Date(pr.created_at)) / (24 * 60 * 60 * 1000));

// Check if the PR author is assigned to the issue
const isAuthorAssigned = (issue, login) => {
  if (!issue || issue.state?.toUpperCase() !== 'OPEN') return false;
  const assignees = issue.assignees?.nodes?.map(a => a.login) || [];
  return assignees.includes(login);
};

const baseMessage = `Hi there! I'm the LinkedIssueBot.\nThis pull request has been automatically closed due to the following reason(s):
`;
const messageSuffix = `Please read - [Creating Issues](docs/sdk_developers/creating_issues.md) - [How To Link Issues Workflow](docs/sdk_developers/training/workflow/how_to_link_issues.md)\n\nThank you,
From Python SDK team`

const messages = {
  no_issue: `${baseMessage} - Reason: This pull request is not linked to any issue. Please link it to an issue and reopen the pull request if this is an error.\n${messageSuffix}`,
  not_assigned: `${baseMessage} - Reason: You are not assigned to the linked issue. Please ensure you are assigned before reopening the pull request.\n${messageSuffix}`
};

// Fetch linked issues using GraphQL
async function getLinkedIssues(github, pr, owner, repo) {
  const query = `
    query($owner: String!, $repo: String!, $prNumber: Int!) {
      repository(owner:  $owner, name: $repo) {
        pullRequest(number:  $prNumber) {
          closingIssuesReferences(first: 100) {
            nodes {
              number
              state
              assignees(first: 100) {
                nodes { login }
              }
            }
          }
        }
      }
    }
  `;
  try {
    const result = await github.graphql(query, { owner, repo, prNumber: pr.number });
    const allIssues = result.repository.pullRequest.closingIssuesReferences.nodes || [];
    // Return only open issues
    return allIssues.filter(issue => issue.state === 'OPEN');
  } catch (err) {
    console.error(`GraphQL query failed for PR #${pr.number}:`, err.message);
    return null; // Signal error
  }
}

// Validation 
async function validatePR(github, pr, owner, repo) {
  const issues = await getLinkedIssues(github, pr, owner, repo);

  // Skip on API errors (fail-safe)
  if (issues === null) {
    console.log(`Skipping PR #${pr.number} due to API error`);
    return { valid: true };
  }

  if (issues.length === 0) return { valid: false, reason: 'no_issue' };

  if (requireAuthorAssigned) {
    const assigned = issues.some(issue => isAuthorAssigned(issue, pr.user.login));
    if (!assigned) return { valid: false, reason: 'not_assigned' };
  }
  return { valid: true };
}

async function closePR(github, pr, owner, repo, reason) {
  if (dryRun) {
    console.log(`[DRY RUN] Would close PR #${pr.number} ${pr.html_url} (${reason})`);
    return true;
  }

  try {
    await github.rest.issues.createComment({
      owner, repo, issue_number: pr.number,
      body: messages[reason]
    });
    await github.rest.pulls.update({
      owner, repo, pull_number: pr.number, state: 'closed'
    });
    console.log(`✓ Closed PR #${pr.number} (${reason}) link: ${pr.html_url}`);
  } catch (err) {
    console.error(`✗ Failed to close PR #${pr.number}:`, err.message);
  }
}

module.exports = async ({ github, context }) => {
  try {
    const { owner, repo } = context.repo;
  const prs = await github.paginate(github.rest.pulls.list, {
    owner, repo, state: 'open', per_page: 100
  });

  console.log(`Evaluating ${prs.length} open PRs\n`);

  for (const pr of prs) {
    const days = getDaysOpen(pr);
    if (days < daysBeforeClose)
    {
      console.log(`PR #${pr.number} link: ${pr.html_url} is only ${days} days old. Skipping.`);
      continue;
    }

    const { valid, reason } = await validatePR(github, pr, owner, repo);
    if (valid) {
      console.log(`PR #${pr.number} link: ${pr.html_url} is Valid ✓.`);
    } else {
      await closePR(github, pr, owner, repo, reason);
    }
  }
  } catch (err) {
    console.error('Unexpected error:', err.message);
  }
};
