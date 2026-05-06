// .github/scripts/review-sync/labels.js
//
// Core label determination and application for the Review Queue Sync.
//
// Logic (Phase 1 — simplified, no difficulty routing):
//   1. Fetch all reviews on a PR (paginated, sorted by submitted_at)
//   2. Build username → latest review state map
//   3. Ignore COMMENTED; DISMISSED actively deletes prior state (prevents ghost approvals)
//   4. For each APPROVED reviewer, check permission level
//   5. Determine correct queue label based on approval counts
//   6. Apply label: add new FIRST, then remove stale (non-negotiable order)
//
// Phase 2 will add difficulty-based routing on top of this logic.

/**
 * The three mutually exclusive queue labels managed by this bot.
 * Colours and names match the Phase 1 specification.
 */
const QUEUE_LABELS = {
  JUNIOR: {
    name: 'queue:junior-committer',
    color: 'e4e669',
    description: 'PR awaiting initial quality review',
  },
  COMMITTERS: {
    name: 'queue:committers',
    color: '0075ca',
    description: 'PR awaiting committer technical review',
  },
  MERGE: {
    name: 'ready-to-merge',
    color: '0e8a16',
    description: 'PR has 2+ write approvals and is ready to merge',
  },
};

/** All queue label names, used for cleanup operations. */
const ALL_QUEUE_LABEL_NAMES = Object.values(QUEUE_LABELS).map((l) => l.name);

/**
 * Fetch all reviews on a PR, returning only the latest state per reviewer.
 * COMMENTED reviews are ignored. DISMISSED reviews actively delete prior state
 * to prevent ghost approvals (e.g. when GitHub auto-dismisses stale reviews
 * after new commits are pushed).
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {number} prNumber - Pull request number
 * @returns {Map<string, string>} username → latest review state (APPROVED | CHANGES_REQUESTED)
 */
async function getLatestReviewStates(github, owner, repo, prNumber) {
  const reviews = await github.paginate(github.rest.pulls.listReviews, {
    owner,
    repo,
    pull_number: prNumber,
    per_page: 100,
  });

  // Sort explicitly by submitted_at to guarantee chronological order.
  // The GitHub API returns reviews chronologically in practice, but
  // explicit sorting makes this correct by construction.
  const sortedReviews = [...reviews].sort(
    (a, b) => new Date(a.submitted_at) - new Date(b.submitted_at)
  );

  // Build a map keyed by reviewer login.
  // Later entries overwrite earlier ones — giving us the latest state per user.
  const latestByUser = new Map();

  for (const review of sortedReviews) {
    const login = review.user?.login;
    const state = review.state?.toUpperCase();

    if (!login || !state) continue;

    if (state === 'APPROVED' || state === 'CHANGES_REQUESTED') {
      latestByUser.set(login, state);
    } else if (state === 'DISMISSED') {
      // CRITICAL: A dismissed review wipes out the user's prior approval.
      // Without this, a stale review that GitHub auto-dismissed (e.g. after
      // new commits) would persist as a ghost approval in the map.
      latestByUser.delete(login);
    }
    // COMMENTED is the only state intentionally ignored
  }

  return latestByUser;
}

/**
 * Check the repository permission level for a given user.
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {string} username - GitHub username
 * @returns {string} 'admin' | 'write' | 'read' | 'none'
 */
async function getPermissionLevel(github, owner, repo, username) {
  try {
    const { data } = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });
    return data.permission || 'none';
  } catch (error) {
    if (error.status === 404) {
      // External contributor — not a collaborator
      return 'none';
    }
    // Log unexpected errors but don't crash the run
    const message = error instanceof Error ? error.message : String(error);
    console.log(`    ⚠ Permission check failed for ${username}: ${message}. Treating as "none".`);
    return 'none';
  }
}

/**
 * Count approvals on a PR, split by permission level.
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {number} prNumber - Pull request number
 * @returns {{ writeApproval: number, softApproval: number, anyApproval: number }}
 */
async function countApprovals(github, owner, repo, prNumber) {
  const latestStates = await getLatestReviewStates(github, owner, repo, prNumber);

  let writeApproval = 0;
  let softApproval = 0;

  for (const [username, state] of latestStates) {
    if (state !== 'APPROVED') continue;

    const permission = await getPermissionLevel(github, owner, repo, username);

    if (permission === 'admin' || permission === 'write') {
      writeApproval++;
    } else {
      // read, none, or any unexpected value → soft approval
      softApproval++;
    }
  }

  return {
    writeApproval,
    softApproval,
    anyApproval: writeApproval + softApproval,
  };
}

/**
 * Determine the correct queue label for a PR based on approval counts.
 *
 * Phase 1 logic (no difficulty routing):
 *   writeApproval >= 2  → ready-to-merge
 *   anyApproval  >= 1   → queue:committers
 *   else                → queue:junior-committer
 *
 * @param {{ writeApproval: number, anyApproval: number }} approvals
 * @returns {object} The correct QUEUE_LABELS entry
 */
function determineLabel(approvals) {
  if (approvals.writeApproval >= 2) {
    return QUEUE_LABELS.MERGE;
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
 *   1. Check if the correct label is already present → skip if yes
 *   2. ADD the correct label first
 *   3. THEN remove any stale queue labels
 *
 * This ensures a PR never has zero queue labels, even if the process
 * crashes mid-run.
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
    `  PR #${prNumber}: writeApproval=${approvals.writeApproval}, ` +
    `softApproval=${approvals.softApproval}, anyApproval=${approvals.anyApproval} ` +
    `→ ${correctLabel.name}`
  );

  // Check if the correct label is already present
  if (currentLabels.includes(correctLabel.name)) {
    console.log(`    ✓ Already has "${correctLabel.name}". No change needed.`);
    return false;
  }

  // Determine which stale queue labels to remove
  const staleLabels = currentLabels.filter(
    (name) => ALL_QUEUE_LABEL_NAMES.includes(name) && name !== correctLabel.name
  );

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
      }
    }
  }

  return true;
}

module.exports = {
  QUEUE_LABELS,
  ALL_QUEUE_LABEL_NAMES,
  syncLabel,
};
