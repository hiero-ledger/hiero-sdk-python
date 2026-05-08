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

const { QUEUE_LABELS, ALL_QUEUE_LABEL_NAMES } = require('./constants');
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
 * Determine the correct queue label for a PR based on approval counts.
 *
 * Phase 1 logic (4-stage pipeline):
 *   maintainerApproval >= 1 AND (maintainerApproval + writeApproval) >= 2  → status: ready-to-merge      (CODEOWNERS + min core reviews)
 *   writeApproval >= 1 OR maintainerApproval >= 1 → queue:maintainers   (senior review present, needs more)
 *   anyApproval >= 1                               → queue:committers    (has any approval, needs committer)
 *   else                                           → queue:junior-committer (no approvals yet)
 *
 * Note: status: ready-to-merge requires BOTH a maintainer approval AND at least 2
 * total core reviews (maintainer or write). This prevents a single maintainer approval
 * + a soft approval from marking a PR as ready when branch protection requires 2+ core reviews.
 *
 * @param {{ maintainerApproval: number, writeApproval: number, softApproval: number, anyApproval: number }} approvals
 * @returns {object} The correct QUEUE_LABELS entry
 */
function determineLabel(approvals) {
  if (approvals.maintainerApproval >= 1 && (approvals.maintainerApproval + approvals.writeApproval) >= 2) {
    return QUEUE_LABELS.MERGE;
  }
  if (approvals.writeApproval >= 1 || approvals.maintainerApproval >= 1) {
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

  // Count approvals and determine the correct label
  const approvals = await countApprovals(github, owner, repo, prNumber);
  const correctLabel = determineLabel(approvals);

  console.log(
    `  PR #${prNumber}: maintainerApproval=${approvals.maintainerApproval}, ` +
    `writeApproval=${approvals.writeApproval}, ` +
    `softApproval=${approvals.softApproval}, anyApproval=${approvals.anyApproval} ` +
    `→ ${correctLabel.name}`
  );

  // Determine which stale queue labels to remove
  const staleLabels = currentLabels.filter(
    (name) => ALL_QUEUE_LABEL_NAMES.includes(name) && name !== correctLabel.name
  );

  // Check if the correct label is already present AND there are no stale labels to remove
  if (currentLabels.includes(correctLabel.name) && staleLabels.length === 0) {
    console.log(`    ✓ Already has "${correctLabel.name}". No change needed.`);
    return false;
  }

  if (dryRun) {
    console.log(`    [DRY RUN] Would add "${correctLabel.name}".`);
    if (staleLabels.length > 0) {
      console.log(`    [DRY RUN] Would remove: ${staleLabels.join(', ')}.`);
    }
    return true;
  }

  // Step 1: ADD the correct label FIRST (crash-safe: PR always has at least one label)
  await github.rest.issues.addLabels({
    owner,
    repo,
    issue_number: prNumber,
    labels: [correctLabel.name],
  });
  console.log(`    + Added "${correctLabel.name}".`);

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

module.exports = { ensureLabel, determineLabel, syncLabel };
