// SPDX-License-Identifier: Apache-2.0
//
// .github/scripts/review-sync/report.js
//
// Read-only PR review status reporter.
//
// This script intentionally does not create labels, add comments, assign
// reviewers, or block merges. It only reads PR labels/reviews and publishes the
// computed status to workflow logs and the GitHub Actions job summary.

const helpers = require('./helpers');
const { countApprovals } = helpers.permissions;
const { getLatestReviewStates } = helpers.reviews;
const { buildReviewStatus, formatStatusForLog } = helpers.status;

function getPullRequestNumber(context) {
  return context.payload?.pull_request?.number || Number(process.env.PR_NUMBER);
}

async function writeJobSummary(core, status, logMessage) {
  if (!core?.summary) return;

  await core.summary
    .addHeading(`Review status for PR #${status.prNumber}`, 2)
    .addCodeBlock(logMessage, 'text')
    .write();
}

module.exports = async ({ github, context, core }) => {
  const prNumber = getPullRequestNumber(context);

  if (!prNumber) {
    console.log('No pull request number found. Exiting.');
    return;
  }

  const { owner, repo } = context.repo;
  console.log(`Evaluating review status for PR #${prNumber} in ${owner}/${repo}.`);

  try {
    const { data: pr } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });

    const latestReviewStates = await getLatestReviewStates(github, owner, repo, prNumber);
    const approvals = await countApprovals(github, owner, repo, prNumber);
    const status = buildReviewStatus({
      prNumber,
      labels: pr.labels || [],
      approvals,
      latestReviewStates,
    });

    const logMessage = formatStatusForLog(status);

    console.log('\n--- Review Status Report ---');
    console.log(logMessage);
    console.log('--- End Review Status Report ---\n');

    core?.setOutput?.('current_state', status.currentState);
    core?.setOutput?.('waiting_on', status.waitingOn);
    core?.setOutput?.('expected_queue_label', status.expectedQueueLabel);
    core?.setOutput?.('summary', status.summary);

    await writeJobSummary(core, status, logMessage);
  } catch (error) {
    const hint = error?.status === 403
      ? ' Check workflow permissions include pull-requests: read.'
      : '';
    console.error(`Failed to evaluate review status for PR #${prNumber}: ${error.message}.${hint}`);
    throw error;
  }
};
