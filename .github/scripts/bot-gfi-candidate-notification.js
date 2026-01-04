// Script to notify the team when a Good First Issue Candidate is created.

const marker = '<!-- GFI Candidate Notification -->';
const TEAM_ALIAS = '@hiero-ledger/hiero-sdk-good-first-issue-support';

async function notifyTeam(github, owner, repo, issue, message) {
   if (dryRun) {
    console.log('Notified team about GFI candidate');
    console.log(`Repo: ${owner}/${repo}`);
    console.log(`Issue: #${issue.number} - ${issue.title}`);
    console.log(`Message:\n${message}`);
    return true;
  }
  const comment = `${marker} :wave: Hello Team :wave:
${TEAM_ALIAS}

${message}

Repository: ${owner}/${repo}
Issue: #${issue.number} - ${issue.title || '(no title)'}

Best Regards,
Hiero Python SDK team`;

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issue.number,
      body: comment,
    });
    console.log(`Notified team about #${issue.number}`);
    return true;
  } catch (err) {
    console.log(
      `Failed to notify team about GFI candidate #${issue.number}:`,
      err.message || err
    );
    return false;
  }
}

module.exports = async ({ github, context }) => {
  try {
    const { owner, repo } = context.repo;
    const { issue, label } = context.payload;

    if (!issue?.number || !label?.name) {
      return console.log('Missing issue or label in payload');
    }

    //  Only handle Good First Issue Candidate
    if (label.name !== 'good first issue candidate') {
      return;
    }

    //
    dryRun && console.log('DRY-RUN active');


    // Prevent duplicate notifications
    const comments = await github.paginate(
      github.rest.issues.listComments,
      { owner, repo, issue_number: issue.number, per_page: 100 }
    );

    if (comments.some(c => c.body?.includes(marker))) {
      return console.log(`Notification already exists for #${issue.number}`);
    }

    const message =
      'A new Good First Issue Candidate has been created. Please review it and confirm whether it should be labeled as a Good First Issue.';

    const success = await notifyTeam(github, owner, repo, issue, message);

    if (success) {
      console.log('=== Summary ===');
      console.log(`Repository: ${owner}/${repo}`);
      console.log(`Issue Number: ${issue.number}`);
      console.log(`Label: ${label.name}`);
    }
  } catch (err) {
    console.log('❌ Error:', err.message);
  }
};
