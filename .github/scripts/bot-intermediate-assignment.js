const COMMENT_MARKER = process.env.INTERMEDIATE_COMMENT_MARKER || '<!-- Intermediate Issue Guard -->';
const INTERMEDIATE_LABEL = process.env.INTERMEDIATE_LABEL?.trim() || 'intermediate';
const GFI_LABEL = process.env.GFI_LABEL?.trim() || 'Good First Issue';
const EXEMPT_PERMISSION_LEVELS = (process.env.INTERMEDIATE_EXEMPT_PERMISSIONS || 'admin,maintain,write,triage')
  .split(',')
  .map((entry) => entry.trim().toLowerCase())
  .filter(Boolean);

function hasLabel(issue, labelName) {
  if (!issue?.labels?.length) {
    return false;
  }

  return issue.labels.some((label) => {
    const name = typeof label === 'string' ? label : label?.name;
    return typeof name === 'string' && name.toLowerCase() === labelName.toLowerCase();
  });
}

async function hasExemptPermission(github, owner, repo, username) {
  if (!EXEMPT_PERMISSION_LEVELS.length) {
    return false;
  }

  try {
    const response = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });

    const permission = response?.data?.permission?.toLowerCase();
    return Boolean(permission) && EXEMPT_PERMISSION_LEVELS.includes(permission);
  } catch (error) {
    if (error?.status === 404) {
      return false;
    }

    const message = error instanceof Error ? error.message : String(error);
    console.log(`Unable to verify ${username}'s repository permissions: ${message}`);
    return false;
  }
}

function buildGfiSearchQuery(owner, repo, username) {
  const sanitizedLabel = JSON.stringify(GFI_LABEL).slice(1, -1);
  return `repo:${owner}/${repo} label:"${sanitizedLabel}" state:closed assignee:${username}`;
}

async function countCompletedGfiIssues(github, owner, repo, username) {
  const query = buildGfiSearchQuery(owner, repo, username);

  try {
    const response = await github.rest.search.issuesAndPullRequests({
      q: query,
      per_page: 1,
    });

    return response?.data?.total_count || 0;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`Unable to verify completed GFIs for ${username}: ${message}`);
    return null;
  }
}

async function hasExistingGuardComment(github, owner, repo, issueNumber, mentee) {
  const comments = await github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: issueNumber,
    per_page: 100,
  });

  return comments.some((comment) => {
    if (!comment?.body?.includes(COMMENT_MARKER)) {
      return false;
    }

    const normalizedBody = comment.body.toLowerCase();
    const normalizedMentee = `@${mentee}`.toLowerCase();

    return normalizedBody.includes(normalizedMentee);
  });
}

function buildRejectionComment({ mentee, completedCount }) {
  const plural = completedCount === 1 ? '' : 's';

  return `${COMMENT_MARKER}
Hi @${mentee}! Thanks for your interest in contributing 💡

This issue is labeled as intermediate, which means it requires a bit more familiarity with the SDK.
Before you can take it on, please complete at least one Good First Issue so we can make sure you have a smooth on-ramp.

You've completed **${completedCount}** Good First Issue${plural} so far.
Once you wrap up your first GFI, feel free to come back and we’ll gladly help you get rolling here!`;
}

module.exports = async ({ github, context }) => {
  try {
    const issue = context.payload.issue;
    const assignee = context.payload.assignee;

    if (!issue?.number || !assignee?.login) {
      return console.log('Missing issue or assignee in payload. Skipping intermediate guard.');
    }

    if (!hasLabel(issue, INTERMEDIATE_LABEL)) {
      return console.log(`Issue #${issue.number} is not labeled '${INTERMEDIATE_LABEL}'. Skipping.`);
    }

    if (assignee.type === 'Bot') {
      return console.log(`Assignee ${assignee.login} is a bot. Skipping.`);
    }

    const { owner, repo } = context.repo;
    const mentee = assignee.login;

    if (await hasExemptPermission(github, owner, repo, mentee)) {
      return console.log(`${mentee} has exempt repository permissions. Skipping guard.`);
    }

    const completedCount = await countCompletedGfiIssues(github, owner, repo, mentee);

    if (completedCount === null) {
      return console.log(`Skipping guard for @${mentee} on issue #${issue.number} due to API error when verifying GFIs.`);
    }

    if (completedCount >= 1) {
      return console.log(`${mentee} has completed ${completedCount} GFI(s). Assignment allowed.`);
    }

    try {
      await github.rest.issues.removeAssignees({
        owner,
        repo,
        issue_number: issue.number,
        assignees: [mentee],
      });
      console.log(`Removed @${mentee} from issue #${issue.number} due to missing GFI completion.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Unable to remove assignee ${mentee} from issue #${issue.number}: ${message}`);
    }

    if (await hasExistingGuardComment(github, owner, repo, issue.number, mentee)) {
      return console.log(`Guard comment already exists on issue #${issue.number}. Skipping duplicate message.`);
    }

    const comment = buildRejectionComment({ mentee, completedCount });

    try {
      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: issue.number,
        body: comment,
      });

      console.log(`Posted guard comment for @${mentee} on issue #${issue.number}.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Unable to post guard comment for @${mentee} on issue #${issue.number}: ${message}`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`❌ Intermediate assignment guard failed: ${message}`);
    throw error;
  }
};
