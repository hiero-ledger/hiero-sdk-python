/*
------------------------------------------------------------------------------
Unassign Bot

Executes When:
  - Triggered by GitHub Actions on 'issue_comment' (created)

Goal:
  Allows an assignee to unassign themselves by commenting "/unassign".

Safeguards:
  - Only works on open issues (not PRs)
  - Only the current assignee can unassign
  - Each user can only unassign once per issue
  - Repeat /unassign commands are ignored

------------------------------------------------------------------------------
*/

function commentRequestsUnassign(body) {
  return (
    typeof body === 'string' &&
    /(^|\s)\/unassign(\s|$)/i.test(body)
  );
}

function buildUnassignMarker(username) {
  return `<!-- unassign-requested:${username} -->`;
}

module.exports = async ({ github, context }) => {
  try {
    const { issue, comment } = context.payload;
    const { owner, repo } = context.repo;

    console.log('[unassign] Payload snapshot:', {
      issueNumber: issue?.number,
      commenter: comment?.user?.login,
      commenterType: comment?.user?.type,
      commentBody: comment?.body,
    });

    // Basic validation
    if (!issue?.number || issue.pull_request) {
      console.log('[unassign] Exit: not an issue or missing issue number');
      return;
    }

    if (!comment?.body || !comment?.user?.login) {
      console.log('[unassign] Exit: missing comment body or user');
      return;
    }

    if (comment.user.type === 'Bot') {
      console.log('[unassign] Exit: comment authored by bot');
      return;
    }

    if (issue.state !== 'open') {
      console.log('[unassign] Exit: issue is not open');
      return;
    }

    if (!commentRequestsUnassign(comment.body)) {
      console.log('[unassign] Exit: comment does not request unassign');
      return;
    }

    const username = comment.user.login;
    const issueNumber = issue.number;

    console.log('[unassign] Unassign command detected by', username);

    // Check if user is currently assigned
    const assignees = issue.assignees?.map(a => a.login) ?? [];
    if (!assignees.includes(username)) {
      console.log('[unassign] Exit: user is not an assignee');
      return;
    }

    // Fetch comments to check for prior unassign
    const comments = await github.paginate(
      github.rest.issues.listComments,
      {
        owner,
        repo,
        issue_number: issueNumber,
        per_page: 100,
      }
    );

    const marker = buildUnassignMarker(username);
    const alreadyUnassigned = comments.some(c =>
      typeof c.body === 'string' && c.body.includes(marker)
    );

    if (alreadyUnassigned) {
      console.log('[unassign] Exit: user already unassigned once before');
      return;
    }

    console.log('[unassign] Removing assignee');

    // Remove assignee
    await github.rest.issues.removeAssignees({
      owner,
      repo,
      issue_number: issueNumber,
      assignees: [username],
    });

    // Add hidden marker to track unassign
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issueNumber,
      body: marker,
    });

    console.log('[unassign] Unassign completed successfully');

  } catch (error) {
    console.error('[unassign] Error:', {
      message: error.message,
      status: error.status,
      issueNumber: context.payload?.issue?.number,
      commenter: context.payload?.comment?.user?.login,
    });
    throw error;
  }
};
