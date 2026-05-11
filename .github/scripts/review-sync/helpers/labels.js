// SPDX-License-Identifier: Apache-2.0
//
// helpers/labels.js
//
// Label creation, determination, and synchronization.
//
// Key design decisions:
//   - ensureLabel() silently handles 422 (race condition / concurrent run)
//   - determineLabel() uses a 4-stage pipeline gated by maintainer approval
//   - syncLabel() adds the correct label FIRST, then removes stale ones
//     (crash-safe: PR never has zero queue labels)

const { QUEUE_LABELS, ALL_QUEUE_LABEL_NAMES, COMMUNITY_REVIEW } = require('./constants');
const { countApprovals } = require('./permissions');

/**
 * Ensure a single label exists in the repo.
 * Silently handles 422 (label already exists).
 *
 * Note: checks existence only. If a label already exists with the wrong
 * colour or description, it will not be corrected in Phase 1.
 */
async function ensureLabel(github, owner, repo, label, dryRun) {
  try {
    await github.rest.issues.getLabel({ owner, repo, name: label.name });
    console.log(`  Label "${label.name}" already exists. Skipping creation.`);
  } catch (error) {
    if (error.status === 404) {
      if (dryRun) {
        console.log(`  [DRY RUN] Would create label "${label.name}" (${label.color}).`);
        return;
      }
      try {
        await github.rest.issues.createLabel({
          owner,
          repo,
          name: label.name,
          color: label.color,
          description: label.description,
        });
        console.log(`  Created label "${label.name}" (#${label.color}).`);
      } catch (createError) {
        // 422 = label already exists (race condition or concurrent run)
        if (createError.status === 422) {
          console.log(`  Label "${label.name}" already exists (422). Skipping.`);
        } else {
          throw createError;
        }
      }
    } else {
      throw error;
    }
  }
}

/**
 * Check if the latest CI runs for a given commit have any failures.
 *
 * We intentionally treat the following as failures:
 * - 'failure', 'timed_out' (explicit test failures)
 * - 'startup_failure' (e.g., invalid workflow YAML)
 * - 'action_required' (e.g., waiting for maintainer approval for first-time contributors)
 *
 * We intentionally EXCLUDE 'cancelled':
 * When a developer pushes a new commit, GitHub automatically cancels the currently
 * running workflows. If we treated 'cancelled' as a failure, every re-push would
 * instantly demote the PR to queue:junior-committer, frustrating contributors.
 *
 * @returns {boolean} true if any check run conclusion is a blocking failure.
 */
async function hasCIFailures(github, owner, repo, sha) {
  try {
    // We MUST use paginate, otherwise it silently truncates at 30 runs.
    // Matrix builds often exceed 30 checks.
    const checkRuns = await github.paginate(github.rest.checks.listForRef, {
      owner,
      repo,
      ref: sha,
      filter: 'latest'
    });

    return checkRuns.some(
      run =>
        run.conclusion === 'failure' ||
        run.conclusion === 'timed_out' ||
        run.conclusion === 'startup_failure' ||
        run.conclusion === 'action_required'
    );
  } catch (error) {
    // Fail securely: do not assume CI is passing if we cannot verify it.
    // Throwing ensures this PR skips sync and the workflow registers an error.
    const message = error instanceof Error ? error.message : String(error);
    console.error(`    ✗ Failed to fetch CI checks for ${sha}: ${message}`);
    throw error;
  }
}

/**
 * Determine the correct queue label for a PR based on approval counts.
 *
 * Phase 1 logic (5-stage pipeline):
 *   ciFailing                                        → queue:junior-committer (CI broken, block promotion)
 *   maintainerApprovals >= 1 AND coreApprovals >= 2  → status: ready-to-merge (CODEOWNERS + min core reviews)
 *   maintainerApprovals >= 1 (but coreApprovals < 2) → queue:committers      (maintainer already in, need committer next)
 *   coreApprovals >= 1 (no maintainer yet)            → queue:maintainers     (committer reviewed, needs maintainer)
 *   anyApproval >= 1                                 → queue:committers      (has soft approval, needs committer)
 *   else                                             → queue:junior-committer (no approvals yet)
 *
 * Note: When a maintainer "jumps in early" before triage/committers, the PR should
 * route to queue:committers (not queue:maintainers) to attract a committer review
 * rather than a second maintainer. This prevents wasting maintainer bandwidth.
 *
 * status: ready-to-merge requires BOTH a maintainer approval AND at least 2
 * total core reviews (maintainer or committer). This prevents a single maintainer approval
 * + a soft approval from marking a PR as ready when branch protection requires 2+ core reviews.
 *
 * @param {{ maintainerApprovals: number, coreApprovals: number, softApprovals: number, anyApproval: number }} approvals
 * @param {boolean} ciFailing - If true, automatically demotes PR to queue:junior-committer
 * @returns {object} The correct QUEUE_LABELS entry
 */
