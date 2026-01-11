const COMMENT_MARKER = process.env.INTERMEDIATE_COMMENT_MARKER || '<!-- Intermediate Issue Guard -->';
const INTERMEDIATE_LABEL = process.env.INTERMEDIATE_LABEL?.trim() || 'intermediate';
const BEGINNER_LABEL = process.env.BEGINNER_LABEL?.trim() || 'beginner';
const EXEMPT_PERMISSION_LEVELS = (process.env.INTERMEDIATE_EXEMPT_PERMISSIONS || 'admin,maintain,write,triage')
  .split(',')
  .map((entry) => entry.trim().toLowerCase())
  .filter(Boolean);
const DRY_RUN = /^true$/i.test(process.env.DRY_RUN || '');

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
    console.log(`No exempt permission levels configured. Skipping permission check for ${username} in ${owner}/${repo}.`);
    return false;
  }

  console.log(`Checking repository permissions for ${username} in ${owner}/${repo} against exempt levels: [${EXEMPT_PERMISSION_LEVELS.join(', ')}]`);

  try {
    const response = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });

    const permission = response?.data?.permission?.toLowerCase();
    const isExempt = Boolean(permission) && EXEMPT_PERMISSION_LEVELS.includes(permission);

    console.log(`Permission check for ${username} in ${owner}/${repo}: permission='${permission}', exempt=${isExempt}`);

    return isExempt;
  } catch (error) {
    if (error?.status === 404) {
      console.log(`User ${username} not found as collaborator in ${owner}/${repo} (404). Treating as non-exempt.`);
      return false;
    }

    const message = error instanceof Error ? error.message : String(error);
    console.log(`Unable to verify ${username}'s repository permissions in ${owner}/${repo}: ${message}`);
    return false;
  }
}

async function countCompletedBeginnerIssues(github, owner, repo, username) {
  try {
    console.log(`Checking closed '${BEGINNER_LABEL}' issues in ${owner}/${repo} for ${username}`);

    const query = `
      query ($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
          issues(
            first: 10
            states: CLOSED
            labels: ["beginner"]
            orderBy: { field: UPDATED_AT, direction: DESC }
          ) {
            nodes {
              number
              assignees(first: 10) {
                nodes {
                  login
                }
              }
            }
          }
        }
      }
    `;

    const data = await github.graphql(query, { owner, repo });
    const normalizedUsername = username.toLowerCase();
    const issues = data?.repository?.issues?.nodes ?? [];
    console.log(
      `Retrieved ${issues.length} closed Beginner issue(s) for evaluation`);

    for (const issue of issues) {
      const assignees = issue.assignees?.nodes ?? [];
      
      const wasAssigned = assignees.some(
        (assignee) =>
          assignee?.login?.toLowerCase() === normalizedUsername
      );

      console.log(
        `Issue #${issue.number}: assignees=[${assignees
          .map(a => a.login)
          .join(', ')}], matched=${wasAssigned}`
      );

      if (wasAssigned) {
        console.log(`Found completed Beginner issue #${issue.number} for ${username}`);
        return 1;
      }
    }

    console.log(`No completed Beginner issues found for ${username}`);
    return 0;

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`Unable to verify completed Beginner issues for ${username}: ${message}`);
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
Before you can take it on, please complete at least one Beginner Issue so we can make sure you have a smooth on-ramp.

You've completed **${completedCount}** Beginner Issue${plural} so far.
Once you wrap up your first Beginner issue, feel free to come back and we’ll gladly help you get rolling here!`;
}

module.exports = async ({ github, context }) => {
  try {
    if (DRY_RUN) {
      console.log('Running intermediate guard in dry-run mode: no assignee removals or comments will be posted.');
    }

    const issue = context.payload.issue;
    const assignee = context.payload.assignee;

    if (!issue?.number || !assignee?.login) {
      return console.log('Missing issue or assignee in payload. Skipping intermediate guard.');
    }

    const { owner, repo } = context.repo;
    const mentee = assignee.login;

    console.log(`Processing intermediate guard for issue #${issue.number} in ${owner}/${repo}: assignee=${mentee}, dry_run=${DRY_RUN}`);

    if (!hasLabel(issue, INTERMEDIATE_LABEL)) {
      return console.log(`Issue #${issue.number} is not labeled '${INTERMEDIATE_LABEL}'. Skipping.`);
    }

    if (assignee.type === 'Bot') {
      return console.log(`Assignee ${mentee} is a bot. Skipping.`);
    }

    if (await hasExemptPermission(github, owner, repo, mentee)) {
      console.log(`✅ ${mentee} has exempt repository permissions in ${owner}/${repo}. Skipping guard.`);
      return;
    }

    const completedCount = await countCompletedBeginnerIssues(github, owner, repo, mentee);

    if (completedCount === null) {
      return console.log(`Skipping guard for @${mentee} on issue #${issue.number} due to API error when verifying Beginner issues.`);
    }

    if (completedCount >= 1) {
      console.log(`✅ ${mentee} has completed ${completedCount} Beginner issues. Assignment allowed.`);
      return;
    }

    console.log(`❌ ${mentee} has completed ${completedCount} Beginner issues. Assignment not allowed; proceeding with removal and comment.`);

    try {
      if (DRY_RUN) {
        console.log(`[dry-run] Would remove @${mentee} from issue #${issue.number} due to missing Beginner issue completion.`);
      } else {
        await github.rest.issues.removeAssignees({
          owner,
          repo,
          issue_number: issue.number,
          assignees: [mentee],
        });
        console.log(`Removed @${mentee} from issue #${issue.number} due to missing Beginner issue completion.`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Unable to remove assignee ${mentee} from issue #${issue.number}: ${message}`);
    }

    try {
      if (await hasExistingGuardComment(github, owner, repo, issue.number, mentee)) {
        return console.log(`Guard comment already exists on issue #${issue.number}. Skipping duplicate message.`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Unable to check for existing guard comment: ${message}. Proceeding to post comment anyway (accepting small risk of duplicate).`);
    }

    const comment = buildRejectionComment({ mentee, completedCount });

    try {
      if (DRY_RUN) {
        console.log('[dry-run] Would post guard comment with body:\n', comment);
      } else {
        await github.rest.issues.createComment({
          owner,
          repo,
          issue_number: issue.number,
          body: comment,
        });

        console.log(`Posted guard comment for @${mentee} on issue #${issue.number}.`);
      }
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
