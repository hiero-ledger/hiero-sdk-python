const LINKBOT_UNASSIGNED_ISSUE_MARKER = '<!-- LinkBot Unassigned Linked Issue -->';

async function getLinkedOpenIssues(github, owner, repo, prNumber) {
  const query = `
    query($owner: String!, $repo: String!, $prNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $prNumber) {
          closingIssuesReferences(first: 100) {
            nodes {
              number
              state
              assignees(first: 100) {
                nodes {
                  login
                }
              }
            }
          }
        }
      }
    }
  `;

  try {
    const result = await github.graphql(query, { owner, repo, prNumber });
    const issues = result.repository.pullRequest.closingIssuesReferences.nodes || [];
    return issues.filter(issue => issue.state === 'OPEN');
  } catch (error) {
    console.error(`Failed to fetch linked issues for PR #${prNumber}:`, error.message);
    return null;
  }
}

function isAuthorAssignedToAnyIssue(issues, authorLogin) {
  return issues.some(issue =>
    (issue.assignees?.nodes || []).some(assignee => assignee.login === authorLogin)
  );
}

module.exports = async ({ github, context }) => {
  let prNumber;
  try {
    const isDryRun = process.env.DRY_RUN === 'true';
    prNumber = Number(process.env.PR_NUMBER) || context.payload.pull_request?.number;

    if (!prNumber) {
      throw new Error('PR number could not be determined');
    }

    console.log(`Processing PR #${prNumber} for assignment check (Dry run: ${isDryRun})`);

    // For workflow_dispatch, we need to fetch PR details
    let prData;
    if (context.payload.pull_request) {
      prData = context.payload.pull_request;
    } else {
      const prResponse = await github.rest.pulls.get({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: prNumber,
      });
      prData = prResponse.data;
    }

    const authorType = prData.user?.type;
    const authorLogin = prData.user?.login;

    if (authorType === 'Bot' || authorLogin?.endsWith('[bot]')) {
      console.log(`Skipping comment: PR created by bot (${authorLogin})`);
      return;
    }

    const comments = await github.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    const alreadyCommented = comments.data.some(comment =>
      comment.body?.includes(LINKBOT_UNASSIGNED_ISSUE_MARKER)
    );

    if (alreadyCommented) {
      console.log('LinkBot unassigned-issue reminder already posted on this PR');
      return;
    }

    const linkedIssues = await getLinkedOpenIssues(github, context.repo.owner, context.repo.repo, prNumber);
    if (linkedIssues === null) {
      console.log('Could not determine linked issues. Skipping comment for safety.');
      return;
    }

    if (linkedIssues.length === 0) {
      console.log('PR has no linked open issues - missing-link workflow handles this case');
      return;
    }

    if (isAuthorAssignedToAnyIssue(linkedIssues, authorLogin)) {
      console.log('PR author is assigned to at least one linked issue - no comment needed');
      return;
    }

    const safeAuthor = authorLogin ?? 'there';
    const linkedIssueList = linkedIssues.map(issue => `#${issue.number}`).join(', ');
    const commentBody = [`${LINKBOT_UNASSIGNED_ISSUE_MARKER}` +
      `Hi @${safeAuthor}, this is **LinkBot** 👋`,
      ``,
      `🚨 **This pull request is linked to issue(s), but you are not assigned to any of them.**`,
      `If this remains unchanged, this pull request will be automatically closed.`,
      ``,
      `Linked issue(s): ${linkedIssueList}`,
      ``,
      `Please get assigned to one of the linked issues and keep the link in this PR description.`,
      `Comment \`/assign\` on the issue to request assignment (works for all issue types).`,
      `Note: assignment for intermediate/advanced issues is not automatic.`,
      ``,
      `📖 Guide:`,
      `[docs/sdk_developers/how_to_link_issues.md](https://github.com/${context.repo.owner}/${context.repo.repo}/blob/main/docs/sdk_developers/how_to_link_issues.md)`,
      ``,
      `Thanks!`
    ].join('\n');

    if (isDryRun) {
      console.log('DRY RUN: Would post the following unassigned-issue comment:');
      console.log('---');
      console.log(commentBody);
      console.log('---');
    } else {
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: commentBody,
      });
      console.log('LinkBot unassigned-issue comment posted successfully');
    }
  } catch (error) {
    console.error('Error processing PR assignment check:', error);
    console.error('PR number:', prNumber);
    console.error('Repository:', `${context.repo.owner}/${context.repo.repo}`);
    throw error;
  }
};
