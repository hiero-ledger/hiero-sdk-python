// Script to notify the team when a P0 issue is created. 

const marker = '<!-- P0 Issue Notification -->';

  async function notifyTeam(github, owner, repo, issue, marker) {
    const comment = `${marker} :rotating_light: Attention Team :rotating_light: 
@hiero-ledger/hiero-sdk-python-maintainers @hiero-ledger/hiero-sdk-python-committers @hiero-ledger/hiero-sdk-python-triage

A new P0 issue has been created: #${issue.number} - ${issue.title || '(no title)'}
Please prioritize this issue accordingly.

Best Regards,
Automated Notification System`;

    try {
      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: issue.number,
        body: comment,
      });
      console.log(`Notified team about P0 issue #${issue.number}`);
      return true;
    } catch (commentErr) {
      console.log(`Failed to notify team about P0 issue #${issue.number}:`, commentErr.message || commentErr);
      return false;
    }
  }

module.exports = async ({ github, context }) => {
  try {
    const { owner, repo } = context.repo;
    const { issue, label } = context.payload;

    // Validations
    if (!issue?.number) return console.log('No issue in payload');
    if (label?.name?.toLowerCase() !== 'p0') return;
    if (!issue.labels?.some(l => l?.name?.toLowerCase() === 'p0')) return;

    // Check for existing comment
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner, repo, issue_number: issue.number, per_page: 100
    });
    if (comments.some(c => c.body?.includes(marker))) {
      return console.log(`Notification already exists for #${issue.number}`);
    }
  // Post notification
    await notifyTeam(github, owner, repo, issue, marker);

    console.log('=== Summary ===');
    console.log(`Repository: ${owner}/${repo}`);
    console.log(`Issue Number: ${issue.number}`);
    console.log(`Issue Title: ${issue.title || '(no title)'}`);
  } catch (err) {
    console.log('❌ Error:', err.message);
  }
};