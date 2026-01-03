// Script to trigger CodeRabbit plan for intermediate and advanced issues

const marker = '<!-- CodeRabbit Plan Trigger -->';

async function triggerCodeRabbitPlan(github, owner, repo, issue, marker, dryRun) {
  const comment = `${marker} @coderabbitai plan`;

  try {
    if (dryRun === 'true') {
      console.log(`DRY RUN: Would post CodeRabbit plan comment for issue #${issue.number}`);
      console.log(`Comment content: ${comment}`);
      return true;
    }

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issue.number,
      body: comment,
    });
    console.log(`Triggered CodeRabbit plan for issue #${issue.number}`);
    return true;
  } catch (commentErr) {
    console.log(`Failed to trigger CodeRabbit plan for issue #${issue.number}:`, commentErr.message || commentErr);
    return false;
  }
}

module.exports = async ({ github, context }) => {
  try {
    const { owner, repo } = context.repo;
    const { issue, label } = context.payload;
    const dryRun = process.env.DRY_RUN || 'false';

    // Validations
    if (!issue?.number) return console.log('No issue in payload');
    
    // Check if issue has intermediate or advanced label (case-insensitive)
    const hasIntermediateLabel = issue.labels?.some(l => l?.name?.toLowerCase() === 'intermediate');
    const hasAdvancedLabel = issue.labels?.some(l => l?.name?.toLowerCase() === 'advanced');
    
    // Also check if the newly added label is intermediate/advanced
    const isNewLabelIntermediate = label?.name?.toLowerCase() === 'intermediate';
    const isNewLabelAdvanced = label?.name?.toLowerCase() === 'advanced';
    
    if (!hasIntermediateLabel && !hasAdvancedLabel && !isNewLabelIntermediate && !isNewLabelAdvanced) {
      return console.log('Issue does not have intermediate or advanced label');
    }

    // Check for existing CodeRabbit plan comment
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner, repo, issue_number: issue.number, per_page: 100
    });
    
    if (comments.some(c => c.body?.includes('@coderabbitai plan'))) {
      return console.log(`CodeRabbit plan already triggered for #${issue.number}`);
    }

    // Post CodeRabbit plan trigger
    await triggerCodeRabbitPlan(github, owner, repo, issue, marker, dryRun);

    console.log('=== Summary ===');
    console.log(`Repository: ${owner}/${repo}`);
    console.log(`Issue Number: ${issue.number}`);
    console.log(`Issue Title: ${issue.title || '(no title)'}`);
    console.log(`Labels: ${issue.labels?.map(l => l.name).join(', ') || 'none'}`);
    console.log(`Dry Run: ${dryRun}`);
  } catch (err) {
    console.log('❌ Error:', err.message);
  }
};
