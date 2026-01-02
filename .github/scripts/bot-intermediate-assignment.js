const COMMENT_MARKER = process.env.INTERMEDIATE_COMMENT_MARKER || '<!-- Intermediate Issue Guard -->';
const INTERMEDIATE_LABEL = process.env.INTERMEDIATE_LABEL?.trim() || 'intermediate';
const GFI_LABEL = process.env.GFI_LABEL?.trim() || 'Good First Issue';
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

async function countCompletedGfiIssues(github, owner, repo, username) {
  try {
    console.log(`Checking closed '${GFI_LABEL}' issues in ${owner}/${repo} for ${username}.`);
    const iterator = github.paginate.iterator(github.rest.issues.listForRepo, {
      owner,
      repo,
      state: 'closed',
      labels: GFI_LABEL,
      assignee: username,
      sort: 'updated',
      direction: 'desc',
      per_page: 100,
    });

    const normalizedAssignee = username.toLowerCase();
    let pageCount = 0;
    const MAX_PAGES = 8;

    for await (const { data: issues } of iterator) {
      pageCount += 1;
      if (pageCount > MAX_PAGES) {
        console.log(`Reached pagination safety cap (${MAX_PAGES}) while checking GFIs for ${username}.`);
        break;
      }

      console.log(`Scanning page ${pageCount} of closed '${GFI_LABEL}' issues for ${username} (items: ${issues.length}).`);
      const match = issues.find((issue) => {
        if (issue.pull_request) {
          return false;
        }

        const assignees = Array.isArray(issue.assignees) ? issue.assignees : [];
        return assignees.some((assignee) => assignee?.login?.toLowerCase() === normalizedAssignee);
      });

      if (match) {
        console.log(`Found matching GFI issue #${match.number} (${match.html_url || 'no url'}) for ${username}.`);
        return 1;
      }
    }

    return 0;
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

    const completedCount = await countCompletedGfiIssues(github, owner, repo, mentee);

    if (completedCount === null) {
      return console.log(`Skipping guard for @${mentee} on issue #${issue.number} due to API error when verifying GFIs.`);
    }

    if (completedCount >= 1) {
      console.log(`✅ ${mentee} has completed ${completedCount} GFI(s). Assignment allowed.`);
      return;
    }

    console.log(`❌ ${mentee} has completed ${completedCount} GFI(s). Assignment not allowed; proceeding with removal and comment.`);

    try {
      if (DRY_RUN) {
        console.log(`[dry-run] Would remove @${mentee} from issue #${issue.number} due to missing GFI completion.`);
      } else {
        await github.rest.issues.removeAssignees({
          owner,
          repo,
          issue_number: issue.number,
          assignees: [mentee],
        });
        console.log(`Removed @${mentee} from issue #${issue.number} due to missing GFI completion.`);
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
