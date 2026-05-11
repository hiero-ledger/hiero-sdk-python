// SPDX-License-Identifier: Apache-2.0
//
// .github/scripts/review-sync/index.js
//
// Entry point for the Review Queue Label Sync cron job.
//
// Responsibilities:
//   1. Rate-limit guard — abort if remaining calls < 200
//   2. Fetch all open non-draft PRs (paginated)
//   3. Ensure the four queue labels exist in the repo
//   4. Sync the correct label on every PR via helpers
//   5. Print a summary of what changed
//
// Phase 1 of 4 — label sync only.

const helpers = require('./helpers');
const { QUEUE_LABELS, RATE_LIMIT_FLOOR, COMMUNITY_REVIEW } = helpers.constants;
const { ensureLabel, syncLabel } = helpers.labels;

module.exports = async ({ github, context, core }) => {
  const dryRun = (process.env.DRY_RUN || 'false').toLowerCase() === 'true';
  const { owner, repo } = context.repo;

  if (dryRun) {
    console.log('=== DRY RUN MODE — no labels will be created or modified ===\n');
  }

  // ── 1. Rate-limit guard ──────────────────────────────────────────────────
  console.log('--- Rate Limit Check ---');
  const { data: rateLimit } = await github.rest.rateLimit.get();
  const remaining = rateLimit.resources.core.remaining;
  console.log(`  Core API remaining: ${remaining}`);

  if (remaining < RATE_LIMIT_FLOOR) {
    console.log(`  ⚠ Skipping run: rate limit too low (${remaining} < ${RATE_LIMIT_FLOOR}).`);
    return;
  }

  // ── 2. Fetch all open non-draft PRs (paginated) ──────────────────────────
  console.log('\n--- Fetching Open PRs ---');
  const allPRs = await github.paginate(github.rest.pulls.list, {
    owner,
    repo,
    state: 'open',
    per_page: 100,
  });

  const prs = allPRs.filter((pr) => !pr.draft);
  console.log(`  Total open PRs: ${allPRs.length}`);
  console.log(`  Non-draft PRs to process: ${prs.length}`);
  console.log(`  Draft PRs skipped: ${allPRs.length - prs.length}`);

  if (prs.length === 0) {
    console.log('  No non-draft PRs found. Exiting.');
    return;
  }

  // ── 3. Ensure labels exist ───────────────────────────────────────────────
  console.log('\n--- Ensuring Labels Exist ---');
  for (const label of Object.values(QUEUE_LABELS)) {
    await ensureLabel(github, owner, repo, label, dryRun);
  }
  await ensureLabel(github, owner, repo, COMMUNITY_REVIEW, dryRun);

  // ── 4. Sync label on each PR ─────────────────────────────────────────────
  console.log('\n--- Syncing Labels ---');
  let changed = 0;
  let skipped = 0;
  let errors = 0;

  for (const pr of prs) {
    try {
      const didChange = await syncLabel(github, owner, repo, pr, dryRun);
      if (didChange) {
        changed++;
      } else {
        skipped++;
      }
    } catch (error) {
      errors++;
      const message = error instanceof Error ? error.message : String(error);
      console.error(`  ✗ Error on PR #${pr.number}: ${message}`);
    }
  }

  // ── 5. Summary ───────────────────────────────────────────────────────────
  console.log('\n=== Summary ===');
  console.log(`  PRs processed: ${prs.length}`);
  console.log(`  Labels changed: ${changed}`);
  console.log(`  Labels already correct: ${skipped}`);
  console.log(`  Errors: ${errors}`);

  if (errors > 0) {
    core.setFailed(`Review sync completed with ${errors} error(s). Check logs above.`);
  }
};
