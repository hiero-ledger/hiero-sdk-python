// Script to notify the team when a GFI issue receives its first human comment.

const marker = '<!-- GFI Issue Notification -->';
const TEAM_ALIAS = '@hiero-ledger/hiero-sdk-good-first-issue-support';

async function notifyTeam(github, owner, repo, issue, message) {
  const commentBody = `${marker} :wave: Hello Team :wave:
${TEAM_ALIAS}

${message}

Repository: ${owner}/${repo}  
Issue: #${issue.number} - ${issue.title || '(no title)'}

Best Regards,  
Python SDK team`;

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issue.number,
      body: commentBody,
    });
    console.log(`✅ Notified team about GFI issue #${issue.number}`);
    return true;
  } catch (err) {
    console.log(`❌ Failed to notify team for #${issue.number}:`, err.message);
    return false;
  }
}

function isValidHumanComment(comment) {
  return comment?.user?.type !== 'Bot';
}

function isGoodFirstIssue(issue) {
  const labels = issue.labels?.map(l => l.name) || [];
  return labels.includes('Good First Issue');
}

function isFirstNonBotComment(comments, currentComment) {
  return !comments.some(
    c =>
      c.id !== currentComment.id &&
      c.user?.type !== 'Bot'
  );
}


module.exports = async ({ github, context }) => {
  console.log('Context debug:', {
    actor: context.actor,
    eventName: context.eventName,
    repo: context.repo,
  });

  try {
    const { owner, repo } = context.repo;
    const { issue, comment } = context.payload;

    if (!issue?.number || !comment) {
      return console.log('No issue or comment found in payload');
    }

    if (!isValidHumanComment(comment)) {
      return console.log('Ignoring bot comment');
    }

    if (!isGoodFirstIssue(issue)) {
      return console.log('Issue is not a GFI');
    }

    if (issue.assignees?.length > 0) {
      return console.log('Issue already assigned');
    }

    // Fetch all issue comments
    const comments = await github.paginate(
      github.rest.issues.listComments,
      {
        owner,
        repo,
        issue_number: issue.number,
        per_page: 100,
      }
    );

    // Skip if notification already exists
    if (comments.some(c => c.body?.includes(marker))) {
      return console.log(`Notification already exists for #${issue.number}`);
    }

    if (!isFirstNonBotComment(comments, comment)) {
      return console.log('Not the first non-bot comment, skipping');
    }

    const message = `@${comment.user.login} commented on this **Good First Issue** and may be ready to be assigned. Please review and assign if appropriate.`;


    await notifyTeam(github, owner, repo, issue, message);

    console.log('=== Summary ===');
    console.log(`Repository: ${owner}/${repo}`);
    console.log(`Issue Number: ${issue.number}`);
    console.log(`Triggered by: @${comment.user.login}`);
    console.log(`Message: ${message}`);
  } catch (err) {
     console.log('❌ Error:', err.message);
  }
};