function determineLabel(approvals, ciFailing = false) {
  if (ciFailing) {
    return QUEUE_LABELS.JUNIOR;
  }
  if (approvals.maintainerApprovals >= 1 && approvals.coreApprovals >= 2) {
    return QUEUE_LABELS.MERGE;
  }
  if (approvals.maintainerApprovals >= 1) {
    return QUEUE_LABELS.COMMITTERS;
  }
  if (approvals.coreApprovals >= 1) {
    return QUEUE_LABELS.MAINTAINERS;
  }
  if (approvals.anyApproval >= 1) {
    return QUEUE_LABELS.COMMITTERS;
  }
  return QUEUE_LABELS.JUNIOR;
}

/**
 * Sync the queue label on a single PR.
 *
 * Order of operations (non-negotiable):
 *   1. Compute stale queue labels on the PR
 *   2. Skip only if correct label is already present AND no stale labels exist
 *   3. ADD the correct label first
 *   4. THEN remove any stale queue labels
 *
 * This ensures a PR never has zero queue labels, even if the process
 * crashes mid-run. Stale labels are always cleaned up, even when the
 * correct label was already present.
 *
 * @param {object}  github - Octokit instance
 * @param {string}  owner  - Repository owner
 * @param {string}  repo   - Repository name
 * @param {object}  pr     - Pull request object from the list API
 * @param {boolean} dryRun - If true, log without making changes
 * @returns {boolean} true if the label was changed, false if already correct
 */
async function syncLabel(github, owner, repo, pr, dryRun) {
  const prNumber = pr.number;
  const currentLabels = (pr.labels || []).map((l) => l.name);

  // Count approvals and check CI status
  const approvals = await countApprovals(github, owner, repo, prNumber);
  const ciFailing = await hasCIFailures(github, owner, repo, pr.head.sha);
  const correctLabel = determineLabel(approvals, ciFailing);

  console.log(
    `  PR #${prNumber}: maintainerApprovals=${approvals.maintainerApprovals}, ` +
    `coreApprovals=${approvals.coreApprovals}, ` +
    `softApprovals=${approvals.softApprovals}, anyApproval=${approvals.anyApproval}, ` +
    `ciFailing=${ciFailing} → ${correctLabel.name}`
  );

  // Determine which stale queue labels to remove
  const staleLabels = currentLabels.filter(
    (name) => ALL_QUEUE_LABEL_NAMES.includes(name) && name !== correctLabel.name
  );

  const isHuman = pr.user && pr.user.type !== 'Bot';
  const needsCommunityReview = isHuman && !currentLabels.includes(COMMUNITY_REVIEW.name);

  // Check if the correct labels are already present AND there are no stale labels to remove
  if (currentLabels.includes(correctLabel.name) && staleLabels.length === 0 && !needsCommunityReview) {
    console.log(`    ✓ Already has "${correctLabel.name}"${isHuman ? ` and "${COMMUNITY_REVIEW.name}"` : ''}. No change needed.`);
    return false;
  }

  const labelsToAdd = [];
  if (!currentLabels.includes(correctLabel.name)) {
    labelsToAdd.push(correctLabel.name);
  }
  if (needsCommunityReview) {
    labelsToAdd.push(COMMUNITY_REVIEW.name);
  }

  if (dryRun) {
    if (labelsToAdd.length > 0) {
      console.log(`    [DRY RUN] Would add: ${labelsToAdd.join(', ')}.`);
    }
    if (staleLabels.length > 0) {
      console.log(`    [DRY RUN] Would remove: ${staleLabels.join(', ')}.`);
    }
    return true;
  }

  // Step 1: ADD the correct labels FIRST (crash-safe: PR always has at least one label)
  if (labelsToAdd.length > 0) {
    await github.rest.issues.addLabels({
      owner,
      repo,
      issue_number: prNumber,
      labels: labelsToAdd,
    });
    console.log(`    + Added: ${labelsToAdd.join(', ')}.`);
  }

  // Step 2: THEN remove stale queue labels one by one
  for (const stale of staleLabels) {
    try {
      await github.rest.issues.removeLabel({
        owner,
        repo,
        issue_number: prNumber,
        name: stale,
      });
      console.log(`    - Removed "${stale}".`);
    } catch (error) {
      // 404 = label was already removed (race condition or manual action)
      if (error.status === 404) {
        console.log(`    - Label "${stale}" already gone (404). Skipping.`);
      } else {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`    ✗ Failed to remove "${stale}": ${message}`);
        throw error; // Re-throw to prevent silently leaving PR in a broken multi-label state
      }
    }
  }

  return true;
}

module.exports = { ensureLabel, determineLabel, syncLabel, hasCIFailures };
