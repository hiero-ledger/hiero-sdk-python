// SPDX-License-Identifier: Apache-2.0
//
// helpers/reviews.js
//
// Fetches and processes PR review states.
//
// Key design decisions:
//   - COMMENTED reviews are intentionally ignored (they carry no approval weight)
//   - DISMISSED reviews actively delete prior state to prevent ghost approvals
//   - Explicit chronological sort guarantees correctness regardless of API order

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

module.exports = { getLatestReviewStates };
