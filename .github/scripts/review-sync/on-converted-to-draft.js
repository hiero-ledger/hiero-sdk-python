// SPDX-License-Identifier: Apache-2.0
//
// .github/scripts/review-sync/on-converted-to-draft.js
//
// Entry point for the immediate draft-cleanup event job.
//
// Fires on pull_request.converted_to_draft so a PR loses its queue and
// community-review labels right away, instead of waiting for the next
// review-sync cron run (up to 30 minutes later).

const { stripQueueLabels } = require('./helpers/labels');

module.exports = async ({ github, context, core }) => {
  const dryRun = (process.env.DRY_RUN || 'false').toLowerCase() === 'true';
  const { owner, repo } = context.repo;

  if (dryRun) {
    console.log('=== DRY RUN MODE — no labels will be modified ===\n');
  }

  let pr = context.payload.pull_request;
  const prNumber = pr ? pr.number : Number(process.env.PR_NUMBER);

  if (!pr && !prNumber) {
    core.setFailed('No pull_request in payload and no PR_NUMBER provided.');
    return;
  }

  try {
    if (!pr) {
      console.log(`No pull_request in payload. Fetching PR #${prNumber} directly.`);
      const { data } = await github.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber,
      });
      pr = data;
    }

    if (pr.draft !== true) {
      console.log(`PR #${pr.number}: not a draft. Skipping cleanup.`);
      return;
    }

    console.log(`Cleaning draft PR #${pr.number}...`);

    const didClean = await stripQueueLabels(github, owner, repo, pr, dryRun);
    console.log(didClean ? `PR #${pr.number}: cleanup complete.` : `PR #${pr.number}: nothing to clean.`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    core.setFailed(`Failed to clean draft PR #${prNumber}: ${message}`);
  }
};
