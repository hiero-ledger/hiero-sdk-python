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

function isValidUnassignContext(issue, comment) {
  if (!issue?.number || issue.pull_request) return false;
  if (!comment?.body || !comment?.user?.login) return false;
  if (comment.user.type === 'Bot') return false;
  if (issue.state !== 'open') return false;
  return true;
}

function commentRequestsUnassign(body) {
  return (
    typeof body === 'string' &&
    /(^|\s)\/unassign(\s|$)/i.test(body)
  );
}

function buildUnassignMarker(username) {
  return `<!-- unassign-requested:${username} -->`;
}

function isCurrentAssignee(issue, username) {
  return issue.assignees?.some(a => a.login === username);
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
    if (!isValidUnassignContext(issue, comment)) {
      console.log('[unassign] Exit: invalid unassign context', {
        issueNumber: issue?.number,
        commenter: comment?.user?.login,
        issueState: issue?.state,
        isBot: comment?.user?.type === 'Bot',
      });
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
    if (!isCurrentAssignee(issue, username)) {
      console.log('[unassign] Exit: commenter is not an assignee', {
        requester: username,
        currentAssignees: issue.assignees?.map(a => a.login),
      });
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
      console.log('[unassign] Exit: unassign already requested previously', {
        requester: username,
        issueNumber,
      });
      return;
    }

    console.log('[unassign] Proceeding to unassign user', {
      requester: username,
      issueNumber,
    });

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

   console.log('[unassign] Unassign completed successfully', {
      requester: username,
      issueNumber,
   });

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
