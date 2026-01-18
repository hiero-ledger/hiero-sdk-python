// Script to trigger CodeRabbit plan for intermediate and advanced issues

const CODERABBIT_MARKER = '<!-- CodeRabbit Plan Trigger -->';

async function triggerCodeRabbitPlan(github, owner, repo, issue, marker = CODERABBIT_MARKER, isDryRun = false) {
  const comment = `${marker} @coderabbitai plan`;

  if (isDryRun) {
    console.log(`[DRY RUN] Would trigger CodeRabbit plan for issue #${issue.number}`);
    return true;
  }

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issue.number,
      body: comment,
    });
    console.log(`Triggered CodeRabbit plan for issue #${issue.number}`);
    return true;
  } catch (commentErr) {
    console.log('Failed to trigger CodeRabbit plan:', {
      message: commentErr?.message,
      status: commentErr?.status,
      owner,
      repo,
      issueNumber: issue?.number,
    });
    return false;
  }
}

function hasBeginnerOrHigherLabel(issue, label) {
  // Check if issue has beginner, intermediate or advanced label (case-insensitive)
  const allowed = ['beginner', 'intermediate', 'advanced'];

  const hasAllowedLabel = issue.labels?.some(l => allowed.includes(l?.name?.toLowerCase()));

  // Also check if newly added label is beginner/intermediate/advanced
  const isNewLabelAllowed = allowed.includes(label?.name?.toLowerCase());

  return hasAllowedLabel || isNewLabelAllowed;
}

async function hasExistingCodeRabbitPlan(github, owner, repo, issueNumber) {
  // Check for existing CodeRabbit plan comment (limited to first 500 comments)
  // Uses marker-based detection to avoid false positives from quoted text
  try {
    const comments = [];
    const iterator = github.paginate.iterator(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issueNumber,
      per_page: 100,
    });

    let count = 0;
    for await (const { data: page } of iterator) {
      comments.push(...page);
      count += page.length;
      if (count >= 500) break; // Hard upper bound to prevent unbounded pagination
    }

    // Check for marker-based comment OR @coderabbitai plan text
    return comments.some(c =>
      typeof c?.body === 'string' &&
      (c.body.includes(CODERABBIT_MARKER) || c.body.includes('@coderabbitai plan'))
    );
  } catch (error) {
    console.log('Failed to check existing CodeRabbit plan comments:', {
      message: error?.message,
      status: error?.status,
      owner,
      repo,
      issueNumber,
    });
    // Return false to allow plan trigger attempt (fail-open for better UX)
    return false;
  }
}

function logSummary(owner, repo, issue) {
  console.log('=== Summary ===');
  console.log(`Repository: ${owner}/${repo}`);
  console.log(`Issue Number: ${issue.number}`);
  console.log(`Issue Title: ${issue.title || '(no title)'}`);
  console.log(`Labels: ${issue.labels?.map(l => l.name).join(', ') || 'none'}`);
}

// Main workflow handler (default export for workflow usage)
async function main({ github, context }) {
  try {
    const { owner, repo } = context.repo;
    const { issue, label } = context.payload;

    // Validations
    if (!issue?.number) return console.log('No issue in payload');

    if (!hasBeginnerOrHigherLabel(issue, label)) {
      return console.log('Issue does not have beginner/intermediate/advanced label');
    }

    if (await hasExistingCodeRabbitPlan(github, owner, repo, issue.number)) {
      return console.log(`CodeRabbit plan already triggered for #${issue.number}`);
    }

    // Check for dry run (default to true if not specified, for safety)
    const isDryRun = (process.env.DRY_RUN || 'true').toLowerCase() === 'true';

    // Post CodeRabbit plan trigger
    await triggerCodeRabbitPlan(github, owner, repo, issue, CODERABBIT_MARKER, isDryRun);

    logSummary(owner, repo, issue);
  } catch (err) {
    console.log('❌ Error:', {
      message: err?.message,
      status: err?.status,
      owner: context?.repo?.owner,
      repo: context?.repo?.repo,
      issueNumber: context?.payload?.issue?.number,
    });
  }
}

// Default export for workflow usage: await script({ github, context })
module.exports = main;

// Named exports for reuse by other scripts (e.g., GFI assignment bot)
module.exports.triggerCodeRabbitPlan = triggerCodeRabbitPlan;
module.exports.hasExistingCodeRabbitPlan = hasExistingCodeRabbitPlan;
module.exports.CODERABBIT_MARKER = CODERABBIT_MARKER;
